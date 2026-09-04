from django.conf import settings
from rest_framework import serializers
from .models import Listing, Media, ListingStatus, ListingType, ExitVerificationStatus
from apps.projects.serializers import ProjectSerializer
from apps.developers.serializers import DeveloperSerializer


class MediaSerializer(serializers.ModelSerializer):
    # Expose the model's `url` property so consumers always get an absolute URL
    # regardless of whether the backend uses local storage or S3.
    url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ['id', 'url', 'kind', 'sort_order', 'is_primary']

    def get_url(self, obj: Media) -> str:
        request = self.context.get('request')
        raw_url = obj.url
        if request and raw_url and not raw_url.startswith('http'):
            return request.build_absolute_uri(raw_url)
        return raw_url


class ListingSerializer(serializers.ModelSerializer):
    media = MediaSerializer(many=True, read_only=True)
    project_details = ProjectSerializer(source='project', read_only=True)
    developer_details = DeveloperSerializer(source='developer', read_only=True)
    seller_phone = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()

    # "صفقة دوّار" — only populated (non-null) when is_exit_listing is True
    # and exit_verification_status is verified; every ordinary listing gets
    # is_exit_listing=False and the three figures as null, same as they'd
    # never have appeared before this feature existed.
    cash_required_now = serializers.SerializerMethodField()
    market_gain = serializers.SerializerMethodField()
    remaining_to_developer = serializers.SerializerMethodField()

    def get_seller_phone(self, obj):
        if obj.type == ListingType.SCRAPED and obj.source_seller_phone:
            return obj.source_seller_phone
        return obj.seller.phone if obj.seller else None

    def get_seller_name(self, obj):
        if obj.type == ListingType.SCRAPED and obj.source_seller_name:
            return obj.source_seller_name
        return obj.seller.full_name if obj.seller else None

    def _is_verified_exit(self, obj) -> bool:
        return bool(obj.is_exit_listing) and obj.exit_verification_status == ExitVerificationStatus.VERIFIED

    def get_cash_required_now(self, obj):
        if not self._is_verified_exit(obj) or obj.amount_paid is None:
            return None
        return float(obj.amount_paid + (obj.transfer_fee or 0))

    def get_remaining_to_developer(self, obj):
        if not self._is_verified_exit(obj) or obj.original_price is None or obj.amount_paid is None:
            return None
        return float(obj.original_price - obj.amount_paid)

    def get_market_gain(self, obj):
        if not self._is_verified_exit(obj) or not obj.developer_current_price:
            return None
        cash_required = self.get_cash_required_now(obj)
        dev_price = float(obj.developer_current_price)
        rate = float(obj.exit_commission_rate or 0) / 100
        commission = dev_price * rate if obj.exit_commission_payer == 'buyer' else 0
        return dev_price - cash_required - commission

    class Meta:
        model = Listing
        fields = [
            'id', 'type', 'project', 'project_details', 'seller', 'seller_name', 'seller_phone',
            'developer', 'developer_details', 'title', 'description', 'property_type', 'area_sqm', 'bedrooms',
            'bathrooms', 'floor', 'finishing', 'unit_attributes', 'governorate', 'city', 'district',
            'asking_price', 'currency', 'negotiable', 'original_price', 'amount_paid', 'transfer_fee',
            'installment_plan', 'status', 'published_at', 'created_at', 'media',
            'source_site', 'source_url',
            'is_exit_listing', 'developer_current_price', 'exit_verification_status',
            'cash_required_now', 'market_gain', 'remaining_to_developer',
        ]


class ListingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new resale listing.

    Image files are handled separately via the `upload-media` action —
    this serializer only deals with structured JSON data.
    """

    class Meta:
        model = Listing
        fields = [
            'type', 'project', 'title', 'description', 'property_type', 'area_sqm', 'bedrooms',
            'bathrooms', 'floor', 'finishing', 'unit_attributes', 'governorate', 'city',
            'district', 'asking_price', 'currency', 'negotiable', 'original_price',
            'amount_paid', 'transfer_fee', 'installment_plan',
            'is_exit_listing', 'developer_current_price', 'owner_confirmed_no_markup',
        ]

    def validate(self, data):
        # "صفقة دوّار" listings must carry the seller's explicit acknowledgement
        # that they'll receive exactly what they paid — no markup.
        if data.get('is_exit_listing') and not data.get('owner_confirmed_no_markup'):
            raise serializers.ValidationError({
                'owner_confirmed_no_markup': 'You must confirm there is no markup to list a صفقة دوّار transfer.'
            })
        return data

    def create(self, validated_data: dict) -> Listing:
        user = self.context['request'].user
        # `type` is in the serializer fields so the frontend can send it,
        # but we always force RESALE here — pop it to avoid duplicate kwarg.
        validated_data.pop('type', None)
        is_exit_listing = validated_data.get('is_exit_listing', False)
        if is_exit_listing:
            validated_data['exit_verification_status'] = ExitVerificationStatus.PENDING
            validated_data['exit_commission_rate'] = settings.EXIT_DEFAULT_COMMISSION_RATE
        return Listing.objects.create(
            seller=user,
            type=ListingType.RESALE,
            status=ListingStatus.UNDER_REVIEW,
            **validated_data,
        )


class ScrapedListingCreateSerializer(serializers.ModelSerializer):
    """Serializer used by the scraper microservice to import listings."""
    type = serializers.CharField(read_only=True)
    
    class Meta:
        model = Listing
        fields = [
            'type', 'title', 'description', 'property_type', 'area_sqm', 'bedrooms',
            'bathrooms', 'floor', 'finishing', 'unit_attributes', 'governorate', 'city',
            'district', 'asking_price', 'currency', 'negotiable',
            'source_site', 'source_url', 'source_seller_name', 'source_seller_phone'
        ]

    def create(self, validated_data: dict) -> Listing:
        user = self.context['request'].user
        validated_data.pop('type', None)
        return Listing.objects.create(
            seller=user,
            type=ListingType.SCRAPED,
            status=ListingStatus.ACTIVE,  # Auto-activate scraped listings
            **validated_data
        )


class MediaUploadResponseSerializer(serializers.ModelSerializer):
    """Lightweight read-only serializer for the upload-media response."""
    url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ['id', 'url', 'kind', 'sort_order', 'is_primary']

    def get_url(self, obj: Media) -> str:
        request = self.context.get('request')
        raw_url = obj.url
        if request and raw_url and not raw_url.startswith('http'):
            return request.build_absolute_uri(raw_url)
        return raw_url
