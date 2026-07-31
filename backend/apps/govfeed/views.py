from rest_framework import viewsets, permissions
from .models import Announcement, AnnouncementStatus
from .serializers import AnnouncementSerializer

class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Announcement.objects.filter(status=AnnouncementStatus.PUBLISHED).order_by('-published_at', '-scraped_at')
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.AllowAny]
