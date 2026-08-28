from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .models import Listing, ListingStatus
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
        """Upload one or more image files for an existing listing.

        Accepts ``multipart/form-data`` with field name ``images`` (repeatable).
        Only the listing's owner may upload media.
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

        try:
            service = MediaUploadService(listing)
            media_list = service.upload(files)
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
