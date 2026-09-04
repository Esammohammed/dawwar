"""
Adds the Ministry of Housing's own press-release feed as a scrape source —
a direct integration with api.mhuc.gov.eg (their own public JSON API,
discovered by inspecting network traffic against mhuc.gov.eg, which is a
client-side-rendered SPA the regular HTML-link scraper can't reach at all).
See gov-scraper/scrapers/mhuc_api.py for the integration itself.

This is the Ministry's own official channel — every item is inherently
housing-related by construction, and it already produced a confirmed direct
hit for "سكن كل المصريين" while verifying this.
"""
from django.db import migrations

SOURCE = {
    'name': 'وزارة الإسكان - بيانات صحفية (API)',
    'url': 'https://mhuc.gov.eg/',
    'kind': 'api',
}


def seed_source(apps, schema_editor):
    ScrapeSource = apps.get_model('govfeed', 'ScrapeSource')
    ScrapeSource.objects.get_or_create(name=SOURCE['name'], defaults=SOURCE)


def unseed_source(apps, schema_editor):
    ScrapeSource = apps.get_model('govfeed', 'ScrapeSource')
    ScrapeSource.objects.filter(name=SOURCE['name']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('govfeed', '0005_seed_nuca_source'),
    ]

    operations = [
        migrations.RunPython(seed_source, unseed_source),
    ]
