from rest_framework import serializers
from decimal import Decimal
import json

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


class PurchaseOrderSerializer(serializers.ModelSerializer):
    po_file = serializers.SerializerMethodField()

    class Meta:
        model=PurchaseOrder
        fields=["id","purchase_request", "po_number", "vendor", "item_snapshot", "total_amount", "created_at", "po_file"]
    
    def get_po_file(self, obj):
        if obj.po_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.po_file.url)
            return obj.po_file.url
        return None


class PurchaseRequestSerialzer(serializers.ModelSerializer):
    items = RequestItemSerialzer(many=True)
    created_by = serializers.StringRelatedField(read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    purchase_order = serializers.SerializerMethodField()
    
    def get_purchase_order(self, obj):
        if obj.purchase_order:
            return PurchaseOrderSerializer(obj.purchase_order, context=self.context).data
        return None
    
    def to_representation(self, instance):
        """Override to return full URL for proforma when reading"""
        representation = super().to_representation(instance)
        if instance.proforma:
            request = self.context.get('request')
            if request:
                representation['proforma'] = request.build_absolute_uri(instance.proforma.url)
            else:
                representation['proforma'] = instance.proforma.url
        return representation

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
            "amount",  
        ]

    def to_internal_value(self, data):
        # Handle FormData: parse JSON string for items if present
        if hasattr(data, 'get'):
            items_value = data.get('items')
            if isinstance(items_value, str):
                try:
                    parsed_items = json.loads(items_value)
                    # Create a mutable copy of the data
                    if hasattr(data, '_mutable'):
                        data._mutable = True
                    data['items'] = parsed_items
                except (json.JSONDecodeError, TypeError):
                    pass  # Let serializer handle the error
        return super().to_internal_value(data)

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        
        # Handle JSON string from FormData
        if isinstance(items_data, str):
            try:
                items_data = json.loads(items_data)
            except json.JSONDecodeError:
                items_data = []

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
        
        # Handle JSON string from FormData
        if isinstance(items_data, str):
            try:
                items_data = json.loads(items_data)
            except json.JSONDecodeError:
                items_data = None

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



class ReceiptSerializer(serializers.ModelSerializer):
    uploaded_by=serializers.StringRelatedField(read_only=True)

    class Meta:
        model=Receipt
        fields=["id","purchase_request", "uploaded_by", "receipt_file", "extracted_data", "validated", "discrepancies", "created_at"]
        read_only_fields=["extracted_data", "validated", "discrepancies", "created_at"]
