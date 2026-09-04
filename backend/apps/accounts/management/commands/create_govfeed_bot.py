from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates the GovFeed Scraper Bot user and generates a JWT token for gov-scraper/.env'

    def handle(self, *args, **kwargs):
        # Distinct from the listings-scraper bot (+201000000000, created by
        # create_ai_user) purely so admin/audit logs can tell which
        # automation created which content — same IsScraperBot gate covers
        # any user with is_bot=True, this doesn't need special permissions.
        phone = '+201000000001'
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                'full_name': 'Dawwar GovFeed Bot',
                'is_bot': True,
                'is_phone_verified': True,
            }
        )

        if not created and not user.is_bot:
            user.is_bot = True
            user.save()

        if created:
            user.set_unusable_password()
            user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created GovFeed Bot user.'))
        else:
            self.stdout.write('GovFeed Bot user already exists.')

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        self.stdout.write(self.style.SUCCESS('\n--- JWT Token for gov-scraper/.env ---'))
        self.stdout.write(access_token)
        self.stdout.write(self.style.SUCCESS('---------------------------------------\n'))
