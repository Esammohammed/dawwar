from rest_framework import viewsets, permissions
from .models import Developer
from .serializers import DeveloperSerializer

class DeveloperViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Developer.objects.filter(verified=True).order_by('-created_at')
    serializer_class = DeveloperSerializer
    permission_classes = [permissions.AllowAny]
