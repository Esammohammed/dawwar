import uuid
from django.db import models
from django.db.models import Q
from django.conf import settings
from apps.listings.models import Listing

class InquiryStatus(models.TextChoices):
    NEW = 'new', 'New'
    CONTACTED = 'contacted', 'Contacted'
    CLOSED = 'closed', 'Closed'

class BookingStatus(models.TextChoices):
    PENDING_PAYMENT = 'pending_payment', 'Pending Payment'
    CONFIRMED = 'confirmed', 'Confirmed'
    EXPIRED = 'expired', 'Expired'
    CANCELLED = 'cancelled', 'Cancelled'

class Inquiry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='inquiries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='inquiries')
    phone = models.CharField(max_length=20)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=InquiryStatus.choices, default=InquiryStatus.NEW)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_inquiries')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inquiries'
        indexes = [
            models.Index(fields=['listing', '-created_at'], name='idx_inq_listing'),
            models.Index(fields=['status', '-created_at'], name='idx_inq_status'),
        ]

    def __str__(self):
        return f"Inquiry from {self.phone} for listing {self.listing_id}"

class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bookings')
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=BookingStatus.choices, default=BookingStatus.PENDING_PAYMENT)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bookings'
        indexes = [
            models.Index(fields=['listing', 'status'], name='idx_book_listing'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['listing'],
                condition=Q(status__in=['pending_payment', 'confirmed']),
                name='uniq_active_booking'
            )
        ]

    def __str__(self):
        return f"Booking {self.id} for Listing {self.listing_id} [{self.status}]"
