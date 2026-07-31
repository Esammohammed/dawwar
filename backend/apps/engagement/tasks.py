from celery import shared_task
from django.utils import timezone
from .models import Booking, BookingStatus
from apps.listings.models import Listing, ListingStatus

@shared_task
def expire_unpaid_bookings_task():
    """
    Celery beat task that finds expired pending bookings, sets their status to EXPIRED,
    and flips their associated listings back to ACTIVE.
    """
    now = timezone.now()
    expired_bookings = Booking.objects.filter(
        status=BookingStatus.PENDING_PAYMENT,
        expires_at__lte=now
    )

    expired_count = 0
    for booking in expired_bookings:
        booking.status = BookingStatus.EXPIRED
        booking.save()

        # Flip listing back to active if it was reserved by this booking
        listing = booking.listing
        if listing.status == ListingStatus.RESERVED:
            listing.status = ListingStatus.ACTIVE
            listing.save()

        expired_count += 1

    return f"Expired {expired_count} unpaid bookings."
