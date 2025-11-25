from rest_framework.response import Response
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import FileResponse, Http404
from django.conf import settings
import os
    
import json
from rest_framework import status

from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

from  accounts.permissions import *
from .serializer import *
from .models import *
from .document_processor import extract_proforma_data, extract_receipt_data, validate_receipt_against_po

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
      
        proforma_file = request.FILES.get('proforma')
        proforma_data = None
        

        data = {}
        
   
        for key in request.data.keys():
            value = request.data.get(key)
           
            if key == 'items' and isinstance(value, str):
                try:
                    data[key] = json.loads(value)
                except json.JSONDecodeError:
                    return Response(
                        {"items": ["Invalid JSON format for items"]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif key != 'items':  
                data[key] = value
        
  
        if 'items' not in data:
         
            items_value = request.data.get('items')
            if items_value and isinstance(items_value, str):
                try:
                    data['items'] = json.loads(items_value)
                except json.JSONDecodeError:
                    pass
        
        if proforma_file:
          
            proforma_data = extract_proforma_data(proforma_file)
            
          
            if proforma_data.get('items') and not data.get('items'):
                data['items'] = proforma_data['items']
            
         
            data['proforma'] = proforma_file
        
        serializer = PurchaseRequestSerialzer(data=data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class UpdatePurchaseRequestView(APIView):
    permission_classes=[IsAuthenticated,Is_Staff]


    def put(self, request, id):
        try:
            purchase=PurchaseRequest.objects.get(id=id, created_by=request.user)
        except PurchaseRequest.DoesNotExist:
            return Response({"error":"Purchase Request not found."}, status=status.HTTP_404_NOT_FOUND)

        if purchase.status !='pending':
            return Response({"error":f"you can not update request because it is already {purchase.status}."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle FormData: parse items JSON string if present
    
        data = {}
        for key in request.data.keys():
            value = request.data.get(key)
            if key == 'items' and isinstance(value, str):
                try:
                    data[key] = json.loads(value)
                except json.JSONDecodeError:
                    return Response(
                        {"items": ["Invalid JSON format for items"]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                data[key] = value
        
        serializer=PurchaseRequestSerialzer(purchase, data=data, context={"request": request})  
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
             




def send_staff_notification(subject, message, staff_email, attachment=None, filename=None):
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[staff_email],
    )
    if attachment and filename:
        email.attach(filename, attachment, 'application/pdf')
    email.send()

class ApproveRequestView(APIView):
    permission_classes = [IsAuthenticated, IsApprover]

    def patch(self, request, id):
        try:
            purchase = PurchaseRequest.objects.get(id=id)
        except PurchaseRequest.DoesNotExist:
            return Response({"error": "Purchase Request not found"}, status=404)

        if purchase.status != "pending":
            return Response({"error": f"Request is already {purchase.status}"}, status=400)

        role = request.user.role
        if role == "manager_1":
            level = 1
        elif role == "manager_2":
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
            send_staff_notification(
                subject="Purchase Requested for Approval",
                    message=f"Your Purchase Request '{purchase.title}' has been approved at {role}.",
                    staff_email=purchase.created_by.email
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

        # Extract vendor from proforma if available
        vendor_name = "Vendor Name"
        if purchase.proforma:
            try:
                purchase.proforma.seek(0)
                proforma_data = extract_proforma_data(purchase.proforma)
                if proforma_data.get('vendor'):
                    vendor_name = proforma_data['vendor']
            except Exception:
                pass

        # Create the PurchaseOrder and link it back to the PurchaseRequest so
        # the frontend can see that a PO has been generated.
        po = PurchaseOrder.objects.create(
            purchase_request=purchase,
            po_number=po_number,
            vendor=vendor_name,
            item_snapshot=items_snapshot,
            total_amount=total_amount,
        )

        # Generate a professional PDF Purchase Order document
        # This uses the reportlab library for PDF generation
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
    
        dark_blue_r, dark_blue_g, dark_blue_b = 0.1, 0.2, 0.4
        light_gray_r, light_gray_g, light_gray_b = 0.9, 0.9, 0.9
        

        c.setFillColorRGB(dark_blue_r, dark_blue_g, dark_blue_b)
        c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height - 45, "IST AFRICA")
        
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 70, "PURCHASE ORDER")
    
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - 50, height - 45, f"PO #: {po.po_number}")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 50, height - 65, f"Date: {purchase.created_at.strftime('%B %d, %Y')}")
        c.drawRightString(width - 50, height - 80, f"Request ID: PR-{purchase.id}")
        
        y_position = height - 130
    
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y_position, "FROM:")
        c.setFont("Helvetica", 10)
        c.drawString(50, y_position - 15, "IST Africa")
        c.drawString(50, y_position - 30, "Procurement Department")
        c.drawString(50, y_position - 45, "Email: procurement@ist.africa")
        
        # Right Column - Vendor Info
        c.setFont("Helvetica-Bold", 11)
        c.drawString(300, y_position, "TO:")
        c.setFont("Helvetica", 10)
        vendor_lines = vendor_name.split('\n') if '\n' in vendor_name else [vendor_name]
        for i, line in enumerate(vendor_lines[:4]):  # Limit to 4 lines
            c.drawString(300, y_position - 15 - (i * 15), line[:50])
        
        y_position -= 80
        
        # ===== REQUEST DETAILS SECTION =====
        c.setFillColorRGB(light_gray_r, light_gray_g, light_gray_b)
        c.rect(50, y_position - 20, width - 100, 50, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(60, y_position, "PURCHASE REQUEST DETAILS")
        c.setFont("Helvetica", 9)
        c.drawString(60, y_position - 15, f"Title: {purchase.title}")
    
        desc_lines = []
        desc = purchase.description
        while len(desc) > 80:
            desc_lines.append(desc[:80])
            desc = desc[80:]
        if desc:
            desc_lines.append(desc)
        for i, line in enumerate(desc_lines[:2]): 
            c.drawString(60, y_position - 30 - (i * 12), line)
        
        y_position -= 90
        
        

        c.setFillColorRGB(dark_blue_r, dark_blue_g, dark_blue_b)
        c.rect(50, y_position - 20, width - 100, 25, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60, y_position - 5, "ITEM DESCRIPTION")
        c.drawString(350, y_position - 5, "QTY")
        c.drawString(400, y_position - 5, "UNIT PRICE")
        c.drawString(480, y_position - 5, "TOTAL")
        
        y_position -= 35
        
    
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        row_height = 20
        for idx, item in enumerate(items_snapshot):
            
            if idx % 2 == 0:
                c.setFillColorRGB(light_gray_r, light_gray_g, light_gray_b)
                c.rect(50, y_position - row_height, width - 100, row_height, fill=1, stroke=0)
                c.setFillColorRGB(0, 0, 0)
            
            item_total = item['quantity'] * item['unit_price']
            
            
            desc = item['description']
            if len(desc) > 45:
                desc = desc[:42] + "..."
            c.drawString(60, y_position - 5, desc)
            
    
            c.drawString(350, y_position - 5, str(item['quantity']))
            
            c.drawString(400, y_position - 5, f"${item['unit_price']:,.2f}")
            
    
            c.drawString(480, y_position - 5, f"${item_total:,.2f}")
            
            y_position -= row_height
            

            if y_position < 200:
                c.showPage()
                y_position = height - 50
        
        
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.line(50, y_position, width - 50, y_position)
        y_position -= 10
        
    
        c.setFont("Helvetica", 9)
        c.drawString(400, y_position, "Subtotal:")
        c.drawString(480, y_position, f"${total_amount:,.2f}")
        y_position -= 15
        
        c.drawString(400, y_position, "Tax (0%):")
        c.drawString(480, y_position, "$0.00")
        y_position -= 20
        
        # Grand Total
        c.setFillColorRGB(dark_blue_r, dark_blue_g, dark_blue_b)
        c.rect(380, y_position - 20, width - 430, 25, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(400, y_position - 5, "TOTAL AMOUNT:")
        c.drawString(480, y_position - 5, f"${total_amount:,.2f}")
        
        y_position -= 50
        
        # ===== TERMS & CONDITIONS =====
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y_position, "TERMS AND CONDITIONS:")
        y_position -= 15
        c.setFont("Helvetica", 8)
        terms = [
            "1. Delivery must be made within 30 days of PO approval.",
            "2. All items must meet specified quality standards.",
            "3. Payment terms: Net 30 days from invoice date.",
            "4. This PO is subject to company approval and budget availability.",
        ]
        for term in terms:
            c.drawString(60, y_position, term)
            y_position -= 12
        
        y_position -= 20
        
        # ===== APPROVAL SECTION =====
        # Approval signature line
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_position, "APPROVED BY:")
        y_position -= 20
        c.setFont("Helvetica", 9)
        c.drawString(50, y_position, f"{approver.get_full_name() if hasattr(approver, 'get_full_name') and approver.get_full_name() else approver.username}")
        c.drawString(50, y_position - 12, f"Finance Department")
        c.drawString(50, y_position - 24, f"Date: {purchase.updated_at.strftime('%B %d, %Y')}")
        
        # Signature line
        c.setLineWidth(0.5)
        c.line(50, y_position - 35, 200, y_position - 35)
        c.setFont("Helvetica", 7)
        c.drawString(50, y_position - 42, "Authorized Signature")
        
        # Footer
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        # ReportLab uses British spelling: drawCentredString
        c.drawCentredString(width / 2, 30, "This is a computer-generated document. No signature required.")
        c.drawCentredString(width / 2, 20, f"Generated on {purchase.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

        
        c.showPage()
        c.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()

        po_filename = f"{po_number}.pdf"
        po.po_file.save(po_filename, ContentFile(pdf_bytes), save=True)
        send_staff_notification(
                subject="Purchase Request Fully Approved",
    message=(
        f"Hello {purchase.created_by.username},\n\n"
        f"Your purchase request '{purchase.title}' has been fully approved.\n"
        f"Purchase Order Number: {po.po_number}\n\n"
        f"The PDF Purchase Order is attached."
    ),
    staff_email=purchase.created_by.email,
    attachment=pdf_bytes,
    filename=f"{po.po_number}.pdf"
        ) 
        purchase.purchase_order = po
        purchase.save(update_fields=["purchase_order"])

        return  Response(
            {"message": "Purchase Order generated successfully."},
            status=status.HTTP_200_OK,
        )


class RejectRequestView(APIView):
    permission_classes=[IsAuthenticated, IsApprover]
    def patch(self, request, id):
        try:
            # Use a normal get() here; select_for_update() requires an explicit
            # transaction and was causing TransactionManagementError.
            purchase=PurchaseRequest.objects.get(id=id)
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
        send_staff_notification(
    subject="Purchase Request Rejected",
    message=(
        f"Hello {purchase.created_by.username},\n\n"
        f"Your purchase request '{purchase.title}' has been rejected.\n"
        f"Reason: {comments}"
    ),
    staff_email=purchase.created_by.email
)
        return Response({"message": "Purchase Request rejected."}, status=status.HTTP_200_OK)


class SubmitReceiptView(APIView):
    permission_classes = [IsAuthenticated, Is_Staff]
    
    def post(self, request, id):
        
        try:
            purchase = PurchaseRequest.objects.get(id=id, created_by=request.user)
        except PurchaseRequest.DoesNotExist:
            return Response(
                {"error": "Purchase Request not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not purchase.purchase_order:
            return Response(
                {"error": "Purchase Order not found. Request must be approved first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        receipt_file = request.FILES.get('receipt_file')
        if not receipt_file:
            return Response(
                {"error": "Receipt file is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        receipt_data = extract_receipt_data(receipt_file)
        
        
        po = purchase.purchase_order
        po_data = {
            "vendor": po.vendor,
            "item_snapshot": po.item_snapshot,
            "total_amount": float(po.total_amount),
        }
        
        # Validate receipt against PO
        validation_result = validate_receipt_against_po(receipt_data, po_data)
        
        # Create receipt record
        receipt = Receipt.objects.create(
            purchase_request=purchase,
            uploaded_by=request.user,
            receipt_file=receipt_file,
            extracted_data=receipt_data,
            validated=validation_result["validated"],
            discrepancies=validation_result["discrepancies"],
        )
        
        serializer = ReceiptSerializer(receipt)
        
        return Response({
            "message": "Receipt submitted successfully.",
            "receipt": serializer.data,
            "validation": {
                "validated": validation_result["validated"],
                "discrepancies": validation_result["discrepancies"],
            }
        }, status=status.HTTP_201_CREATED)


class DownloadFileView(APIView):
    """
    View to download files (proforma, PO PDF, receipts) with proper headers.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, file_type, file_id):
        """
        Download file by type and ID.
        file_type: 'proforma', 'po', or 'receipt'
        file_id: ID of the related object
        """
        try:
            if file_type == 'proforma':
                purchase = PurchaseRequest.objects.get(id=file_id)
                if not purchase.proforma:
                    raise Http404("Proforma not found")
                file_path = purchase.proforma.path
                filename = os.path.basename(purchase.proforma.name)
                
            elif file_type == 'po':
                po = PurchaseOrder.objects.get(id=file_id)
                if not po.po_file:
                    raise Http404("PO file not found")
                file_path = po.po_file.path
                filename = os.path.basename(po.po_file.name)
                
            elif file_type == 'receipt':
                receipt = Receipt.objects.get(id=file_id)
                if not receipt.receipt_file:
                    raise Http404("Receipt file not found")
                file_path = receipt.receipt_file.path
                filename = os.path.basename(receipt.receipt_file.name)
            else:
                raise Http404("Invalid file type")
            
            if not os.path.exists(file_path):
                raise Http404("File not found on server")
            
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/pdf' if filename.lower().endswith('.pdf') else 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except (PurchaseRequest.DoesNotExist, PurchaseOrder.DoesNotExist, Receipt.DoesNotExist):
            raise Http404("File not found")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)