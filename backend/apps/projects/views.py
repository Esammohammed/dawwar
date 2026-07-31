from rest_framework import viewsets, permissions
from .models import Project
from .serializers import ProjectSerializer

class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.select_related('developer').all().order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super().get_queryset()
        project_type = self.request.query_params.get('type')
        governorate = self.request.query_params.get('governorate')
        status_param = self.request.query_params.get('status')

        if project_type:
            qs = qs.filter(type=project_type)
        if governorate:
            qs = qs.filter(governorate__iexact=governorate)
        if status_param:
            qs = qs.filter(status=status_param)

        return qs
