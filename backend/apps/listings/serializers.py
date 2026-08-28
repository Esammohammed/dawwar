from rest_framework import serializers
from .models import Listing, Media, ListingStatus, ListingType
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

    def get_seller_phone(self, obj):
        if obj.type == ListingType.SCRAPED and obj.source_seller_phone:
            return obj.source_seller_phone
        return obj.seller.phone if obj.seller else None

    def get_seller_name(self, obj):
        if obj.type == ListingType.SCRAPED and obj.source_seller_name:
            return obj.source_seller_name
        return obj.seller.full_name if obj.seller else None

    class Meta:
        model = Listing
        fields = [
            'id', 'type', 'project', 'project_details', 'seller', 'seller_name', 'seller_phone',
            'developer', 'developer_details', 'title', 'description', 'area_sqm', 'bedrooms',
            'bathrooms', 'floor', 'finishing', 'unit_attributes', 'governorate', 'city', 'district',
            'asking_price', 'currency', 'negotiable', 'original_price', 'amount_paid', 'transfer_fee',
            'installment_plan', 'status', 'published_at', 'created_at', 'media',
            'source_site', 'source_url'
        ]


class ListingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new resale listing.

    Image files are handled separately via the `upload-media` action —
    this serializer only deals with structured JSON data.
    """

    class Meta:
        model = Listing
        fields = [
            'type', 'project', 'title', 'description', 'area_sqm', 'bedrooms',
            'bathrooms', 'floor', 'finishing', 'unit_attributes', 'governorate', 'city',
            'district', 'asking_price', 'currency', 'negotiable', 'original_price',
            'amount_paid', 'transfer_fee', 'installment_plan',
        ]

    def create(self, validated_data: dict) -> Listing:
        user = self.context['request'].user
        # `type` is in the serializer fields so the frontend can send it,
        # but we always force RESALE here — pop it to avoid duplicate kwarg.
        validated_data.pop('type', None)
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
            'type', 'title', 'description', 'area_sqm', 'bedrooms',
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
