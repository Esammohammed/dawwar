from django.contrib import admin
from django.utils import timezone
from .models import ScrapeSource, Announcement, AnnouncementStatus

@admin.register(ScrapeSource)
class ScrapeSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'url', 'active', 'last_run_at')
    list_filter = ('kind', 'active')


class NeedsProgramReviewFilter(admin.SimpleListFilter):
    """Surfaces Layer 3 of the program matcher (gov-scraper/matcher.py):
    articles the AI noticed mention a specific program by name, but neither
    the deterministic (regex) nor semantic-similarity layers could link to
    an existing Project. Never auto-linked — this filter is exactly how a
    human finds and confirms these."""
    title = 'program match'
    parameter_name = 'needs_program_review'

    def lookups(self, request, model_admin):
        return (('yes', 'Needs program review (AI-suggested, unmatched)'),)

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(project__isnull=True, suggested_program_name__isnull=False).exclude(suggested_program_name='')
        return queryset


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'project', 'suggested_program_name', 'status', 'published_at', 'scraped_at')
    list_filter = ('status', 'source', 'project', NeedsProgramReviewFilter)
    search_fields = ('title', 'body', 'ai_summary', 'suggested_program_name')
    actions = ['publish_announcements', 'reject_announcements']

    @admin.action(description='Publish selected announcements')
    def publish_announcements(self, request, queryset):
        queryset.update(status=AnnouncementStatus.PUBLISHED, published_at=timezone.now())

    @admin.action(description='Reject selected announcements')
    def reject_announcements(self, request, queryset):
        queryset.update(status=AnnouncementStatus.REJECTED)
