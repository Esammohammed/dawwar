from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Announcement, AnnouncementStatus
from .serializers import AnnouncementSerializer, AnnouncementScrapeImportSerializer
# Reused as-is from apps.listings — "is this the scraper bot" is an identity
# check, not a listings-specific concern; no reason to duplicate it.
from apps.listings.views import IsScraperBot


class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Announcement.objects.filter(status=AnnouncementStatus.PUBLISHED).order_by('-published_at', '-scraped_at')
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsScraperBot],
        url_path='scrape-import',
    )
    def scrape_import(self, request):
        """Ingestion endpoint for the gov-scraper microservice.

        Mirrors apps.listings.ListingViewSet.scrape_import — same bot-only
        gate, same "always lands as pending_review, a human publishes"
        workflow. Bumps the matched ScrapeSource's last_run_at so staff can
        see the pipeline is actually alive.
        """
        serializer = AnnouncementScrapeImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save()

        announcement.source.last_run_at = timezone.now()
        announcement.source.save(update_fields=['last_run_at'])

        output = AnnouncementSerializer(announcement, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)
