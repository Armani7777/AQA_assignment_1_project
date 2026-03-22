from decimal import Decimal

from django.db.models import Avg
from rest_framework import serializers

from apps.orders.models import Coupon

from .models import Cart, CartItem, Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("seller",)

    def get_average_rating(self, obj):
        data = obj.reviews.aggregate(avg=Avg("rating"))
        return round(data["avg"], 2) if data["avg"] else 0

    def get_reviews_count(self, obj):
        return obj.reviews.count()


class CartItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)
    image_url = serializers.CharField(source="product.image_url", read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "product_title", "product_price", "image_url", "quantity")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    coupon_code = serializers.CharField(source="applied_coupon.code", read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "user", "coupon_code", "items", "subtotal", "discount", "total")

    def get_subtotal(self, obj):
        total = Decimal("0")
        for item in obj.items.select_related("product"):
            total += item.product.price * item.quantity
        return total

    def get_discount(self, obj):
        subtotal = self.get_subtotal(obj)
        if obj.applied_coupon and obj.applied_coupon.is_valid():
            return (subtotal * Decimal(obj.applied_coupon.discount_percent) / Decimal("100")).quantize(Decimal("0.01"))
        return Decimal("0.00")

    def get_total(self, obj):
        return (self.get_subtotal(obj) - self.get_discount(obj)).quantize(Decimal("0.01"))


class AddCartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)

    def validate_code(self, value):
        try:
            coupon = Coupon.objects.get(code=value)
        except Coupon.DoesNotExist as exc:
            raise serializers.ValidationError("Coupon does not exist.") from exc
        if not coupon.is_valid():
            raise serializers.ValidationError("Coupon is not valid.")
        return value
