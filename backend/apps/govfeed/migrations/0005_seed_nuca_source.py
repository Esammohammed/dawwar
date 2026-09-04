"""
Adds NUCA (هيئة المجتمعات العمرانية الجديدة) as a scrape source — the
government body that actually runs land-plot tenders ("طروحات الأراضي":
بيت الوطن، أراضي المدن الجديدة), added on request for deeper coverage of
that specific content.

NOT reachable/verified from the dev environment this was built in —
`services.nuca.gov.eg` refused the connection at the network level (not an
HTTP error, a connection failure), which could be geo-blocking, infra
flakiness, or something else entirely. Confirm it actually resolves and
scrapes from wherever gov-scraper is deployed before relying on it. The
corresponding link-pattern regex in gov-scraper/scrapers/sources_config.py
is a best-effort guess built from search-result URL shapes
(NewsItemViewer.aspx?NID=...), not verified against live markup.
"""
from django.db import migrations

SOURCE = {
    'name': 'هيئة المجتمعات العمرانية الجديدة',
    'url': 'https://services.nuca.gov.eg/ar/NewsList.aspx',
    'kind': 'html',
}


def seed_source(apps, schema_editor):
    ScrapeSource = apps.get_model('govfeed', 'ScrapeSource')
    ScrapeSource.objects.get_or_create(name=SOURCE['name'], defaults=SOURCE)


def unseed_source(apps, schema_editor):
    ScrapeSource = apps.get_model('govfeed', 'ScrapeSource')
    ScrapeSource.objects.filter(name=SOURCE['name']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('govfeed', '0004_announcement_suggested_program_name'),
    ]

    operations = [
        migrations.RunPython(seed_source, unseed_source),
    ]
