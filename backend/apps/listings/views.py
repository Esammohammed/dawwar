from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .models import Listing, ListingStatus, ExitVerificationStatus, MediaKind
from .serializers import (
    ListingSerializer,
    ListingCreateSerializer,
    MediaUploadResponseSerializer,
    ScrapedListingCreateSerializer,
)
from .services import MediaUploadService


class IsScraperBot(permissions.BasePermission):
    """Allows access only to the dedicated AI scraper bot."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_bot)


class ListingViewSet(viewsets.ModelViewSet):
    """ViewSet for Listing CRUD and media upload.

    Endpoints
    ---------
    GET    /api/listings/               – public list (active only)
    POST   /api/listings/               – create a new resale listing (auth required)
    GET    /api/listings/{id}/          – retrieve a single listing
    POST   /api/listings/{id}/upload-media/  – upload images for a listing (auth required)
    GET    /api/listings/my-listings/   – authenticated seller's own listings
    """

    queryset = (
        Listing.objects
        .filter(status=ListingStatus.ACTIVE)
        .prefetch_related('media')
        .select_related('project', 'developer', 'seller')
        .order_by('-published_at', '-created_at')
    )
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # ── Serializer selection ──────────────────────────────────────────────────

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ListingCreateSerializer
        return ListingSerializer

    # ── Queryset filtering ────────────────────────────────────────────────────

    def get_queryset(self):
        if self.action == 'my_listings':
            return Listing.objects.filter(seller=self.request.user).order_by('-created_at')

        qs = super().get_queryset()
        params = self.request.query_params

        filters = {
            'type':           ('type',              None),
            'property_type':  ('property_type__iexact', None),
            'project':        ('project_id',        None),
            'governorate':    ('governorate__iexact', None),
            'city':           ('city__iexact',       None),
            'district':       ('district__iexact',   None),
            'min_price':      ('asking_price__gte',  None),
            'max_price':      ('asking_price__lte',  None),
            'bedrooms':       ('bedrooms',           None),
            'finishing':      ('finishing',          None),
        }

        for param, (field, _) in filters.items():
            value = params.get(param)
            if value:
                qs = qs.filter(**{field: value})

        if params.get('has_installments', '').lower() in ('true', '1'):
            qs = qs.filter(installment_plan__isnull=False)

        if params.get('is_verified_exit', '').lower() in ('true', '1'):
            qs = qs.filter(is_exit_listing=True, exit_verification_status=ExitVerificationStatus.VERIFIED)

        return qs

    # ── Create listing ────────────────────────────────────────────────────────

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()
        output = ListingSerializer(listing, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)

    # ── Upload media ──────────────────────────────────────────────────────────

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
        url_path='upload-media',
    )
    def upload_media(self, request, pk=None):
        """Upload one or more files for an existing listing.

        Accepts ``multipart/form-data`` with field name ``images`` (repeatable)
        and an optional ``kind`` field (``photo`` default; also accepts
        ``video``, ``floorplan``, or — for صفقة دوّار listings — ``contract``/
        ``payment_receipt``, which additionally allow PDF). Only the
        listing's owner may upload media.
        """
        # Fetch directly — the base queryset is ACTIVE-only, but the seller
        # needs to upload media while the listing is still UNDER_REVIEW.
        try:
            listing = Listing.objects.get(pk=pk)
        except Listing.DoesNotExist:
            return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Ownership check — only the seller can add images.
        if listing.seller != request.user:
            return Response(
                {'detail': 'You do not have permission to upload media for this listing.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        files = request.FILES.getlist('images')
        if not files:
            return Response(
                {'detail': 'No images provided. Send files under the key "images".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        kind = request.data.get('kind', MediaKind.PHOTO)
        if kind not in MediaKind.values:
            return Response({'detail': f"Invalid kind '{kind}'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = MediaUploadService(listing)
            media_list = service.upload(files, kind=kind)
        except DjangoValidationError as exc:
            return Response(
                {'detail': exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MediaUploadResponseSerializer(
            media_list, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ── My listings ───────────────────────────────────────────────────────────

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='my-listings',
    )
    def my_listings(self, request):
        qs = Listing.objects.filter(seller=request.user).order_by('-created_at')
        serializer = ListingSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # ── صفقة دوّار — verified exit opportunities ─────────────────────────────

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.AllowAny],
        url_path='exit-opportunities',
    )
    def exit_opportunities(self, request):
        """Public list of verified صفقة دوّار listings.

        Supports ``sort``: ``newest`` (default), ``cash_asc`` (lowest cash
        required first), ``gain_desc`` (biggest buyer gain first), and the
        existing filter params (governorate/city/bedrooms/etc.) via the same
        ``get_queryset`` filtering, applied on top of the verified-only base.
        """
        qs = (
            Listing.objects
            .filter(
                status=ListingStatus.ACTIVE,
                is_exit_listing=True,
                exit_verification_status=ExitVerificationStatus.VERIFIED,
            )
            .prefetch_related('media')
            .select_related('project', 'developer', 'seller')
        )

        params = request.query_params
        if params.get('negotiable', '').lower() in ('true', '1'):
            qs = qs.filter(negotiable=True)

        sort = params.get('sort', 'newest')
        if sort == 'cash_asc':
            # cash_required_now = amount_paid + transfer_fee; nulls sort last.
            from django.db.models import F, Value, DecimalField
            from django.db.models.functions import Coalesce
            zero = Value(0, output_field=DecimalField())
            qs = qs.annotate(
                _cash_required=Coalesce(F('amount_paid'), zero) + Coalesce(F('transfer_fee'), zero)
            ).order_by('_cash_required')
        elif sort == 'gain_desc':
            from django.db.models import F, Value, DecimalField
            from django.db.models.functions import Coalesce
            zero = Value(0, output_field=DecimalField())
            qs = qs.annotate(
                _gain=Coalesce(F('developer_current_price'), zero)
                - Coalesce(F('amount_paid'), zero)
                - Coalesce(F('transfer_fee'), zero)
            ).order_by('-_gain')
        else:
            qs = qs.order_by('-created_at')

        page = self.paginate_queryset(qs)
        serializer = ListingSerializer(page or qs, many=True, context={'request': request})
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    # ── Scraper Import ────────────────────────────────────────────────────────

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsScraperBot],
        url_path='scrape-import',
    )
    def scrape_import(self, request):
        """Endpoint for the scraper microservice to import scraped listings."""
        serializer = ScrapedListingCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()
        output = ListingSerializer(listing, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)
