from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates the AI Scraper Bot user and generates a JWT token'

    def handle(self, *args, **kwargs):
        phone = '+201000000000' # Dummy bot phone
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                'full_name': 'Dawwar AI Agent',
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
            self.stdout.write(self.style.SUCCESS('Successfully created AI Bot user.'))
        else:
            self.stdout.write('AI Bot user already exists.')

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        self.stdout.write(self.style.SUCCESS('\n--- JWT Token for Scraper .env ---'))
        self.stdout.write(access_token)
        self.stdout.write(self.style.SUCCESS('----------------------------------\n'))
