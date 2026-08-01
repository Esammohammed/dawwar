import hashlib
import secrets
import threading
from datetime import timedelta

from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPCode
from .serializers import (
    RegisterRequestSerializer,
    RegisterVerifySerializer,
    LoginSerializer,
    OTPLoginRequestSerializer,
    OTPLoginVerifySerializer,
    PasswordResetConfirmSerializer,
    PasswordChangeSerializer,
    UserSerializer,
)
from .tasks import send_otp_email_task

User = get_user_model()

OTP_EXPIRY_MINUTES = 5
OTP_MAX_PER_HOUR = 5


def _hash_code(code):
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def _error(message, code, http_status):
    return Response({'error': message, 'code': code}, status=http_status)


def _issue_otp(email, purpose, phone=None):
    """Create and send an email OTP. Returns an error Response or None on success."""
    recent_count = OTPCode.objects.filter(
        email=email,
        created_at__gt=timezone.now() - timedelta(hours=1)
    ).count()
    if recent_count >= OTP_MAX_PER_HOUR:
        return _error(
            'Too many OTP requests for this email. Please try again later.',
            'too_many_requests',
            status.HTTP_429_TOO_MANY_REQUESTS
        )

    raw_code = f"{secrets.randbelow(900000) + 100000:06d}"
    OTPCode.objects.create(
        email=email,
        phone=phone,
        delivery_method=OTPCode.DeliveryMethod.EMAIL,
        code_hash=_hash_code(raw_code),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    )

    # Dispatch email in a background thread so the HTTP response is not blocked.
    threading.Thread(
        target=send_otp_email_task,
        args=(email, raw_code),
        daemon=True
    ).start()
    return None


def _check_otp(email, code, purpose):
    """Verify and consume an OTP. Returns an error Response or None on success."""
    otp = OTPCode.objects.filter(
        email=email,
        purpose=purpose,
        consumed_at__isnull=True,
        expires_at__gt=timezone.now()
    ).order_by('-created_at').first()

    if not otp:
        return _error('Invalid or expired OTP code', 'invalid_code', status.HTTP_400_BAD_REQUEST)

    if otp.attempts >= OTPCode.MAX_ATTEMPTS:
        return _error('Too many failed attempts. Request a new code.', 'invalid_code', status.HTTP_400_BAD_REQUEST)

    if otp.code_hash != _hash_code(code):
        otp.attempts += 1
        otp.save(update_fields=['attempts'])
        return _error('Invalid or expired OTP code', 'invalid_code', status.HTTP_400_BAD_REQUEST)

    otp.consumed_at = timezone.now()
    otp.save(update_fields=['consumed_at'])
    return None


def _auth_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    }


class RegisterRequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        email = serializer.validated_data['email']

        if User.objects.filter(phone=phone).exists():
            return _error('An account with this phone number already exists.', 'phone_exists', status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email__iexact=email).exists():
            return _error('An account with this email already exists.', 'email_exists', status.HTTP_400_BAD_REQUEST)

        error = _issue_otp(email, OTPCode.Purpose.REGISTER, phone=phone)
        if error:
            return error
        return Response({'message': 'OTP sent to email successfully', 'email': email}, status=status.HTTP_200_OK)


class RegisterVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        error = _check_otp(data['email'], data['code'], OTPCode.Purpose.REGISTER)
        if error:
            return error

        if User.objects.filter(phone=data['phone']).exists():
            return _error('An account with this phone number already exists.', 'phone_exists', status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email__iexact=data['email']).exists():
            return _error('An account with this email already exists.', 'email_exists', status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(
                phone=data['phone'],
                full_name=data['full_name'],
                password=data['password'],
                email=data['email'],
                is_phone_verified=True,
            )
        except IntegrityError:
            return _error('An account with these details already exists.', 'phone_exists', status.HTTP_400_BAD_REQUEST)

        return Response(_auth_payload(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier'].strip()
        password = serializer.validated_data['password']

        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(phone=identifier).first()

        if not user or not user.is_active:
            return _error('Invalid credentials.', 'invalid_credentials', status.HTTP_401_UNAUTHORIZED)

        if not (user.password and user.has_usable_password()):
            return _error(
                'This account has no password yet. Login with a verification code instead.',
                'password_not_set',
                status.HTTP_403_FORBIDDEN
            )

        if not user.check_password(password):
            return _error('Invalid credentials.', 'invalid_credentials', status.HTTP_401_UNAUTHORIZED)

        return Response(_auth_payload(user), status=status.HTTP_200_OK)


class OTPLoginRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Reveals account existence; accepted tradeoff so users get a clear
        # "no account with this email" message instead of a dead-end code screen.
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            return _error('No account found with this email.', 'email_not_found', status.HTTP_400_BAD_REQUEST)

        error = _issue_otp(email, OTPCode.Purpose.LOGIN)
        if error:
            return error
        return Response({'message': 'OTP sent to email successfully', 'email': email}, status=status.HTTP_200_OK)


class OTPLoginVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPLoginVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        error = _check_otp(email, serializer.validated_data['code'], OTPCode.Purpose.LOGIN)
        if error:
            return error

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return _error('No account found with this email.', 'email_not_found', status.HTTP_400_BAD_REQUEST)

        return Response(_auth_payload(user), status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            return _error('No account found with this email.', 'email_not_found', status.HTTP_400_BAD_REQUEST)

        error = _issue_otp(email, OTPCode.Purpose.RESET)
        if error:
            return error
        return Response({'message': 'OTP sent to email successfully', 'email': email}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        error = _check_otp(email, serializer.validated_data['code'], OTPCode.Purpose.RESET)
        if error:
            return error

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return _error('No account found with this email.', 'email_not_found', status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        return Response(_auth_payload(user), status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        has_password = bool(user.password) and user.has_usable_password()
        if has_password:
            current = serializer.validated_data.get('current_password', '')
            if not current or not user.check_password(current):
                return _error('Current password is incorrect.', 'wrong_password', status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
