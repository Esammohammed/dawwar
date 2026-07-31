from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_custom_user_creation(self):
        user = User.objects.create_user(phone='01011112222', full_name='مستخدم تجريبي')
        self.assertEqual(user.phone, '01011112222')
        self.assertFalse(user.is_staff)

    def test_otp_request_and_verify(self):
        # 1. Request OTP
        req_res = self.client.post('/api/auth/otp/request/', {'phone': '01099998888'}, format='json')
        self.assertEqual(req_res.status_code, 200)

        # 2. Verify OTP
        ver_res = self.client.post('/api/auth/otp/verify/', {
            'phone': '01099998888',
            'code': '123456',
            'full_name': 'مستخدم متأكد'
        }, format='json')
        self.assertEqual(ver_res.status_code, 200)
        self.assertIn('access', ver_res.data)
        self.assertTrue(User.objects.filter(phone='01099998888').exists())
