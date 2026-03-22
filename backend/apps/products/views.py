from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Coupon

from .models import Cart, CartItem, Category, Product
from .permissions import IsOwnerOrAdmin, IsSellerOrAdmin
from .serializers import (
    AddCartItemSerializer,
    ApplyCouponSerializer,
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    ProductSerializer,
)


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related("category", "seller").filter(is_active=True)
    serializer_class = ProductSerializer
    search_fields = ("title", "description")
    filterset_fields = ("category",)
    ordering_fields = ("price", "created_at", "title")

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSellerOrAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("category", "seller")
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.AllowAny()]


class MyProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def retrieve(self, request, *args, **kwargs):
        category = self.get_object()
        category_data = self.get_serializer(category).data
        products_data = ProductSerializer(Product.objects.filter(category=category, is_active=True), many=True).data
        return Response({"category": category_data, "products": products_data})


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)


class AddCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product = get_object_or_404(Product, id=serializer.validated_data["product_id"], is_active=True)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": serializer.validated_data["quantity"]}
        )
        if not created:
            cart_item.quantity += serializer.validated_data["quantity"]
            cart_item.save(update_fields=["quantity"])
        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        cart = get_object_or_404(Cart, user=request.user)
        item = get_object_or_404(CartItem, id=pk, cart=cart)
        quantity = int(request.data.get("quantity", 1))
        if quantity < 1:
            return Response({"detail": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)
        item.quantity = quantity
        item.save(update_fields=["quantity"])
        return Response(CartItemSerializer(item).data)

    def delete(self, request, pk):
        cart = get_object_or_404(Cart, user=request.user)
        item = get_object_or_404(CartItem, id=pk, cart=cart)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClearCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        cart.applied_coupon = None
        cart.save(update_fields=["applied_coupon"])
        return Response({"detail": "Cart cleared."}, status=status.HTTP_200_OK)


class ApplyCouponView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        coupon = Coupon.objects.get(code=serializer.validated_data["code"])
        cart.applied_coupon = coupon
        cart.save(update_fields=["applied_coupon"])
        return Response({"detail": "Coupon applied.", "coupon": coupon.code}, status=status.HTTP_200_OK)
