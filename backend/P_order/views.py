from rest_framework.response import Response
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from rest_framework import status

from  accounts.permissions import *
from .serializer import *
from .models import *

# Create your views here.



class PurchaseRequestListView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request):
        role = getattr(request.user, 'role', None)

        if role == 'staff':
        
            purchase = PurchaseRequest.objects.filter(created_by=request.user)
        else:
        
            purchase = PurchaseRequest.objects.all()

        serializers = PurchaseRequestSerialzer(purchase, many=True)
        return Response(serializers.data, status=status.HTTP_200_OK)
    


class PurchaseRequestByIdView(APIView):
    permission_classes=[IsAuthenticated,Is_Staff]
    def get(self, request, id):
        try:
            purchase=PurchaseRequest.objects.get(id=id, created_by=request.user)
        except PurchaseRequest.DoesNotExist:
            return Response({"error":"Purchase Request not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer=PurchaseRequestSerialzer(purchase)
        return Response(serializer.data, status=status.HTTP_200_OK)
            

class PurchaseRequestView(APIView):
    permission_classes=[IsAuthenticated,Is_Staff]

    def post(self, request):
        serializer=PurchaseRequestSerialzer(data=request.data, context={"request": request} )
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UpdatePurchaseRequestView(APIView):
    permission_classes=[IsAuthenticated,Is_Staff]


    def put(self, request, id):
        try:
            
            purchase=PurchaseRequest.objects.get(id=id, created_by=request.user)
        except PurchaseRequest.DoesNotExist:
            return Response({"error":"Purchase Request not found."}, status=status.HTTP_404_NOT_FOUND)

        if purchase.status !='pending':
            return Response({"error":f"you can not update request because it is already {purchase.status}."}, status=status.HTTP_400_BAD_REQUEST)
        serializer=PurchaseRequestSerialzer(purchase, data=request.data, context={"request": request})  
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
             


class ApproveRequestView(APIView):
    permission_classes = [IsAuthenticated, IsApprover]

    def patch(self, request, id):
        try:
            purchase = PurchaseRequest.objects.select_for_update().get(id=id)
        except PurchaseRequest.DoesNotExist:
            return Response({"error": "Purchase Request not found"}, status=404)

        if purchase.status != "pending":
            return Response({"error": f"Request is already {purchase.status}"}, status=400)

        role = request.user.role
        if role == "approver_level_1":
            level = 1
        elif role == "approver_level_2":
            level = 2
        elif role == "finance":
            level = 3
        else:
            return Response({"error": "Unauthorized role"}, status=403)

        comments = request.data.get("comments", "")

        # Only create an Approval row for actual approver levels (1 and 2).
        # The finance step is handled separately and should not use an
        # invalid level value that is not present in LEVEL_CHOICES.
        if level in (1, 2):
            Approval.objects.create(
                purchase_request=purchase,
                approver=request.user,
                level=level,
                approved=True,
                comments=comments,
            )

        # Recompute which levels have already approved (1 and 2).
        approved_levels = list(
            purchase.approvals.filter(approved=True).values_list("level", flat=True)
        )

        # Finance (level 3) may only approve/generate PO after level 1 and 2.
        if level == 3:
            if 1 in approved_levels and 2 in approved_levels:
                return self.generate_po(purchase, request.user)
            return Response(
                {
                    "message": "Finance approval requires both level 1 and level 2 approvals first.",
                },
                status=400,
            )

        return Response({"message": f"Approved at level {level}."}, status=200)


    def generate_po(self, purchase, approver):

        # Mark the request as fully approved by finance.
        purchase.status = "approved"
        purchase.approved_by = approver
        purchase.save()

        po_number = f"PO-{purchase.id}-{purchase.created_at.strftime('%Y%m%d')}"

        # Build a JSON-serializable snapshot of the items.
        items_snapshot = [
            {
                "description": item.description,
                "quantity": int(item.quantity),
                "unit_price": float(item.unit_price),
            }
            for item in purchase.items.all()
        ]

        total_amount = sum(i["quantity"] * i["unit_price"] for i in items_snapshot)

        # Create the PurchaseOrder and link it back to the PurchaseRequest so
        # the frontend can see that a PO has been generated.
        po = PurchaseOrder.objects.create(
            purchase_request=purchase,
            po_number=po_number,
            vendor="Vendor Name",
            item_snapshot=items_snapshot,
            total_amount=total_amount,
        )

        purchase.purchase_order = po
        purchase.save(update_fields=["purchase_order"])

        return Response(
            {"message": "Finance approved. Purchase Order generated successfully."},
            status=200,
        )


class RejectRequestView(APIView):
    permission_classes=[IsAuthenticated, IsApprover]
    def patch(self, request, id):
        try:
            purchase=PurchaseRequest.objects.select_for_update().get(id=id)
        except PurchaseRequest.DoesNotExist:
            return Response({"error":"Purchase Request not found."}, status=status.HTTP_404_NOT_FOUND)
        if purchase.status !='pending':
            return Response({"error":f"Purchase Request is already {purchase.status}."}, status=status.HTTP_400_BAD_REQUEST)
        role = request.user.role
        if role == "approver_level_1":
            level = 1
        elif role == "approver_level_2":
            level = 2
        else:
            return Response({"error": "Unauthorized role"}, status=403)

        comments = request.data.get("comments", "")

        Approval.objects.create(
            purchase_request=purchase,
            approver=request.user,
            level=level,
            approved=False,
            comments=comments,
        )    
        purchase.status = 'rejected'
        purchase.save()
        return Response({"message": "Purchase Request rejected."}, status=status.HTTP_200_OK)