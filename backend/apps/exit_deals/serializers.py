from rest_framework import serializers
from .models import ExitListing, ExitDocument, ExitLead

class ExitDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExitDocument
        fields = ['id', 'doc_type', 'url', 'uploaded_at']

class ExitListingSerializer(serializers.ModelSerializer):
    documents = ExitDocumentSerializer(many=True, read_only=True)
    cash_required_now = serializers.SerializerMethodField()
    remaining_to_developer = serializers.SerializerMethodField()
    market_gain = serializers.SerializerMethodField()
    
    class Meta:
        model = ExitListing
        fields = [
            'id', 'developer_current_price', 'owner_confirmed_no_markup',
            'verification_status', 'commission_payer', 'commission_rate',
            'created_at', 'documents',
            'cash_required_now', 'remaining_to_developer', 'market_gain'
        ]
        
    def get_cash_required_now(self, obj):
        listing = obj.listing
        if listing.amount_paid is None:
            return 0
        transfer = listing.transfer_fee or 0
        return float(listing.amount_paid + transfer)
        
    def get_remaining_to_developer(self, obj):
        listing = obj.listing
        if listing.original_price is None or listing.amount_paid is None:
            return 0
        return float(listing.original_price - listing.amount_paid)
        
    def get_market_gain(self, obj):
        if not obj.developer_current_price:
            return None
        # Market gain = dev_current - cash_required - (dev_current * commission)
        cash_req = self.get_cash_required_now(obj)
        dev_price = float(obj.developer_current_price)
        comm_rate = float(obj.commission_rate) / 100
        commission = dev_price * comm_rate if obj.commission_payer == 'buyer' else 0
        return dev_price - cash_req - commission

class ExitListingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExitListing
        fields = ['developer_current_price', 'owner_confirmed_no_markup']
        
    def validate_owner_confirmed_no_markup(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm that there is no markup.")
        return value

class ExitLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExitLead
        fields = ['id', 'phone', 'contract_price', 'amount_paid', 'years_paid', 'computed_result', 'created_at']
        read_only_fields = ['id', 'created_at']
