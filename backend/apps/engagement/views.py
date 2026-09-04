from datetime import timedelta
from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from .models import Inquiry, Booking, BookingStatus, ExitLead
from .serializers import InquirySerializer, BookingSerializer, ExitLeadSerializer
from apps.listings.models import Listing, ListingStatus

class InquiryViewSet(viewsets.ModelViewSet):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user if request.user.is_authenticated else None
        inquiry = serializer.save(user=user)

        return Response(InquirySerializer(inquiry).data, status=status.HTTP_201_CREATED)

class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related('listing').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        listing_id = request.data.get('listing')
        deposit_amount = request.data.get('deposit_amount', 10000)

        if not listing_id:
            return Response({'error': 'listing ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Lock the listing row to prevent race conditions
                listing = Listing.objects.select_for_update().get(id=listing_id)

                if listing.status != ListingStatus.ACTIVE:
                    return Response({'error': 'Listing is no longer available for booking'}, status=status.HTTP_400_BAD_REQUEST)

                # Set 24 hour expiry window for deposit payment
                expires_at = timezone.now() + timedelta(hours=24)

                booking = Booking.objects.create(
                    listing=listing,
                    user=request.user,
                    deposit_amount=deposit_amount,
                    status=BookingStatus.PENDING_PAYMENT,
                    expires_at=expires_at
                )

                # Reserve the listing
                listing.status = ListingStatus.RESERVED
                listing.save()

                return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

        except Listing.DoesNotExist:
            return Response({'error': 'Listing not found'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'error': 'This listing already has an active booking'}, status=status.HTTP_409_CONFLICT)

class ExitLeadViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """صفقة دوّار calculator lead capture — no login required (matches the
    calculator itself, which shows results with no auth call)."""
    queryset = ExitLead.objects.all()
    serializer_class = ExitLeadSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'exit_lead'
