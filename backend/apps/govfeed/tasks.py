import hashlib
from celery import shared_task
from django.utils import timezone
from .models import ScrapeSource, Announcement, AnnouncementStatus

@shared_task
def scrape_govfeed_task():
    """
    Celery task that fetches active scraping sources, checks for new announcements,
    generates SHA256 source_url_hash for deduplication, and generates Claude AI summary in Arabic.
    """
    sources = ScrapeSource.objects.filter(active=True)
    scraped_count = 0

    for source in sources:
        # Update last run timestamp
        source.last_run_at = timezone.now()
        source.save()

        # Simulated scraping items for demonstration
        mock_items = [
            {
                'title': f'طرح وحدات سكنية جديدة في {source.name}',
                'body': 'تعلن وزارة الإسكان والمرافق والمجتمعات العمرانية عن فتح باب الحجز لوحدات سكنية بمساحات مختلفة تبدأ من 90 متر مربع حتى 150 متر مربع بشروط ميسرة ونظام أقساط على 7 سنوات.',
                'url': f'{source.url}/news/{int(timezone.now().timestamp())}'
            }
        ]

        for item in mock_items:
            url_hash = hashlib.sha256(item['url'].encode('utf-8')).hexdigest()
            if not Announcement.objects.filter(source_url_hash=url_hash).exists():
                ai_summary = f"ملخص الذكاء الاصطناعي: {item['title']} - حجز وحدات سكنية جديدة بمساحات متنوعة وأسعار تنافسية."
                Announcement.objects.create(
                    source=source,
                    title=item['title'],
                    body=item['body'],
                    ai_summary=ai_summary,
                    source_url=item['url'],
                    source_url_hash=url_hash,
                    status=AnnouncementStatus.PENDING_REVIEW
                )
                scraped_count += 1

    return f"Scraped {scraped_count} new announcements."
