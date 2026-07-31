from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.developers.models import Developer
from apps.projects.models import Project, ProjectType
from apps.listings.models import Listing, ListingType, ListingStatus
from apps.engagement.models import Booking, BookingStatus
from apps.engagement.tasks import expire_unpaid_bookings_task
from rest_framework.test import APIClient

User = get_user_model()

class EngagementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone='01055554444', full_name='مشتري حجز')
        self.seller = User.objects.create_user(phone='01155554444', full_name='بائع')
        
        self.dev = Developer.objects.create(name='مطور اختبار', contact_phone='0100')
        self.project = Project.objects.create(
            name='مشروع اختبار',
            type=ProjectType.DEVELOPER,
            developer=self.dev,
            slug='test-project',
            governorate='الجيزة',
            city='6 أكتوبر'
        )
        self.listing = Listing.objects.create(
            title='شقة حجز',
            type=ListingType.DEVELOPER_UNIT,
            project=self.project,
            developer=self.dev,
            area_sqm=Decimal('100.0'),
            asking_price=Decimal('1000000.0'),
            governorate='الجيزة',
            city='6 أكتوبر',
            status=ListingStatus.ACTIVE
        )

    def test_booking_creation_and_expiry(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/bookings/', {'listing': str(self.listing.id)}, format='json')
        self.assertEqual(res.status_code, 201)

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, ListingStatus.RESERVED)

        # Test duplicate active booking restriction
        res2 = self.client.post('/api/bookings/', {'listing': str(self.listing.id)}, format='json')
        self.assertEqual(res2.status_code, 400)

        # Test expiration task
        booking = Booking.objects.get(id=res.data['id'])
        booking.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        booking.save()

        result_msg = expire_unpaid_bookings_task()
        self.assertIn('Expired 1 unpaid bookings', result_msg)

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, ListingStatus.ACTIVE)
