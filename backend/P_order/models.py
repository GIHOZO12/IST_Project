from django.db import models

from accounts.models import CustomUser

# Create your models here.


 



class  PurchaseRequest(models.Model):
    STATUS_CHOICES=(
        ('pending', 'pending'),
        ('approved', 'approved'),
        ('rejected', 'rejected'),
    )

    status=models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    title=models.CharField(max_length=100)
    description=models.TextField()
    amount= models.DecimalField(max_digits=10, decimal_places=2)
    created_by= models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_requests")
    approved_by= models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_requests")
    proforma= models.FileField(upload_to='proformas/', null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    purchase_order=models.OneToOneField('PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True) 

    def __str__(self):
        return f"{self.title} - {self.status}"




class RequestItem(models.Model):
    purchase_request=models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=512)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)



class Approval(models.Model):
    LEVEL_CHOICES=[(1, 'Level 1'), (2, 'Level 2'),(3, 'finance')]
    purchase_request= models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name="approvals")
    approver=models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="approver_made")
    level=models.IntegerField(choices=LEVEL_CHOICES)
    approved=models.BooleanField()
    comments=models.TextField(null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('purchase_request', 'level')
    

class PurchaseOrder(models.Model):
    purchase_request=models.OneToOneField(PurchaseRequest, on_delete=models.CASCADE, related_name="Generated_PO")
    po_number=models.CharField(max_length=100, unique=True)
    vendor=models.CharField(max_length=100)
    item_snapshot=models.JSONField(default=list)
    total_amount=models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    po_file = models.FileField(upload_to='pos/', null=True, blank=True)



class Receipt(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, related_name='receipts', on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    receipt_file = models.FileField(upload_to='receipts/')
    extracted_data = models.JSONField(null=True, blank=True)
    validated = models.BooleanField(default=False)
    discrepancies = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    