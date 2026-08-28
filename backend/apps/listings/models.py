import uuid
from django.db import models
from django.db.models import Q
from django.conf import settings
from apps.projects.models import Project
from apps.developers.models import Developer

class ListingType(models.TextChoices):
    RESALE = 'resale', 'Resale'
    DEVELOPER_UNIT = 'developer_unit', 'Developer Unit'
    SCRAPED = 'scraped', 'Scraped from Web'

class FinishingType(models.TextChoices):
    CORE_SHELL = 'core_shell', 'Core & Shell (طوب أحمر)'
    SEMI = 'semi', 'Semi Finished (نصف تشطيب)'
    FULLY = 'fully', 'Fully Finished (تشطيب كامل)'
    LUX = 'lux', 'Lux / Super Lux (سوبر لوكس)'

class ListingStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    UNDER_REVIEW = 'under_review', 'Under Review'
    ACTIVE = 'active', 'Active'
    RESERVED = 'reserved', 'Reserved'
    SOLD = 'sold', 'Sold'
    ARCHIVED = 'archived', 'Archived'

class MediaKind(models.TextChoices):
    PHOTO = 'photo', 'Photo'
    VIDEO = 'video', 'Video'
    FLOORPLAN = 'floorplan', 'Floorplan'

class Listing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=15, choices=ListingType.choices)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, null=True, blank=True, related_name='listings')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='resale_listings')
    developer = models.ForeignKey(Developer, on_delete=models.PROTECT, null=True, blank=True, related_name='developer_listings')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    # Unit Facts
    area_sqm = models.DecimalField(max_digits=7, decimal_places=2)
    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.PositiveSmallIntegerField(default=0)
    floor = models.SmallIntegerField(null=True, blank=True)
    finishing = models.CharField(max_length=12, choices=FinishingType.choices, null=True, blank=True)
    unit_attributes = models.JSONField(default=dict, blank=True)

    # Location
    governorate = models.CharField(max_length=60)
    city = models.CharField(max_length=80)
    district = models.CharField(max_length=80, blank=True, null=True)

    # Money
    asking_price = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='EGP')
    negotiable = models.BooleanField(default=True)

    # Resale / Takeover Fields
    original_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    transfer_fee = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    installment_plan = models.JSONField(null=True, blank=True)

    # Scraped Source Fields
    source_site = models.CharField(max_length=50, null=True, blank=True, choices=[('propertyfinder', 'Property Finder'), ('dubizzle', 'Dubizzle')])
    source_url = models.URLField(max_length=500, null=True, blank=True, unique=True)
    source_seller_phone = models.CharField(max_length=50, null=True, blank=True)
    source_seller_name = models.CharField(max_length=150, null=True, blank=True)

    # Workflow
    status = models.CharField(max_length=15, choices=ListingStatus.choices, default=ListingStatus.DRAFT)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_listings')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'listings'
        indexes = [
            models.Index(fields=['status', 'governorate', 'city'], name='idx_listings_search'),
            models.Index(fields=['status', 'asking_price'], name='idx_listings_price'),
            models.Index(fields=['status', 'bedrooms'], name='idx_listings_bedrooms'),
            models.Index(fields=['type', 'status'], name='idx_listings_type'),
            models.Index(fields=['project'], name='idx_listings_project'),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(type='resale') & Q(seller__isnull=False)) |
                    (Q(type='developer_unit') & Q(developer__isnull=False) & Q(project__isnull=False)) |
                    (Q(type='scraped') & Q(seller__isnull=False))
                ),
                name='chk_listing_owner'
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.asking_price} EGP [{self.status}]"

class Media(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='media')
    # ImageField stores files on disk (MEDIA_ROOT/listings/YYYY/MM/).
    # To swap to S3 in production, simply set DEFAULT_FILE_STORAGE in settings —
    # no model or service code needs to change.
    file = models.ImageField(upload_to='listings/%Y/%m/')
    kind = models.CharField(max_length=10, choices=MediaKind.choices, default=MediaKind.PHOTO)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_primary = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'media'
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['listing', 'sort_order'], name='idx_media_listing'),
        ]

    @property
    def url(self) -> str:
        """Return the publicly accessible URL for this media file.

        Works for both local file storage (returns /media/...) and
        cloud storage backends (returns a full https:// URL).
        """
        return self.file.url if self.file else ''

    def __str__(self):
        return f"Media {self.kind} for {self.listing_id}"
