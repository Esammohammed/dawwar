from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.db.models import Count
from django.db.models.functions import Lower


def fix_legacy_passwords_and_emails(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    # Users created via get_or_create bypassed the manager and have password=''.
    # Django considers '' a usable password, so replace it with an unusable hash
    # to make has_usable_password() trustworthy.
    for user in User.objects.filter(password=''):
        user.password = make_password(None)
        user.save(update_fields=['password'])

    # Normalize emails to lowercase.
    for user in User.objects.exclude(email=None).exclude(email=''):
        lowered = user.email.lower()
        if lowered != user.email:
            user.email = lowered
            user.save(update_fields=['email'])

    # Treat empty-string emails as NULL so the unique constraint ignores them.
    User.objects.filter(email='').update(email=None)

    # Dedupe: keep the oldest account per email, null out the rest.
    dupes = (
        User.objects.exclude(email=None)
        .annotate(email_lower=Lower('email'))
        .values('email_lower')
        .annotate(n=Count('id'))
        .filter(n__gt=1)
    )
    for row in dupes:
        losers = (
            User.objects.filter(email=row['email_lower'])
            .order_by('created_at')[1:]
            .values_list('id', flat=True)
        )
        loser_ids = list(losers)
        if loser_ids:
            print(f"[accounts.0004] Nulling duplicate email {row['email_lower']!r} on users: {loser_ids}")
            User.objects.filter(id__in=loser_ids).update(email=None)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_profile_fields_otpcode_attempts'),
    ]

    operations = [
        migrations.RunPython(fix_legacy_passwords_and_emails, migrations.RunPython.noop),
    ]
