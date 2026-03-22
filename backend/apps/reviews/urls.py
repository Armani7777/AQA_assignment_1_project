from django.urls import path

from .views import ReviewDeleteView, ReviewListCreateView

urlpatterns = [
    path("", ReviewListCreateView.as_view()),
    path("<int:pk>/", ReviewDeleteView.as_view()),
]
