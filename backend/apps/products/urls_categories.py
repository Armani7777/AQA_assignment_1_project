from django.urls import path

from .views import CategoryDetailView, CategoryListCreateView

urlpatterns = [
    path("", CategoryListCreateView.as_view()),
    path("<int:pk>/", CategoryDetailView.as_view()),
]
