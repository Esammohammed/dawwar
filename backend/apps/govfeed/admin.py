from django.contrib import admin
from django.utils import timezone
from .models import ScrapeSource, Announcement, AnnouncementStatus

@admin.register(ScrapeSource)
class ScrapeSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'url', 'active', 'last_run_at')
    list_filter = ('kind', 'active')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'status', 'published_at', 'scraped_at')
    list_filter = ('status', 'source')
    search_fields = ('title', 'body', 'ai_summary')
    actions = ['publish_announcements', 'reject_announcements']

    @admin.action(description='Publish selected announcements')
    def publish_announcements(self, request, queryset):
        queryset.update(status=AnnouncementStatus.PUBLISHED, published_at=timezone.now())

    @admin.action(description='Reject selected announcements')
    def reject_announcements(self, request, queryset):
        queryset.update(status=AnnouncementStatus.REJECTED)
