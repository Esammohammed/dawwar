from rest_framework import serializers
from .models import Application
from apps.projects.serializers import ProjectSerializer

class ApplicationSerializer(serializers.ModelSerializer):
    project_details = ProjectSerializer(source='project', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'user', 'project', 'project_details', 'status', 'documents', 'service_fee', 'paid', 'submitted_at', 'notes', 'created_at']
        read_only_fields = ['id', 'user', 'status', 'paid', 'submitted_at', 'created_at']

class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['project', 'documents', 'service_fee', 'notes']

    def create(self, validated_data):
        user = self.context['request'].user
        return Application.objects.create(user=user, **validated_data)
