import logging
from decimal import Decimal

from django.db import OperationalError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Cart, Product

from .models import Coupon, Order, OrderItem
from .serializers import (
    CouponSerializer,
    CreateOrderSerializer,
    OrderSerializer,
    OrderStatusSerializer,
    ValidateCouponSerializer,
    calculate_discount,
)

logger = logging.getLogger(__name__)


class CouponListCreateView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]


class CouponValidateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ValidateCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coupon = Coupon.objects.filter(code=serializer.validated_data["code"]).first()
        if not coupon or not coupon.is_valid():
            return Response({"valid": False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"valid": True, "discount_percent": coupon.discount_percent}, status=status.HTTP_200_OK)


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ("created_at", "total_price")

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product")

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = get_object_or_404(Cart.objects.prefetch_related("items__product"), user=request.user)
        if not cart.items.exists():
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return self._create_order(request, serializer, cart)
        except OperationalError:
            logger.warning("Database lock during order creation for user %s", request.user.id)
            return Response(
                {"detail": "Server is busy, please try again."},
                status=status.HTTP_409_CONFLICT,
            )

    @transaction.atomic
    def _create_order(self, request, serializer, cart):
        product_ids = [item.product_id for item in cart.items.all()]
        locked_products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}
        subtotal = Decimal("0.00")
        for item in cart.items.all():
            product = locked_products[item.product_id]
            if item.quantity > product.stock:
                return Response(
                    {"detail": f"Not enough stock for {product.title}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subtotal += product.price * item.quantity
        discount = calculate_discount(subtotal, cart.applied_coupon)
        order = Order.objects.create(
            user=request.user,
            shipping_address=serializer.validated_data["shipping_address"],
            coupon=cart.applied_coupon,
            discount_amount=discount,
            total_price=(subtotal - discount).quantize(Decimal("0.01")),
        )
        for item in cart.items.all():
            product = locked_products[item.product_id]
            OrderItem.objects.create(order=order, product=product, quantity=item.quantity, price=product.price)
            product.stock -= item.quantity
            product.save(update_fields=["stock"])
        cart.items.all().delete()
        cart.applied_coupon = None
        cart.save(update_fields=["applied_coupon"])
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product")


class CancelOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        order = get_object_or_404(Order, id=pk, user=request.user)
        if order.status != "pending":
            return Response({"detail": "Only pending orders can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        for item in order.items.select_related("product"):
            item.product.stock += item.quantity
            item.product.save(update_fields=["stock"])
        order.status = "cancelled"
        order.save(update_fields=["status"])
        return Response({"detail": "Order cancelled."}, status=status.HTTP_200_OK)


class UpdateOrderStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order.status = serializer.validated_data["status"]
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
