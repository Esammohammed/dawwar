from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPCode

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone', 'full_name', 'role', 'is_phone_verified', 'is_staff', 'created_at')
    list_filter = ('role', 'is_phone_verified', 'is_staff', 'is_active')
    search_fields = ('phone', 'full_name', 'email')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('full_name', 'email', 'telegram_id')}),
        ('Permissions', {'fields': ('role', 'is_phone_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('phone', 'purpose', 'expires_at', 'consumed_at', 'created_at')
    search_fields = ('phone',)
