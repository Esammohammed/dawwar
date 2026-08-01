from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterRequestOTPView,
    RegisterVerifyView,
    LoginView,
    OTPLoginRequestView,
    OTPLoginVerifyView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView,
)

urlpatterns = [
    path('register/request-otp/', RegisterRequestOTPView.as_view(), name='register-request-otp'),
    path('register/verify/', RegisterVerifyView.as_view(), name='register-verify'),
    path('login/', LoginView.as_view(), name='login'),
    path('login/otp/request/', OTPLoginRequestView.as_view(), name='login-otp-request'),
    path('login/otp/verify/', OTPLoginVerifyView.as_view(), name='login-otp-verify'),
    path('password/reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
