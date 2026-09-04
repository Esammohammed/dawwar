"""
Seeds the 4 named government housing programs the gov-scraper microservice
targets, as stable-slug Project rows (type=government). Giving the scraper's
deterministic keyword-matcher a fixed set of slugs to link
Announcement.project against avoids an LLM ever freely minting/duplicating
Project rows with inconsistent naming.

Status/location values below are a best-effort snapshot from research done
when this was planned — these are exactly the kind of details that go stale
fast (a program's status moves from "announced" to "open_for_booking" on the
ministry's own timeline), so they're deliberately editable via Django admin
afterward, not something this migration should try to keep re-asserting.
"""
from django.db import migrations


PROGRAMS = [
    {
        'slug': 'sakan-lel-masreyeen-7',
        'name': 'سكن لكل المصريين 7',
        'description': 'المرحلة السابعة من مبادرة سكن لكل المصريين للإسكان الاجتماعي.',
    },
    {
        'slug': 'sakan-lel-masreyeen-8',
        'name': 'سكن لكل المصريين 8',
        'description': 'المرحلة الثامنة من مبادرة سكن لكل المصريين للإسكان الاجتماعي.',
    },
    {
        'slug': 'beitak-fi-masr',
        'name': 'بيتك في مصر',
        'description': 'مبادرة وزارة الإسكان لتمكين المصريين بالخارج من التملك في مصر.',
    },
    {
        'slug': 'masr-el-aqareya-platform',
        'name': 'منصة مصر العقارية',
        'description': 'المنصة الرسمية الحكومية لطرح الوحدات السكنية والتسويق العقاري.',
    },
]


def seed_programs(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    for program in PROGRAMS:
        Project.objects.get_or_create(
            slug=program['slug'],
            defaults={
                'type': 'government',
                'name': program['name'],
                'description': program['description'],
                'status': 'announced',
                # Project.governorate/city aren't nullable, but these
                # programs run nationwide across many governorates — there's
                # no single correct value. Using explicit placeholders
                # rather than an arbitrary single governorate, flagged here
                # so it's not mistaken for real per-unit location data.
                'governorate': 'جمهورية مصر العربية',
                'city': 'مواقع متعددة',
                'details': {},
            },
        )


def unseed_programs(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    Project.objects.filter(slug__in=[p['slug'] for p in PROGRAMS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_programs, unseed_programs),
    ]
