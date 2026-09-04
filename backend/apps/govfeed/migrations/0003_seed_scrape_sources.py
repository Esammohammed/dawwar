"""
Seeds the news/press sources gov-scraper actually targets — chosen because
each has a real, frequently-updated section covering Egyptian government
housing news (not the citizen-facing booking portals like shmff.gov.eg or
beitakfemisr.com, which are transactional application flows, not scrapable
content feeds — see dawwar-govfeed-scraper-plan.md §1).
"""
from django.db import migrations


SOURCES = [
    {'name': 'الهيئة العامة للاستعلامات', 'url': 'https://www.sis.gov.eg', 'kind': 'html'},
    {'name': 'مصراوي - أخبار العقارات', 'url': 'https://www.masrawy.com/news/realestate-news', 'kind': 'html'},
    {'name': 'بروبرتي فايندر - المدونة', 'url': 'https://www.propertyfinder.eg/blog', 'kind': 'html'},
    {'name': 'الدستور', 'url': 'https://www.dostor.org', 'kind': 'html'},
    {'name': 'عقار 24', 'url': 'https://aqaar24.com', 'kind': 'html'},
    {'name': 'البلد نيوز', 'url': 'https://www.elbalad.news', 'kind': 'html'},
]


def seed_sources(apps, schema_editor):
    ScrapeSource = apps.get_model('govfeed', 'ScrapeSource')
    for source in SOURCES:
        ScrapeSource.objects.get_or_create(name=source['name'], defaults=source)


def unseed_sources(apps, schema_editor):
    ScrapeSource = apps.get_model('govfeed', 'ScrapeSource')
    ScrapeSource.objects.filter(name__in=[s['name'] for s in SOURCES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('govfeed', '0002_announcement_requirements'),
    ]

    operations = [
        migrations.RunPython(seed_sources, unseed_sources),
    ]
