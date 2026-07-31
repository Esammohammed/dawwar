from rest_framework.routers import DefaultRouter
from .views import InquiryViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'inquiries', InquiryViewSet, basename='inquiry')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = router.urls
