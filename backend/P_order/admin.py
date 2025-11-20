from django.contrib import admin


from .models import  *



@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
   list_display =["id", "title", "description", "amount", "created_by", "status", "created_at"]
   list_filter = ["status", "created_at", "created_by"]



@admin.register(RequestItem)
class RequestIOtemAdmin(admin.ModelAdmin):
   list_display=["id","description", "quantity", "unit_price","purchase_request"]
   list_filter=["purchase_request"]




@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
   list_display=["id", "purchase_request", "approver", "level", "approved", "created_at"]
   list_filter=["level", "approved", "created_at"]



@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
   list_display=["id", "po_number", "vendor", "total_amount", "created_at"]
   list_filter=["created_at"]


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
   list_display=["id","purchase_request","created_at"]
   list_filter=["created_at"]
