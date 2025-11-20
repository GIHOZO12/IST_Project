from rest_framework import serializers


from .models import *



class RequestItemSerialzer(serializers.ModelSerializer):
    class Meta:
        model=RequestItem
        fields=["id","description", "quantity", "unit_price"]



class PurchaseRequestSerialzer(serializers.ModelSerializer):
    items=RequestItemSerialzer(many=True)
    created_by=serializers.StringRelatedField(read_only=True)
    class Meta:
        model=PurchaseRequest
        fields=["id","status", "title", "description", "amount", "created_by", "approved_by", "proforma", "created_at", "updated_at", "items","purchase_order"]
        read_only_fields=["status", "created_by", "approved_by", "created_at", "updated_at", "purchase_order"]


    def create(self, validated_data):
        items_data=validated_data.pop("items",[])
        user=self.context["request"].user
        pr=PurchaseRequest.objects.create(created_by=user, **validated_data)


        for item_data in items_data:
            RequestItem.objects.create(purchase_request=pr, **item_data)
        return pr

    def update(self, instance, validated_data):
        items_data=validated_data.pop("items",None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()


        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                RequestItem.objects.create(purchase_request=instance, **item_data)        
        return instance
    



class ApprovalSerializer(serializers.ModelSerializer):
    approver=serializers.StringRelatedField(read_only=True)
    class Meta:
        model=Approval
        fields=["id","purchase_request", "approver", "approved", "comments", "created_at"]
        read_only_fields=["purchase_request","approved", "approver", "created_at"]




class PurchaseOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model=PurchaseOrder
        fields=["id","purchase_request", "po_number", "vendor", "item_snapshot", "total_amount", "created_at", "po_file"]



class ReceiptSerializer(serializers.ModelSerializer):
    uploaded_by=serializers.StringRelatedField(read_only=True)

    class Meta:
        model=Receipt
        fields=["id","purchase_request", "uploaded_by", "receipt_file", "extracted_data", "validated", "discrepancies", "created_at"]
        read_only_fields=["extracted_data", "validated", "discrepancies", "created_at"]
