from rest_framework import serializers
from .models import Inquiry, Booking, ExitLead
from apps.listings.serializers import ListingSerializer

class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = ['id', 'listing', 'user', 'phone', 'message', 'status', 'created_at']
        read_only_fields = ['id', 'user', 'status', 'created_at']

class BookingSerializer(serializers.ModelSerializer):
    listing_details = ListingSerializer(source='listing', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'listing', 'listing_details', 'user', 'deposit_amount', 'status', 'expires_at', 'created_at']
        read_only_fields = ['id', 'user', 'status', 'expires_at', 'created_at']

class ExitLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExitLead
        fields = ['id', 'phone', 'contract_price', 'amount_paid', 'years_paid', 'computed_result', 'created_at']
        read_only_fields = ['id', 'created_at']
