from django.contrib import admin
from django.utils import timezone
from .models import Listing, Media, ListingStatus, ExitVerificationStatus

class MediaInline(admin.TabularInline):
    model = Media
    extra = 1

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'type', 'asking_price', 'governorate', 'city', 'status',
        'is_exit_listing', 'exit_verification_status', 'published_at', 'created_at',
    )
    list_filter = ('type', 'status', 'governorate', 'finishing', 'is_exit_listing', 'exit_verification_status')
    search_fields = ('title', 'description', 'city', 'district')
    inlines = [MediaInline]
    actions = ['approve_and_publish', 'mark_as_sold', 'mark_exit_verified', 'mark_exit_rejected']
    fieldsets = (
        (None, {
            'fields': (
                'type', 'title', 'description', 'property_type', 'seller', 'developer', 'project',
                'status', 'reviewed_by', 'published_at',
            ),
        }),
        ('Unit facts', {
            'fields': ('area_sqm', 'bedrooms', 'bathrooms', 'floor', 'finishing', 'unit_attributes'),
        }),
        ('Location', {
            'fields': ('governorate', 'city', 'district'),
        }),
        ('Money', {
            'fields': ('asking_price', 'currency', 'negotiable', 'original_price', 'amount_paid', 'transfer_fee', 'installment_plan'),
        }),
        ('صفقة دوّار — verified contract-exit', {
            'fields': (
                'is_exit_listing', 'developer_current_price', 'owner_confirmed_no_markup',
                'exit_verification_status', 'exit_verification_notes',
                'exit_commission_payer', 'exit_commission_rate',
            ),
        }),
        ('Scraped source', {
            'classes': ('collapse',),
            'fields': ('source_site', 'source_url', 'source_seller_name', 'source_seller_phone'),
        }),
    )

    @admin.action(description='Approve and Publish selected listings')
    def approve_and_publish(self, request, queryset):
        queryset.update(
            status=ListingStatus.ACTIVE,
            reviewed_by=request.user,
            published_at=timezone.now()
        )

    @admin.action(description='Mark selected listings as Sold')
    def mark_as_sold(self, request, queryset):
        queryset.update(status=ListingStatus.SOLD)

    @admin.action(description='صفقة دوّار: mark exit-verified')
    def mark_exit_verified(self, request, queryset):
        queryset.filter(is_exit_listing=True).update(exit_verification_status=ExitVerificationStatus.VERIFIED)

    @admin.action(description='صفقة دوّار: mark exit-rejected')
    def mark_exit_rejected(self, request, queryset):
        queryset.filter(is_exit_listing=True).update(exit_verification_status=ExitVerificationStatus.REJECTED)

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('listing', 'kind', 'file', 'sort_order')
    list_filter = ('kind',)
