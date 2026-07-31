from rest_framework import serializers
from .models import Announcement, ScrapeSource

class ScrapeSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapeSource
        fields = ['id', 'name', 'url', 'kind', 'active', 'last_run_at']

class AnnouncementSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'source', 'source_name', 'project', 'title', 'body', 'ai_summary', 'source_url', 'status', 'published_at', 'scraped_at']
