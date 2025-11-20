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
    permission_classes=[IsAuthenticated,Is_Staff]
    def get(self, request):
        purchase=PurchaseRequest.objects.all()
        serializers=PurchaseRequestSerialzer(purchase, many=True)
        return Response(serializers.data, status=status.HTTP_200_OK)
    


class PurchaseRequestByIdView(APIView):
    permission_classes=[IsAuthenticated,Is_Staff]
    def get(self, request, id):
        try:
            purchase=PurchaseRequest.objects.get(id=id)
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
    




class ApproveRequestView(APIView):
    permission_classes=[IsAuthenticated, IsApprover]

    def patch(self, request, id):
        try:
            purchase=PurchaseRequest.objects.select_for_update().get(id=id)
        except PurchaseRequest.DoesNotExist:
            return Response({"error":"Purchase Request not found."}, status=status.HTTP_404_NOT_FOUND)
       
        if purchase.status !='pending':
            return Response({"error":"Purchase Request is still pending."}, status=status.HTTP_400_BAD_REQUEST)
        


        role = request.user.role
        if role == "approver_level_1":
            level = 1
        elif role == "approver_level_2":
            level = 2
        elif role == "finance":
            level = 3
        else:
            return Response({"error": "Unauthorized role"}, status=403)

        serializer=ApprovalSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        Approval.objects.create(
            purchase_request=purchase,
            approver=request.user,
            level=level,
            approved=True,
            comments=serializer.validated_data.get('comments','')


        )
        required_level=[1,2]
        approved_levels=list(purchase.approvals.filter(approved=True))
        if all(level in approved_levels for level in required_level):
            purchase.status='approved'
            purchase.approved_by=request.user
            purchase.save()


            po_number=f"Po {purchase.id} -{purchase.created_at.strftime('%Y%m%d')}"
            items_snapshot=[
                {"description":item.desscription, "quantity":item.quantity, "unit_price":item.unit_price}
                for item in purchase.items.all()
            ]
            totol_amount=sum(i['quantity'] * i['unit_price'] for i in items_snapshot)

            PurchaseOrder.objects.create(
                purchase_request=purchase,
                po_number=po_number,
                vendor="Vendor name",
                item_snapshot=items_snapshot,
                total_amount=totol_amount
            )
            return Response({"message":"Purchase Request approved and Purchase Order generated."}, status=status.HTTP_200_OK)
        return Response({"message":"Request approved at this level."}, status=status.HTTP_200_OK)