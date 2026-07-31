import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.developers.models import Developer
from apps.projects.models import Project, ProjectType, ProjectStatus
from apps.govfeed.models import ScrapeSource, Announcement, AnnouncementStatus, SourceKind
from apps.listings.models import Listing, Media, ListingType, FinishingType, ListingStatus, MediaKind

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds initial sample data for the Dawwar real estate platform'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding Dawwar database...'))

        # 1. Users
        admin_user, _ = User.objects.get_or_create(
            phone='01000000000',
            defaults={
                'full_name': 'مدير النظام',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_phone_verified': True
            }
        )
        if not admin_user.password:
            admin_user.set_password('admin123')
            admin_user.save()

        seller_user, _ = User.objects.get_or_create(
            phone='01111111111',
            defaults={
                'full_name': 'أحمد محمود',
                'role': 'seller',
                'is_phone_verified': True
            }
        )

        buyer_user, _ = User.objects.get_or_create(
            phone='01222222222',
            defaults={
                'full_name': 'سارة محمد',
                'role': 'buyer',
                'is_phone_verified': True
            }
        )

        # 2. Developers
        tmg, _ = Developer.objects.get_or_create(
            name='مجموعة طلعت مصطفى (TMG)',
            defaults={
                'contact_phone': '19600',
                'contact_email': 'info@tmg.com.eg',
                'verified': True,
                'commercial_register_no': '10293847',
                'notes': 'من كبرى شركات التطوير العقاري في مصر'
            }
        )

        palm_hills, _ = Developer.objects.get_or_create(
            name='بالم هيلز للتعمير',
            defaults={
                'contact_phone': '19011',
                'contact_email': 'sales@palmhills.com',
                'verified': True,
                'commercial_register_no': '56473829'
            }
        )

        # 3. Projects
        gov_project, _ = Project.objects.get_or_create(
            slug='sakan-misr-october',
            defaults={
                'name': 'مشروع سكن مصر - أكتوبر الجديدة',
                'type': ProjectType.GOVERNMENT,
                'governorate': 'الجيزة',
                'city': '6 أكتوبر',
                'district': 'أكتوبر الجديدة',
                'description': 'طرح حكومي مميز لوحدات سكنية كاملة التشطيب بمساحات 115 م2',
                'status': ProjectStatus.OPEN_FOR_BOOKING,
                'details': {'delivery_year': 2026, 'min_downpayment': 50000, 'installments_years': 7}
            }
        )

        dev_project, _ = Project.objects.get_or_create(
            slug='badya-palm-hills',
            defaults={
                'name': 'كمبوند بادية - بالم هيلز',
                'type': ProjectType.DEVELOPER,
                'developer': palm_hills,
                'governorate': 'الجيزة',
                'city': '6 أكتوبر',
                'district': 'توسعات أكتوبر',
                'description': 'مدينة متكاملة الذكاء الاصطناعي والاستدامة غرب القاهرة',
                'status': ProjectStatus.UNDER_CONSTRUCTION,
                'details': {'delivery_year': 2027, 'amenities': ['نادي رياضي', 'بحيرات صناعية', 'مدارس دولية']}
            }
        )

        # 4. Listings
        listing_1, created_1 = Listing.objects.get_or_create(
            title='شقة للبيع إعادة بيع (إعادة تنازل) في سكن مصر أكتوبر',
            defaults={
                'type': ListingType.RESALE,
                'project': gov_project,
                'seller': seller_user,
                'area_sqm': Decimal('115.00'),
                'bedrooms': 3,
                'bathrooms': 2,
                'floor': 3,
                'finishing': FinishingType.FULLY,
                'governorate': 'الجيزة',
                'city': '6 أكتوبر',
                'district': 'أكتوبر الجديدة',
                'asking_price': Decimal('1250000.00'),
                'original_price': Decimal('950000.00'),
                'amount_paid': Decimal('350000.00'),
                'transfer_fee': Decimal('25000.00'),
                'installment_plan': {
                    'remaining_amount': 600000,
                    'quarterly_installment': 25000,
                    'years_remaining': 6
                },
                'status': ListingStatus.ACTIVE,
                'published_at': timezone.now()
            }
        )
        if created_1:
            Media.objects.create(listing=listing_1, file='https://images.unsplash.com/photo-1560448204-e02f11c3d0e2', kind=MediaKind.PHOTO, sort_order=0)

        listing_2, created_2 = Listing.objects.get_or_create(
            title='شقة 180م2 في كمبوند بادية بالم هيلز تسليم قريب',
            defaults={
                'type': ListingType.DEVELOPER_UNIT,
                'project': dev_project,
                'developer': palm_hills,
                'area_sqm': Decimal('180.00'),
                'bedrooms': 3,
                'bathrooms': 3,
                'floor': 2,
                'finishing': FinishingType.LUX,
                'governorate': 'الجيزة',
                'city': '6 أكتوبر',
                'district': 'توسعات أكتوبر',
                'asking_price': Decimal('4800000.00'),
                'negotiable': False,
                'installment_plan': {
                    'down_payment': 480000,
                    'years': 8,
                    'quarterly': 135000
                },
                'status': ListingStatus.ACTIVE,
                'published_at': timezone.now()
            }
        )
        if created_2:
            Media.objects.create(listing=listing_2, file='https://images.unsplash.com/photo-1512917774080-9991f1c4c750', kind=MediaKind.PHOTO, sort_order=0)

        # 5. Govfeed
        source, _ = ScrapeSource.objects.get_or_create(
            name='موقع وزارة الإسكان والمجتمعات العمرانية',
            defaults={
                'url': 'http://www.mhuc.gov.eg',
                'kind': SourceKind.HTML,
                'active': True
            }
        )

        Announcement.objects.get_or_create(
            source_url='http://www.mhuc.gov.eg/news/sakan-misr-2026',
            defaults={
                'source': source,
                'project': gov_project,
                'title': 'فتح باب التقديم لشقق سكن مصر وأكتوبر الجديدة المرحلة السادسة',
                'body': 'تعلن وزارة الإسكان عن كراسة الشروط الخاصة بطرح 5000 وحدة سكنية بمحافظتي الجيزة والقاهرة ابتداء من الشهر القادم.',
                'ai_summary': 'ملخص الذكاء الاصطناعي: طرح حكومي لـ 5000 شقة في سكن مصر بأسعار تبدأ من 950 ألف جنيه مع تسليم خلال سنتين.',
                'status': AnnouncementStatus.PUBLISHED,
                'published_at': timezone.now()
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded Dawwar platform sample data!'))
