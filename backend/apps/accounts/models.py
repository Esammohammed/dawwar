import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserRole(models.TextChoices):
    BUYER = 'buyer', 'Buyer'
    SELLER = 'seller', 'Seller'
    STAFF = 'staff', 'Staff'
    ADMIN = 'admin', 'Admin'

class Governorate(models.TextChoices):
    # Values must stay in sync with frontend/src/constants/governorates.js
    CAIRO = 'cairo', 'Cairo'
    GIZA = 'giza', 'Giza'
    ALEXANDRIA = 'alexandria', 'Alexandria'
    QALYUBIA = 'qalyubia', 'Qalyubia'
    SHARQIA = 'sharqia', 'Sharqia'
    DAKAHLIA = 'dakahlia', 'Dakahlia'
    BEHEIRA = 'beheira', 'Beheira'
    GHARBIA = 'gharbia', 'Gharbia'
    MONUFIA = 'monufia', 'Monufia'
    KAFR_EL_SHEIKH = 'kafr_el_sheikh', 'Kafr El Sheikh'
    DAMIETTA = 'damietta', 'Damietta'
    PORT_SAID = 'port_said', 'Port Said'
    ISMAILIA = 'ismailia', 'Ismailia'
    SUEZ = 'suez', 'Suez'
    NORTH_SINAI = 'north_sinai', 'North Sinai'
    SOUTH_SINAI = 'south_sinai', 'South Sinai'
    RED_SEA = 'red_sea', 'Red Sea'
    MATROUH = 'matrouh', 'Matrouh'
    NEW_VALLEY = 'new_valley', 'New Valley'
    FAYOUM = 'fayoum', 'Fayoum'
    BENI_SUEF = 'beni_suef', 'Beni Suef'
    MINYA = 'minya', 'Minya'
    ASSIUT = 'assiut', 'Assiut'
    SOHAG = 'sohag', 'Sohag'
    QENA = 'qena', 'Qena'
    LUXOR = 'luxor', 'Luxor'
    ASWAN = 'aswan', 'Aswan'

class UserManager(BaseUserManager):
    def create_user(self, phone, full_name='', password=None, **extra_fields):
        if not phone:
            raise ValueError('The Phone field must be set')
        user = self.model(phone=phone, full_name=full_name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, full_name='Admin User', password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('is_phone_verified', True)
        return self.create_user(phone=phone, full_name=full_name, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, unique=True, db_index=True)
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True, default='')
    governorate = models.CharField(max_length=32, choices=Governorate.choices, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=14, blank=True, default='')
    role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.BUYER)
    is_phone_verified = models.BooleanField(default=False)
    telegram_id = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # Marks the dedicated AI scraper bot account — grants access to scrape_import endpoint.
    is_bot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role'], name='idx_users_role'),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.phone})"

class OTPCode(models.Model):
    class DeliveryMethod(models.TextChoices):
        PHONE = 'phone', 'Phone'
        EMAIL = 'email', 'Email'

    class Purpose(models.TextChoices):
        REGISTER = 'register', 'Register'
        LOGIN = 'login', 'Login'
        RESET = 'reset', 'Password Reset'

    MAX_ATTEMPTS = 5

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    delivery_method = models.CharField(max_length=10, choices=DeliveryMethod.choices, default=DeliveryMethod.PHONE)
    code_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.LOGIN)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_codes'
        indexes = [
            models.Index(fields=['phone', 'expires_at'], name='idx_otp_phone'),
            models.Index(fields=['email', 'expires_at'], name='idx_otp_email'),
        ]

    def __str__(self):
        target = self.email if self.delivery_method == self.DeliveryMethod.EMAIL else self.phone
        return f"OTP for {target} via {self.delivery_method} ({self.purpose})"

