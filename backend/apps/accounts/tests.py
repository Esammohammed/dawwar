import re
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Governorate, OTPCode, User


class SyncThread:
    """Stand-in for threading.Thread that runs the target synchronously."""

    def __init__(self, target=None, args=(), kwargs=None, daemon=None):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}

    def start(self):
        self._target(*self._args, **self._kwargs)


def sync_email(test_func):
    return patch('apps.accounts.views.threading.Thread', SyncThread)(test_func)


class AuthTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()  # reset login throttle between tests

    def latest_code(self):
        body = mail.outbox[-1].body
        return re.search(r'\b(\d{6})\b', body).group(1)

    def register_user(self, phone='01012345678', email='user@example.com',
                      full_name='Test User', password='StrongPass123!'):
        res = self.client.post('/api/auth/register/request-otp/', {'phone': phone, 'email': email})
        self.assertEqual(res.status_code, 200, res.data)
        res = self.client.post('/api/auth/register/verify/', {
            'phone': phone, 'email': email, 'code': self.latest_code(),
            'full_name': full_name, 'password': password,
        })
        self.assertEqual(res.status_code, 201, res.data)
        return res


class RegistrationTests(AuthTestBase):
    @sync_email
    def test_register_happy_path(self):
        res = self.register_user()
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        user = User.objects.get(phone='01012345678')
        self.assertTrue(user.check_password('StrongPass123!'))
        self.assertTrue(user.is_phone_verified)
        self.assertEqual(user.email, 'user@example.com')
        self.assertTrue(res.data['user']['has_password'])

    @sync_email
    def test_otp_code_not_in_subject(self):
        self.client.post('/api/auth/register/request-otp/', {'phone': '01012345678', 'email': 'user@example.com'})
        code = self.latest_code()
        self.assertNotIn(code, mail.outbox[-1].subject)

    def test_register_existing_phone_rejected(self):
        User.objects.create_user(phone='01012345678', full_name='Existing')
        res = self.client.post('/api/auth/register/request-otp/', {'phone': '01012345678', 'email': 'new@example.com'})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'phone_exists')

    def test_register_existing_email_rejected(self):
        User.objects.create_user(phone='01099999999', full_name='Existing', email='taken@example.com')
        res = self.client.post('/api/auth/register/request-otp/', {'phone': '01012345678', 'email': 'Taken@Example.com'})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'email_exists')

    @sync_email
    def test_register_wrong_code_rejected(self):
        self.client.post('/api/auth/register/request-otp/', {'phone': '01012345678', 'email': 'user@example.com'})
        real_code = self.latest_code()
        wrong = '000000' if real_code != '000000' else '111111'
        res = self.client.post('/api/auth/register/verify/', {
            'phone': '01012345678', 'email': 'user@example.com', 'code': wrong,
            'full_name': 'Test User', 'password': 'StrongPass123!',
        })
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'invalid_code')

    @sync_email
    def test_backdoor_code_123456_rejected(self):
        self.client.post('/api/auth/register/request-otp/', {'phone': '01012345678', 'email': 'user@example.com'})
        if self.latest_code() == '123456':
            self.skipTest('Generated code happened to be 123456')
        res = self.client.post('/api/auth/register/verify/', {
            'phone': '01012345678', 'email': 'user@example.com', 'code': '123456',
            'full_name': 'Test User', 'password': 'StrongPass123!',
        })
        self.assertEqual(res.status_code, 400)

    @sync_email
    def test_register_weak_password_rejected(self):
        self.client.post('/api/auth/register/request-otp/', {'phone': '01012345678', 'email': 'user@example.com'})
        res = self.client.post('/api/auth/register/verify/', {
            'phone': '01012345678', 'email': 'user@example.com', 'code': self.latest_code(),
            'full_name': 'Test User', 'password': '123',
        })
        self.assertEqual(res.status_code, 400)

    def test_register_invalid_phone_rejected(self):
        res = self.client.post('/api/auth/register/request-otp/', {'phone': '0123', 'email': 'user@example.com'})
        self.assertEqual(res.status_code, 400)

    @sync_email
    def test_otp_rate_limit(self):
        for _ in range(5):
            res = self.client.post('/api/auth/register/request-otp/', {'phone': '01012345678', 'email': 'user@example.com'})
            self.assertEqual(res.status_code, 200)
        res = self.client.post('/api/auth/register/request-otp/', {'phone': '01012345678', 'email': 'user@example.com'})
        self.assertEqual(res.status_code, 429)
        self.assertEqual(res.data['code'], 'too_many_requests')


