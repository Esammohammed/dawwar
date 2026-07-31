from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Application
from .serializers import ApplicationSerializer, ApplicationCreateSerializer

class ApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ApplicationCreateSerializer
        return ApplicationSerializer

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).select_related('project').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        output_serializer = ApplicationSerializer(application)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
