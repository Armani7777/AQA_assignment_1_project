from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password", "full_name", "is_seller")

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid credentials.") from exc
        auth_user = authenticate(username=user.username, password=password)
        if not auth_user:
            raise serializers.ValidationError("Invalid credentials.")
        refresh = RefreshToken.for_user(auth_user)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "full_name", "phone", "is_seller", "is_staff")


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "full_name", "phone", "is_seller")
        read_only_fields = ("username", "email", "is_seller")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value
