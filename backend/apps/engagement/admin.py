from django.contrib import admin
from .models import Inquiry, Booking

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'phone', 'status', 'assigned_to', 'created_at')
    list_filter = ('status',)
    search_fields = ('phone', 'message')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'user', 'deposit_amount', 'status', 'expires_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__phone', 'user__full_name')
