from rest_framework import serializers
from .models import Listing, Media, ListingStatus, ListingType
from apps.projects.serializers import ProjectSerializer
from apps.developers.serializers import DeveloperSerializer

class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['id', 'file', 'kind', 'sort_order']

class ListingSerializer(serializers.ModelSerializer):
    media = MediaSerializer(many=True, read_only=True)
    project_details = ProjectSerializer(source='project', read_only=True)
    developer_details = DeveloperSerializer(source='developer', read_only=True)
    seller_phone = serializers.CharField(source='seller.phone', read_only=True)
    seller_name = serializers.CharField(source='seller.full_name', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'type', 'project', 'project_details', 'seller', 'seller_name', 'seller_phone',
            'developer', 'developer_details', 'title', 'description', 'area_sqm', 'bedrooms',
            'bathrooms', 'floor', 'finishing', 'unit_attributes', 'governorate', 'city', 'district',
            'asking_price', 'currency', 'negotiable', 'original_price', 'amount_paid', 'transfer_fee',
            'installment_plan', 'status', 'published_at', 'created_at', 'media'
        ]

class ListingCreateSerializer(serializers.ModelSerializer):
    uploaded_media = serializers.ListField(
        child=serializers.CharField(max_length=500),
        write_only=True,
        required=False
    )

    class Meta:
        model = Listing
        fields = [
            'type', 'project', 'title', 'description', 'area_sqm', 'bedrooms',
            'bathrooms', 'floor', 'finishing', 'unit_attributes', 'governorate', 'city',
            'district', 'asking_price', 'currency', 'negotiable', 'original_price',
            'amount_paid', 'transfer_fee', 'installment_plan', 'uploaded_media'
        ]

    def create(self, validated_data):
        uploaded_media = validated_data.pop('uploaded_media', [])
        user = self.context['request'].user
        
        listing = Listing.objects.create(
            seller=user,
            type=ListingType.RESALE,
            status=ListingStatus.UNDER_REVIEW, # Default status for seller submissions
            **validated_data
        )

        for index, file_url in enumerate(uploaded_media):
            Media.objects.create(
                listing=listing,
                file=file_url,
                sort_order=index
            )

        return listing
