from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Marketplace", {"fields": ("full_name", "phone", "is_seller", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
