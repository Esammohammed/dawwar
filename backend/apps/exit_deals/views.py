from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from apps.listings.models import Listing, ListingStatus
from apps.listings.serializers import ListingSerializer

from .models import ExitListing, ExitLead, VerificationStatus, DocumentType
from .serializers import (
    ExitListingSerializer, 
    ExitListingCreateSerializer,
    ExitDocumentSerializer,
    ExitLeadSerializer
)
from .services import ExitDocumentUploadService

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_exit_profile(request, listing_id):
    """Attach ExitListing metadata to an already-created listing."""
    try:
        listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    if listing.seller != request.user:
        return Response(
            {'detail': 'You do not have permission to modify this listing.'},
            status=status.HTTP_403_FORBIDDEN,
        )
        
    if hasattr(listing, 'exit_profile'):
        return Response(
            {'detail': 'This listing already has an exit profile.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
        
    serializer = ExitListingCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    
    exit_listing = serializer.save(listing=listing)
    
    output = ExitListingSerializer(exit_listing, context={'request': request})
    return Response(output.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_exit_documents(request, listing_id):
    """Upload contracts and payment receipts for an exit listing."""
    try:
        listing = Listing.objects.select_related('exit_profile').get(id=listing_id)
    except Listing.DoesNotExist:
        return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    if listing.seller != request.user:
        return Response(
            {'detail': 'You do not have permission to upload documents for this listing.'},
            status=status.HTTP_403_FORBIDDEN,
        )
        
    if not hasattr(listing, 'exit_profile'):
        return Response(
            {'detail': 'This listing does not have an exit profile.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
        
    files = request.FILES.getlist('documents')
    doc_type = request.data.get('doc_type', DocumentType.OTHER)
    
    if not files:
        return Response(
            {'detail': 'No documents provided. Send files under the key "documents".'},
            status=status.HTTP_400_BAD_REQUEST,
        )
        
    try:
        service = ExitDocumentUploadService(listing.exit_profile)
        docs = service.upload(files, doc_type=doc_type)
    except DjangoValidationError as exc:
        return Response(
            {'detail': exc.message},
            status=status.HTTP_400_BAD_REQUEST,
        )
        
    serializer = ExitDocumentSerializer(docs, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)

class ExitOpportunitiesViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view for verified exit opportunities."""
    permission_classes = [permissions.AllowAny]
    serializer_class = ListingSerializer
    
    def get_queryset(self):
        qs = (
            Listing.objects
            .filter(
                status=ListingStatus.ACTIVE,
                exit_profile__verification_status=VerificationStatus.VERIFIED
            )
            .select_related('exit_profile', 'project', 'developer', 'seller')
            .prefetch_related('media')
        )
        
        # We can implement specific exit deal sorting if needed via query params
        # (newest, lowest cash required, biggest gain, negotiable)
        # For now we order by created_at
        return qs.order_by('-created_at')

class ExitLeadViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Endpoint for calculator lead capture."""
    permission_classes = [permissions.AllowAny]
    serializer_class = ExitLeadSerializer
    queryset = ExitLead.objects.all()
