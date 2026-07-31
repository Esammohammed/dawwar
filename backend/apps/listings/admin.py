from django.contrib import admin
from django.utils import timezone
from .models import Listing, Media, ListingStatus

class MediaInline(admin.TabularInline):
    model = Media
    extra = 1

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'asking_price', 'governorate', 'city', 'status', 'published_at', 'created_at')
    list_filter = ('type', 'status', 'governorate', 'finishing')
    search_fields = ('title', 'description', 'city', 'district')
    inlines = [MediaInline]
    actions = ['approve_and_publish', 'mark_as_sold']

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

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('listing', 'kind', 'file', 'sort_order')
    list_filter = ('kind',)