class LoginTests(AuthTestBase):
    @sync_email
    def setUp(self):
        super().setUp()
        self.register_user()
        mail.outbox = []

    def test_login_with_phone(self):
        res = self.client.post('/api/auth/login/', {'identifier': '01012345678', 'password': 'StrongPass123!'})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIn('access', res.data)

    def test_login_with_email_case_insensitive(self):
        res = self.client.post('/api/auth/login/', {'identifier': 'User@Example.COM', 'password': 'StrongPass123!'})
        self.assertEqual(res.status_code, 200, res.data)

    def test_login_wrong_password(self):
        res = self.client.post('/api/auth/login/', {'identifier': '01012345678', 'password': 'wrong'})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data['code'], 'invalid_credentials')

    def test_login_unknown_identifier(self):
        res = self.client.post('/api/auth/login/', {'identifier': '01000000000', 'password': 'whatever'})
        self.assertEqual(res.status_code, 401)

    def test_login_legacy_user_without_password(self):
        User.objects.create_user(phone='01055555555', full_name='Legacy', email='legacy@example.com')
        res = self.client.post('/api/auth/login/', {'identifier': '01055555555', 'password': 'anything'})
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data['code'], 'password_not_set')

    def test_token_refresh(self):
        res = self.client.post('/api/auth/login/', {'identifier': '01012345678', 'password': 'StrongPass123!'})
        refresh = res.data['refresh']
        res = self.client.post('/api/auth/token/refresh/', {'refresh': refresh})
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)


class OTPLoginTests(AuthTestBase):
    @sync_email
    def setUp(self):
        super().setUp()
        self.register_user()
        mail.outbox = []

    @sync_email
    def test_otp_login_existing_user(self):
        res = self.client.post('/api/auth/login/otp/request/', {'email': 'user@example.com'})
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/api/auth/login/otp/verify/', {'email': 'user@example.com', 'code': self.latest_code()})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIn('access', res.data)

    def test_otp_login_unknown_email(self):
        res = self.client.post('/api/auth/login/otp/request/', {'email': 'nobody@example.com'})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'email_not_found')

    @sync_email
    def test_otp_expired_code_rejected(self):
        self.client.post('/api/auth/login/otp/request/', {'email': 'user@example.com'})
        code = self.latest_code()
        OTPCode.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        res = self.client.post('/api/auth/login/otp/verify/', {'email': 'user@example.com', 'code': code})
        self.assertEqual(res.status_code, 400)

    @sync_email
    def test_otp_attempt_lockout(self):
        self.client.post('/api/auth/login/otp/request/', {'email': 'user@example.com'})
        code = self.latest_code()
        wrong = '000000' if code != '000000' else '111111'
        for _ in range(5):
            self.client.post('/api/auth/login/otp/verify/', {'email': 'user@example.com', 'code': wrong})
        # correct code no longer accepted after 5 failed attempts
        res = self.client.post('/api/auth/login/otp/verify/', {'email': 'user@example.com', 'code': code})
        self.assertEqual(res.status_code, 400)

    @sync_email
    def test_otp_code_not_reusable(self):
        self.client.post('/api/auth/login/otp/request/', {'email': 'user@example.com'})
        code = self.latest_code()
        res = self.client.post('/api/auth/login/otp/verify/', {'email': 'user@example.com', 'code': code})
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/api/auth/login/otp/verify/', {'email': 'user@example.com', 'code': code})
        self.assertEqual(res.status_code, 400)


