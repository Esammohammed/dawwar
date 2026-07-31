from rest_framework import serializers
from .models import Developer

class DeveloperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Developer
        fields = ['id', 'name', 'commercial_register_no', 'contact_phone', 'contact_email', 'logo', 'verified', 'commission_terms', 'notes', 'created_at']
