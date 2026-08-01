from decimal import Decimal

from rest_framework.test import APIClient, APITestCase

from apps.developers.models import Developer
from apps.projects.models import Project, ProjectStatus, ProjectType

from .models import Listing, ListingStatus, ListingType


class ListingProjectFilterTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.developer = Developer.objects.create(name='Palm Hills', contact_phone='01000000000')
        self.project_a = Project.objects.create(
            type=ProjectType.DEVELOPER,
            developer=self.developer,
            name='Palm Hills Badya',
            slug='palm-hills-badya',
            governorate='Giza',
            city='6th of October',
            status=ProjectStatus.OPEN_FOR_BOOKING,
        )
        self.project_b = Project.objects.create(
            type=ProjectType.DEVELOPER,
            developer=self.developer,
            name='Mountain View iCity',
            slug='mountain-view-icity',
            governorate='Cairo',
            city='New Cairo',
            status=ProjectStatus.UNDER_CONSTRUCTION,
        )
        self.listing_a = self._make_listing(self.project_a, 'Unit in Badya')
        self.listing_b = self._make_listing(self.project_b, 'Unit in iCity')

    def _make_listing(self, project, title):
        return Listing.objects.create(
            type=ListingType.DEVELOPER_UNIT,
            project=project,
            developer=self.developer,
            title=title,
            area_sqm=Decimal('120.00'),
            governorate=project.governorate,
            city=project.city,
            asking_price=Decimal('3000000.00'),
            status=ListingStatus.ACTIVE,
        )

    def test_filter_by_project_returns_only_its_listings(self):
        res = self.client.get('/api/listings/', {'project': str(self.project_a.id)})
        self.assertEqual(res.status_code, 200)
        ids = {item['id'] for item in res.data.get('results', res.data)}
        self.assertEqual(ids, {str(self.listing_a.id)})

    def test_no_project_filter_returns_all_active_listings(self):
        res = self.client.get('/api/listings/')
        self.assertEqual(res.status_code, 200)
        ids = {item['id'] for item in res.data.get('results', res.data)}
        self.assertEqual(ids, {str(self.listing_a.id), str(self.listing_b.id)})

    def test_unknown_project_returns_empty(self):
        res = self.client.get('/api/listings/', {'project': '00000000-0000-0000-0000-000000000000'})
        self.assertEqual(res.status_code, 200)
        ids = res.data.get('results', res.data)
        self.assertEqual(ids, [])
