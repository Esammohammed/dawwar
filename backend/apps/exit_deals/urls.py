from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    create_exit_profile,
    upload_exit_documents,
    ExitOpportunitiesViewSet,
    ExitLeadViewSet
)

router = DefaultRouter()
router.register(r'opportunities', ExitOpportunitiesViewSet, basename='exit-opportunity')
router.register(r'calculator-leads', ExitLeadViewSet, basename='exit-lead')

urlpatterns = [
    path('', include(router.urls)),
    path('listings/<uuid:listing_id>/profile/', create_exit_profile, name='create-exit-profile'),
    path('listings/<uuid:listing_id>/documents/', upload_exit_documents, name='upload-exit-documents'),
]
