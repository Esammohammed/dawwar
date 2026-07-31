import uuid
from django.db import models
from django.db.models import Q
from apps.developers.models import Developer

class ProjectType(models.TextChoices):
    GOVERNMENT = 'government', 'Government'
    DEVELOPER = 'developer', 'Developer'

class ProjectStatus(models.TextChoices):
    ANNOUNCED = 'announced', 'Announced'
    OPEN_FOR_BOOKING = 'open_for_booking', 'Open for Booking'
    UNDER_CONSTRUCTION = 'under_construction', 'Under Construction'
    DELIVERED = 'delivered', 'Delivered'

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=12, choices=ProjectType.choices)
    developer = models.ForeignKey(Developer, on_delete=models.PROTECT, null=True, blank=True, related_name='projects')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    governorate = models.CharField(max_length=60)
    city = models.CharField(max_length=80)
    district = models.CharField(max_length=80, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.ANNOUNCED)
    details = models.JSONField(default=dict, blank=True)
    cover_image = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects'
        indexes = [
            models.Index(fields=['type', 'status'], name='idx_projects_type_status'),
            models.Index(fields=['governorate', 'city'], name='idx_projects_location'),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(type='developer') & Q(developer__isnull=False)) |
                    (Q(type='government') & Q(developer__isnull=True))
                ),
                name='chk_project_developer'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
