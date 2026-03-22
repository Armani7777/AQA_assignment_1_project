from django.urls import path

from .views import MyProductsView, ProductDetailView, ProductListCreateView

urlpatterns = [
    path("", ProductListCreateView.as_view()),
    path("my/", MyProductsView.as_view()),
    path("<int:pk>/", ProductDetailView.as_view()),
]
