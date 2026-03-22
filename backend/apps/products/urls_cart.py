from django.urls import path

from .views import (
    AddCartItemView,
    ApplyCouponView,
    CartItemDetailView,
    CartView,
    ClearCartView,
)

urlpatterns = [
    path("", CartView.as_view()),
    path("items/", AddCartItemView.as_view()),
    path("items/<int:pk>/", CartItemDetailView.as_view()),
    path("clear/", ClearCartView.as_view()),
    path("apply-coupon/", ApplyCouponView.as_view()),
]
