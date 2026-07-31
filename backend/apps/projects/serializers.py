from rest_framework import serializers
from .models import Project
from apps.developers.serializers import DeveloperSerializer

class ProjectSerializer(serializers.ModelSerializer):
    developer_details = DeveloperSerializer(source='developer', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'type', 'developer', 'developer_details', 'name', 'slug', 'governorate', 'city', 'district', 'description', 'status', 'details', 'cover_image', 'created_at']
