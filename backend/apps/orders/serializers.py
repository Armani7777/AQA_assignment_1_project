from decimal import Decimal

from rest_framework import serializers

from .models import Coupon, Order, OrderItem


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class ValidateCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_title", "quantity", "price")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "status",
            "total_price",
            "shipping_address",
            "coupon",
            "discount_amount",
            "items",
            "items_count",
            "created_at",
        )
        read_only_fields = ("user", "status", "total_price", "discount_amount")

    def get_items_count(self, obj):
        return sum(item.quantity for item in obj.items.all())


class CreateOrderSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)


def calculate_discount(subtotal, coupon):
    if coupon and coupon.is_valid():
        return (subtotal * Decimal(coupon.discount_percent) / Decimal("100")).quantize(Decimal("0.01"))
    return Decimal("0.00")
