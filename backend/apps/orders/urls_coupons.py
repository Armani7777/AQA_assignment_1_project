from django.urls import path

from .views import CouponListCreateView, CouponValidateView

urlpatterns = [
    path("", CouponListCreateView.as_view()),
    path("validate/", CouponValidateView.as_view()),
]