class PasswordResetTests(AuthTestBase):
    @sync_email
    def setUp(self):
        super().setUp()
        self.register_user()
        mail.outbox = []

    @sync_email
    def test_reset_flow(self):
        res = self.client.post('/api/auth/password/reset/request/', {'email': 'user@example.com'})
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/api/auth/password/reset/confirm/', {
            'email': 'user@example.com', 'code': self.latest_code(), 'new_password': 'NewStrongPass456!',
        })
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIn('access', res.data)
        res = self.client.post('/api/auth/login/', {'identifier': '01012345678', 'password': 'NewStrongPass456!'})
        self.assertEqual(res.status_code, 200)

    @sync_email
    def test_reset_rejects_login_purpose_code(self):
        self.client.post('/api/auth/login/otp/request/', {'email': 'user@example.com'})
        code = self.latest_code()
        res = self.client.post('/api/auth/password/reset/confirm/', {
            'email': 'user@example.com', 'code': code, 'new_password': 'NewStrongPass456!',
        })
        self.assertEqual(res.status_code, 400)


class PasswordChangeTests(AuthTestBase):
    @sync_email
    def setUp(self):
        super().setUp()
        res = self.register_user()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_change_with_correct_current(self):
        res = self.client.post('/api/auth/password/change/', {
            'current_password': 'StrongPass123!', 'new_password': 'NewStrongPass456!',
        })
        self.assertEqual(res.status_code, 200, res.data)
        self.assertTrue(User.objects.get(phone='01012345678').check_password('NewStrongPass456!'))

    def test_change_with_wrong_current(self):
        res = self.client.post('/api/auth/password/change/', {
            'current_password': 'nope', 'new_password': 'NewStrongPass456!',
        })
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'wrong_password')

    def test_legacy_user_sets_password_without_current(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        user = User.objects.create_user(phone='01055555555', full_name='Legacy', email='legacy@example.com')
        self.assertFalse(bool(user.password) and user.has_usable_password())
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
        res = client.post('/api/auth/password/change/', {'new_password': 'FreshPass789!'})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertTrue(res.data['has_password'])
        user.refresh_from_db()
        self.assertTrue(user.check_password('FreshPass789!'))


class ProfileTests(AuthTestBase):
    @sync_email
    def setUp(self):
        super().setUp()
        res = self.register_user()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_get_profile(self):
        res = self.client.get('/api/me/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['phone'], '01012345678')
        self.assertTrue(res.data['has_password'])

    def test_patch_profile_fields(self):
        res = self.client.patch('/api/me/', {
            'full_name': 'Updated Name',
            'address': '12 Tahrir St.',
            'governorate': 'cairo',
            'city': 'Nasr City',
            'date_of_birth': '1995-06-15',
            'national_id': '29506150101234',
        })
        self.assertEqual(res.status_code, 200, res.data)
        user = User.objects.get(phone='01012345678')
        self.assertEqual(user.address, '12 Tahrir St.')
        self.assertEqual(user.governorate, 'cairo')
        self.assertEqual(str(user.date_of_birth), '1995-06-15')

    def test_patch_phone_and_email_ignored(self):
        self.client.patch('/api/me/', {'phone': '01000000000', 'email': 'hacker@example.com'})
        user = User.objects.get(phone='01012345678')
        self.assertEqual(user.email, 'user@example.com')

    def test_invalid_national_id_rejected(self):
        res = self.client.patch('/api/me/', {'national_id': '1950615010123'})
        self.assertEqual(res.status_code, 400)
        res = self.client.patch('/api/me/', {'national_id': '19506150101234'})
        self.assertEqual(res.status_code, 400)

    def test_invalid_governorate_rejected(self):
        res = self.client.patch('/api/me/', {'governorate': 'atlantis'})
        self.assertEqual(res.status_code, 400)

    def test_future_dob_rejected(self):
        res = self.client.patch('/api/me/', {'date_of_birth': '2999-01-01'})
        self.assertEqual(res.status_code, 400)


class ModelTests(AuthTestBase):
    def test_governorate_choices_count(self):
        self.assertEqual(len(Governorate.choices), 27)

    def test_create_user_without_password_unusable(self):
        user = User.objects.create_user(phone='01011112222', full_name='NoPass')
        self.assertFalse(user.check_password(''))
        self.assertTrue(user.password)  # unusable hash, not empty string

    def test_old_otp_endpoints_removed(self):
        res = self.client.post('/api/auth/otp/request/', {'phone': '01012345678'})
        self.assertEqual(res.status_code, 404)
        res = self.client.post('/api/auth/otp/email/request/', {'phone': '01012345678', 'email': 'a@b.com'})
        self.assertEqual(res.status_code, 404)
