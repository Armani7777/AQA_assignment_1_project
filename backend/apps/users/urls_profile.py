from django.urls import path

from .views import ChangePasswordView, ProfileView

urlpatterns = [
    path("profile/", ProfileView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
]
