from rest_framework import serializers
from decimal import Decimal

from .models import *


class RequestItemSerialzer(serializers.ModelSerializer):
    class Meta:
        model = RequestItem
        fields = ["id", "description", "quantity", "unit_price"]


class ApprovalSerializer(serializers.ModelSerializer):
    approver = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Approval
        fields = [
            "id",
            "purchase_request",
            "approver",
            "level",
            "approved",
            "comments",
            "created_at",
        ]
        read_only_fields = ["purchase_request", "approver", "created_at"]


class PurchaseRequestSerialzer(serializers.ModelSerializer):
    items = RequestItemSerialzer(many=True)
    created_by = serializers.StringRelatedField(read_only=True)
    # expose all approvals for this request (used by finance UI)
    approvals = ApprovalSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            "id",
            "status",
            "title",
            "description",
            "amount",
            "created_by",
            "approved_by",
            "proforma",
            "created_at",
            "updated_at",
            "items",
            "purchase_order",
            "approvals",
        ]
        read_only_fields = [
            "status",
            "created_by",
            "approved_by",
            "created_at",
            "updated_at",
            "purchase_order",
            "amount",  # auto-calculated from items
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])

        # Calculate total amount from items (quantity * unit_price) and
        # ignore any incoming amount value to keep it consistent.
        total_amount = sum(
            Decimal(item.get("quantity", 0)) * Decimal(item.get("unit_price", 0))
            for item in items_data
        )

        validated_data["amount"] = total_amount

        user = self.context["request"].user
        pr = PurchaseRequest.objects.create(created_by=user, **validated_data)

        for item_data in items_data:
            RequestItem.objects.create(purchase_request=pr, **item_data)
        return pr

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        # If items are provided on update, recompute amount from them.
        if items_data is not None:
            total_amount = sum(
                Decimal(item.get("quantity", 0)) * Decimal(item.get("unit_price", 0))
                for item in items_data
            )
            validated_data["amount"] = total_amount

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                RequestItem.objects.create(purchase_request=instance, **item_data)
        return instance




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
