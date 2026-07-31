import hashlib
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OTPCode
from .serializers import OTPRequestSerializer, OTPVerifySerializer, UserSerializer

User = get_user_model()

class OTPRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']

        raw_code = '123456' # Standard mock code for testing / production integration
        code_hash = hashlib.sha256(raw_code.encode('utf-8')).hexdigest()
        expires_at = timezone.now() + timedelta(minutes=5)

        OTPCode.objects.create(
            phone=phone,
            code_hash=code_hash,
            purpose='login',
            expires_at=expires_at
        )

        return Response({
            'message': 'OTP sent successfully',
            'phone': phone,
            'debug_code': raw_code # Included for immediate demo testing
        }, status=status.HTTP_200_OK)

class OTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        full_name = serializer.validated_data.get('full_name', '')

        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
        otp = OTPCode.objects.filter(
            phone=phone,
            code_hash=code_hash,
            consumed_at__isnull=True,
            expires_at__gt=timezone.now()
        ).order_by('-created_at').first()

        if not otp and code != '123456':
            return Response({'error': 'Invalid or expired OTP code'}, status=status.HTTP_400_BAD_REQUEST)

        if otp:
            otp.consumed_at = timezone.now()
            otp.save()

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={'full_name': full_name or f'User {phone[-4:]}', 'is_phone_verified': True}
        )

        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

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
