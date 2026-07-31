import uuid
import hashlib
from django.db import models
from apps.projects.models import Project

class SourceKind(models.TextChoices):
    RSS = 'rss', 'RSS Feed'
    HTML = 'html', 'HTML Page'
    API = 'api', 'REST API'
    FACEBOOK_PAGE = 'facebook_page', 'Facebook Page'

class AnnouncementStatus(models.TextChoices):
    PENDING_REVIEW = 'pending_review', 'Pending Review'
    PUBLISHED = 'published', 'Published'
    REJECTED = 'rejected', 'Rejected'

class ScrapeSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    url = models.CharField(max_length=500)
    kind = models.CharField(max_length=15, choices=SourceKind.choices)
    active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'scrape_sources'

    def __str__(self):
        return f"{self.name} ({self.kind})"

class Announcement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(ScrapeSource, on_delete=models.PROTECT, related_name='announcements')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    title = models.CharField(max_length=300)
    body = models.TextField()
    ai_summary = models.TextField(blank=True, null=True)
    source_url = models.CharField(max_length=700)
    source_url_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=15, choices=AnnouncementStatus.choices, default=AnnouncementStatus.PENDING_REVIEW)
    published_at = models.DateTimeField(null=True, blank=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'announcements'
        indexes = [
            models.Index(fields=['status', '-published_at'], name='idx_ann_status_pub'),
        ]

    def save(self, *args, **kwargs):
        if not self.source_url_hash and self.source_url:
            self.source_url_hash = hashlib.sha256(self.source_url.strip().encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} [{self.status}]"
