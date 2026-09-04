from django.contrib import admin
from .models import Inquiry, Booking, ExitLead

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

@admin.register(ExitLead)
class ExitLeadAdmin(admin.ModelAdmin):
    list_display = ('phone', 'contract_price', 'amount_paid', 'years_paid', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('phone',)
    readonly_fields = ('created_at',)
