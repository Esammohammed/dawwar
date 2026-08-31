"""
Tests for the exit_deals app.

Covers:
- ExitListing model & ExitLead model creation
- ExitDocumentUploadService validation
- Calculator utility
- API endpoints: create_exit_profile, upload_documents, opportunities, calculator-leads
"""
import io
import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.listings.models import Listing, ListingType, ListingStatus
from apps.exit_deals.models import (
    ExitListing, ExitDocument, ExitLead,
    VerificationStatus, CommissionPayer, DocumentType
)
from apps.exit_deals.services import ExitDocumentUploadService

User = get_user_model()


# ─── Helper factories ──────────────────────────────────────────────────────────

def make_user(**kwargs):
    defaults = dict(phone='+201000000001', email='seller@test.com')
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_listing(seller, **kwargs):
    defaults = dict(
        title='Test Unit',
        type=ListingType.RESALE,
        status=ListingStatus.ACTIVE,
        area_sqm=100,
        bedrooms=2,
        bathrooms=1,
        asking_price=Decimal('1500000'),
        original_price=Decimal('1000000'),
        amount_paid=Decimal('400000'),
        transfer_fee=Decimal('25000'),
        governorate='Giza',
        city='Sheikh Zayed',
    )
    defaults.update(kwargs)
    return Listing.objects.create(seller=seller, **defaults)


def make_exit_listing(listing, **kwargs):
    defaults = dict(
        developer_current_price=Decimal('1800000'),
        owner_confirmed_no_markup=True,
        verification_status=VerificationStatus.PENDING,
        commission_payer=CommissionPayer.BUYER,
        commission_rate=Decimal('1.25'),
    )
    defaults.update(kwargs)
    return ExitListing.objects.create(listing=listing, **defaults)


def fake_file(name='contract.pdf', content_type='application/pdf', size=1024):
    """Create an in-memory file object mimicking InMemoryUploadedFile."""
    from django.core.files.uploadedfile import InMemoryUploadedFile
    f = io.BytesIO(b'%PDF-1.4 fake content' * (size // 20 + 1))
    f.name = name
    f.content_type = content_type
    f.size = size
    return InMemoryUploadedFile(f, 'file', name, content_type, size, None)


# ─── Model Tests ───────────────────────────────────────────────────────────────

class ExitListingModelTests(TestCase):
    def setUp(self):
        self.seller = make_user()
        self.listing = make_listing(self.seller)

    def test_create_exit_listing_with_defaults(self):
        el = make_exit_listing(self.listing)
        self.assertEqual(el.verification_status, VerificationStatus.PENDING)
        self.assertEqual(el.commission_payer, CommissionPayer.BUYER)
        self.assertEqual(el.commission_rate, Decimal('1.25'))
        self.assertTrue(el.owner_confirmed_no_markup)

    def test_one_to_one_relationship(self):
        el = make_exit_listing(self.listing)
        self.assertEqual(self.listing.exit_profile, el)
        self.assertEqual(el.listing, self.listing)

    def test_str_representation(self):
        el = make_exit_listing(self.listing)
        self.assertIn('Test Unit', str(el))

    def test_duplicate_exit_listing_raises_error(self):
        make_exit_listing(self.listing)
        from django.db import IntegrityError
        with self.assertRaises(Exception):  # IntegrityError from OneToOne
            make_exit_listing(self.listing)

    def test_verification_status_choices(self):
        el = make_exit_listing(self.listing)
        el.verification_status = VerificationStatus.VERIFIED
        el.save()
        el.refresh_from_db()
        self.assertEqual(el.verification_status, VerificationStatus.VERIFIED)

    def test_delete_listing_cascades_to_exit_listing(self):
        el = make_exit_listing(self.listing)
        exit_id = el.id
        self.listing.delete()
        self.assertFalse(ExitListing.objects.filter(id=exit_id).exists())


class ExitLeadModelTests(TestCase):
    def test_create_lead_with_minimal_data(self):
        lead = ExitLead.objects.create(
            contract_price=Decimal('5000000'),
            amount_paid=Decimal('1000000'),
            years_paid=Decimal('2.0'),
        )
        self.assertIsNone(lead.phone)
        self.assertIsNotNone(lead.created_at)

    def test_create_lead_with_phone_and_computed_result(self):
        result = {'transferRecovery': 1000000, 'cancelRecovery': 700000}
        lead = ExitLead.objects.create(
            phone='+201000000001',
            contract_price=Decimal('5000000'),
            amount_paid=Decimal('1000000'),
            years_paid=Decimal('2.0'),
            computed_result=result,
        )
        self.assertEqual(lead.phone, '+201000000001')
        self.assertEqual(lead.computed_result['transferRecovery'], 1000000)

    def test_str_representation_with_phone(self):
        lead = ExitLead.objects.create(
            phone='+20100',
            contract_price=Decimal('1000000'),
            amount_paid=Decimal('300000'),
            years_paid=Decimal('1.0'),
        )
        self.assertIn('+20100', str(lead))

    def test_str_representation_without_phone(self):
        lead = ExitLead.objects.create(
            contract_price=Decimal('1000000'),
            amount_paid=Decimal('300000'),
            years_paid=Decimal('1.0'),
        )
        self.assertIn('Anonymous', str(lead))


# ─── Service Tests ─────────────────────────────────────────────────────────────

class ExitDocumentUploadServiceTests(TestCase):
    def setUp(self):
        self.seller = make_user()
        self.listing = make_listing(self.seller)
        self.exit_listing = make_exit_listing(self.listing)

    def test_upload_valid_pdf(self):
        svc = ExitDocumentUploadService(self.exit_listing)
        f = fake_file('contract.pdf', 'application/pdf', 1024)
        docs = svc.upload([f], doc_type=DocumentType.CONTRACT)
        self.assertEqual(len(docs), 1)
        self.assertIsInstance(docs[0], ExitDocument)
        self.assertEqual(docs[0].doc_type, DocumentType.CONTRACT)

    def test_upload_valid_image(self):
        svc = ExitDocumentUploadService(self.exit_listing)
        f = fake_file('receipt.jpg', 'image/jpeg', 512)
        docs = svc.upload([f], doc_type=DocumentType.PAYMENT_RECEIPT)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].doc_type, DocumentType.PAYMENT_RECEIPT)

    def test_upload_invalid_mime_type_raises(self):
        svc = ExitDocumentUploadService(self.exit_listing)
        f = fake_file('virus.exe', 'application/x-msdownload', 512)
        with self.assertRaises(ValidationError):
            svc.upload([f])

    def test_upload_too_many_docs_raises(self):
        svc = ExitDocumentUploadService(self.exit_listing)
        # Upload 5 docs first
        for i in range(5):
            f = fake_file(f'doc{i}.pdf', 'application/pdf', 512)
            svc.upload([f])
        # Now 1 more should fail
        with self.assertRaises(ValidationError):
            svc.upload([fake_file('extra.pdf', 'application/pdf', 512)])

    def test_upload_oversized_file_raises(self):
        svc = ExitDocumentUploadService(self.exit_listing)
        large_size = 11 * 1024 * 1024  # 11 MB, exceeds limit
        f = fake_file('big.pdf', 'application/pdf', large_size)
        with self.assertRaises(ValidationError):
            svc.upload([f])


