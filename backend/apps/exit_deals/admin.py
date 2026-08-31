from django.contrib import admin
from .models import ExitListing, ExitDocument, ExitLead, VerificationStatus

class ExitDocumentInline(admin.TabularInline):
    model = ExitDocument
    extra = 0
    readonly_fields = ('uploaded_at', 'url')

@admin.register(ExitListing)
class ExitListingAdmin(admin.ModelAdmin):
    list_display = ('listing_title', 'verification_status', 'commission_payer', 'created_at')
    list_filter = ('verification_status', 'commission_payer', 'created_at')
    search_fields = ('listing__title', 'listing__id')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ExitDocumentInline]
    
    actions = ['mark_verified', 'mark_rejected']
    
    def listing_title(self, obj):
        return obj.listing.title
    listing_title.short_description = 'Listing'
    
    @admin.action(description='Mark selected exit listings as verified')
    def mark_verified(self, request, queryset):
        queryset.update(verification_status=VerificationStatus.VERIFIED)
        
    @admin.action(description='Mark selected exit listings as rejected')
    def mark_rejected(self, request, queryset):
        queryset.update(verification_status=VerificationStatus.REJECTED)

@admin.register(ExitLead)
class ExitLeadAdmin(admin.ModelAdmin):
    list_display = ('phone', 'contract_price', 'amount_paid', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('phone',)
    readonly_fields = ('created_at', 'computed_result')
