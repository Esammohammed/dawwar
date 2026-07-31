from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Listing, ListingStatus, ListingType
from .serializers import ListingSerializer, ListingCreateSerializer

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.filter(status=ListingStatus.ACTIVE).prefetch_related('media').select_related('project', 'developer', 'seller').order_by('-published_at', '-created_at')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ListingCreateSerializer
        return ListingSerializer

    def get_queryset(self):
        if self.action == 'my_listings':
            return Listing.objects.filter(seller=self.request.user).order_by('-created_at')
            
        qs = super().get_queryset()
        params = self.request.query_params

        listing_type = params.get('type')
        governorate = params.get('governorate')
        city = params.get('city')
        district = params.get('district')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        bedrooms = params.get('bedrooms')
        finishing = params.get('finishing')
        has_installments = params.get('has_installments')

        if listing_type:
            qs = qs.filter(type=listing_type)
        if governorate:
            qs = qs.filter(governorate__iexact=governorate)
        if city:
            qs = qs.filter(city__iexact=city)
        if district:
            qs = qs.filter(district__iexact=district)
        if min_price:
            qs = qs.filter(asking_price__gte=min_price)
        if max_price:
            qs = qs.filter(asking_price__lte=max_price)
        if bedrooms:
            qs = qs.filter(bedrooms=bedrooms)
        if finishing:
            qs = qs.filter(finishing=finishing)
        if has_installments and has_installments.lower() in ['true', '1']:
            qs = qs.filter(installment_plan__isnull=False)

        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()
        output_serializer = ListingSerializer(listing)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='my-listings')
    def my_listings(self, request):
        qs = Listing.objects.filter(seller=request.user).order_by('-created_at')
        serializer = ListingSerializer(qs, many=True)
        return Response(serializer.data)
