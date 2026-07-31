from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'email', 'full_name', 'role', 'is_phone_verified', 'telegram_id', 'created_at']
        read_only_fields = ['id', 'role', 'is_phone_verified', 'created_at']
