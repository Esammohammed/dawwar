import uuid
from django.db import models
from django.conf import settings
from apps.projects.models import Project

class ApplicationStatus(models.TextChoices):
    COLLECTING_DOCS = 'collecting_docs', 'Collecting Documents'
    READY = 'ready', 'Ready for Submission'
    SUBMITTED = 'submitted', 'Submitted to Government'
    ACCEPTED = 'accepted', 'Accepted'
    REJECTED = 'rejected', 'Rejected'
    REFUNDED = 'refunded', 'Refunded'

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='applications')
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='applications')
    status = models.CharField(max_length=18, choices=ApplicationStatus.choices, default=ApplicationStatus.COLLECTING_DOCS)
    documents = models.JSONField(default=list, blank=True)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'applications'
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_apps_user'),
            models.Index(fields=['status'], name='idx_apps_status'),
        ]

    def __str__(self):
        return f"Application {self.id} - {self.user.phone} for {self.project.name}"