# ─── API Tests ─────────────────────────────────────────────────────────────────

class CreateExitProfileAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seller = make_user(phone='+201111111111', email='seller2@test.com')
        self.other = make_user(phone='+201222222222', email='other@test.com')
        self.listing = make_listing(self.seller)

    def test_unauthenticated_request_is_rejected(self):
        url = f'/api/exit-deals/listings/{self.listing.id}/profile/'
        res = self.client.post(url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_owner_cannot_create_profile(self):
        self.client.force_authenticate(self.other)
        url = f'/api/exit-deals/listings/{self.listing.id}/profile/'
        res = self.client.post(url, {'owner_confirmed_no_markup': True}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_create_exit_profile(self):
        self.client.force_authenticate(self.seller)
        url = f'/api/exit-deals/listings/{self.listing.id}/profile/'
        res = self.client.post(url, {
            'developer_current_price': '1800000',
            'owner_confirmed_no_markup': True,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ExitListing.objects.filter(listing=self.listing).exists())

    def test_cannot_create_duplicate_exit_profile(self):
        make_exit_listing(self.listing)
        self.client.force_authenticate(self.seller)
        url = f'/api/exit-deals/listings/{self.listing.id}/profile/'
        res = self.client.post(url, {'owner_confirmed_no_markup': True}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listing_not_found_returns_404(self):
        import uuid
        self.client.force_authenticate(self.seller)
        url = f'/api/exit-deals/listings/{uuid.uuid4()}/profile/'
        res = self.client.post(url, {'owner_confirmed_no_markup': True}, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class ExitOpportunitiesAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seller = make_user(phone='+201333333333', email='seller3@test.com')

    def test_only_verified_listings_returned(self):
        # Create 2 listings: one verified, one pending
        l1 = make_listing(self.seller, title='Verified Unit')
        l2 = make_listing(self.seller, title='Pending Unit')
        make_exit_listing(l1, verification_status=VerificationStatus.VERIFIED)
        make_exit_listing(l2, verification_status=VerificationStatus.PENDING)

        res = self.client.get('/api/exit-deals/opportunities/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check only verified is returned
        ids = [item['id'] for item in res.data.get('results', res.data)]
        self.assertIn(str(l1.id), ids)
        self.assertNotIn(str(l2.id), ids)

    def test_rejected_listings_not_returned(self):
        l = make_listing(self.seller, title='Rejected Unit')
        make_exit_listing(l, verification_status=VerificationStatus.REJECTED)

        res = self.client.get('/api/exit-deals/opportunities/')
        ids = [item['id'] for item in res.data.get('results', res.data)]
        self.assertNotIn(str(l.id), ids)

    def test_endpoint_is_public(self):
        # No authentication needed
        res = self.client.get('/api/exit-deals/opportunities/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class ExitLeadAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_lead_without_auth(self):
        """Calculator leads must work without login."""
        res = self.client.post('/api/exit-deals/calculator-leads/', {
            'contract_price': '5000000',
            'amount_paid': '1000000',
            'years_paid': '2.0',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ExitLead.objects.exists())

    def test_create_lead_with_phone(self):
        res = self.client.post('/api/exit-deals/calculator-leads/', {
            'phone': '+201000000001',
            'contract_price': '5000000',
            'amount_paid': '1000000',
            'years_paid': '2.5',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        lead = ExitLead.objects.get()
        self.assertEqual(lead.phone, '+201000000001')

    def test_missing_required_fields_returns_400(self):
        res = self.client.post('/api/exit-deals/calculator-leads/', {
            'phone': '+201000000001',
            # missing contract_price, amount_paid, years_paid
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ListingSerializerExitProfileTests(TestCase):
    """Test that exit_profile is injected into the main listing API."""

    def setUp(self):
        self.client = APIClient()
        self.seller = make_user(phone='+201444444444', email='seller4@test.com')
        self.listing = make_listing(self.seller)

    def test_ordinary_listing_has_null_exit_profile(self):
        res = self.client.get(f'/api/listings/{self.listing.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data.get('exit_profile'))

    def test_pending_exit_listing_not_visible(self):
        make_exit_listing(self.listing, verification_status=VerificationStatus.PENDING)
        res = self.client.get(f'/api/listings/{self.listing.id}/')
        self.assertIsNone(res.data.get('exit_profile'))

    def test_verified_exit_listing_is_visible(self):
        make_exit_listing(self.listing, verification_status=VerificationStatus.VERIFIED)
        res = self.client.get(f'/api/listings/{self.listing.id}/')
        self.assertIsNotNone(res.data.get('exit_profile'))
        ep = res.data['exit_profile']
        # Check expected fields are present
        self.assertIn('cash_required_now', ep)
        self.assertIn('remaining_to_developer', ep)
        self.assertIn('market_gain', ep)

    def test_cash_required_now_calculation(self):
        """cash_required = amount_paid + transfer_fee"""
        make_exit_listing(self.listing, verification_status=VerificationStatus.VERIFIED)
        res = self.client.get(f'/api/listings/{self.listing.id}/')
        ep = res.data['exit_profile']
        expected = float(self.listing.amount_paid + self.listing.transfer_fee)
        self.assertAlmostEqual(float(ep['cash_required_now']), expected)

    def test_remaining_to_developer_calculation(self):
        """remaining = original_price - amount_paid"""
        make_exit_listing(self.listing, verification_status=VerificationStatus.VERIFIED)
        res = self.client.get(f'/api/listings/{self.listing.id}/')
        ep = res.data['exit_profile']
        expected = float(self.listing.original_price - self.listing.amount_paid)
        self.assertAlmostEqual(float(ep['remaining_to_developer']), expected)


class IsVerifiedExitFilterTests(TestCase):
    """Test the is_verified_exit query param on the main /api/listings/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.seller = make_user(phone='+201555555555', email='seller5@test.com')
        self.l_verified = make_listing(self.seller, title='Verified Exit')
        self.l_regular = make_listing(self.seller, title='Regular Listing')
        make_exit_listing(self.l_verified, verification_status=VerificationStatus.VERIFIED)

    def test_filter_returns_only_exit_listings(self):
        res = self.client.get('/api/listings/?is_verified_exit=true')
        ids = [item['id'] for item in res.data.get('results', res.data)]
        self.assertIn(str(self.l_verified.id), ids)
        self.assertNotIn(str(self.l_regular.id), ids)

    def test_without_filter_returns_all_listings(self):
        res = self.client.get('/api/listings/')
        ids = [item['id'] for item in res.data.get('results', res.data)]
        self.assertIn(str(self.l_verified.id), ids)
        self.assertIn(str(self.l_regular.id), ids)
