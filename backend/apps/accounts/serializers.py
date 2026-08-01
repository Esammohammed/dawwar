from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from rest_framework import serializers

User = get_user_model()

phone_validator = RegexValidator(
    regex=r'^01[0125]\d{8}$',
    message='Enter a valid Egyptian mobile number (e.g. 01xxxxxxxxx).'
)


class RegisterRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, validators=[phone_validator])
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()


class RegisterVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, validators=[phone_validator])
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    full_name = serializers.CharField(max_length=150, min_length=2)
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=254)
    password = serializers.CharField(write_only=True)


class OTPLoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()


class OTPLoginVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate_email(self, value):
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower()

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class UserSerializer(serializers.ModelSerializer):
    has_password = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'phone', 'email', 'full_name', 'address', 'governorate', 'city',
            'date_of_birth', 'national_id', 'role', 'is_phone_verified',
            'telegram_id', 'has_password', 'created_at'
        ]
        read_only_fields = ['id', 'phone', 'email', 'role', 'is_phone_verified', 'created_at']

    def get_has_password(self, obj):
        return bool(obj.password) and obj.has_usable_password()

    def validate_national_id(self, value):
        if value == '':
            return value
        if not value.isdigit() or len(value) != 14 or value[0] not in ('2', '3'):
            raise serializers.ValidationError('National ID must be 14 digits starting with 2 or 3.')
        return value

    def validate_date_of_birth(self, value):
        if value and value > date.today():
            raise serializers.ValidationError('Date of birth cannot be in the future.')
        return value
