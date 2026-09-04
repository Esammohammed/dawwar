"""
Seeds two more named government programs, found by real evidence rather
than guessed: after the gov-scraper's Layer 3 (AI-suggested unmatched
program name) ran against ~300 real Ministry of Housing press releases,
"حياة كريمة" came up 32 times and "بيت الوطن" 7 times as specific programs
the matcher had no seeded Project for — by far the strongest recurring
signals besides bare "سكن لكل المصريين" mentions with no phase number
(which correctly stay in the general catch-all, since guessing a phase
would be worse than not matching).

Neither has numbered phases (unlike سكن لكل المصريين), so both are literal-
name matches in gov-scraper/matcher.py, the same pattern already used for
بيتك في مصر / منصة مصر العقارية.
"""
from django.db import migrations

PROGRAMS = [
    {
        'slug': 'hayah-karima',
        'name': 'حياة كريمة',
        'description': 'المبادرة الرئاسية لتنمية الريف المصري وتحسين جودة الحياة بالقرى الأكثر احتياجاً.',
    },
    {
        'slug': 'beit-el-watan',
        'name': 'بيت الوطن',
        'description': 'مشروع لتمكين المصريين العاملين بالخارج من امتلاك أراضٍ ووحدات سكنية في المدن الجديدة.',
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
        ('projects', '0002_seed_government_programs'),
    ]

    operations = [
        migrations.RunPython(seed_programs, unseed_programs),
    ]
