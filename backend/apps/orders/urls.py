from django.urls import path

from .views import CancelOrderView, OrderDetailView, OrderListCreateView, UpdateOrderStatusView

urlpatterns = [
    path("", OrderListCreateView.as_view()),
    path("<int:pk>/", OrderDetailView.as_view()),
    path("<int:pk>/cancel/", CancelOrderView.as_view()),
    path("<int:pk>/status/", UpdateOrderStatusView.as_view()),
]
