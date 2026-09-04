import hashlib
import re
from rest_framework import serializers
from .models import Announcement, ScrapeSource, AnnouncementStatus
from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer

# The one program family with numbered phases — slugs of this exact shape
# are safe to auto-create on the fly (see validate_project_slug below)
# because both the slug and the resulting Arabic name are mechanically
# derived from the captured number, never free-form AI text.
_SAKAN_PHASE_SLUG_RE = re.compile(r'^sakan-lel-masreyeen-(\d+)$')

class ScrapeSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapeSource
        fields = ['id', 'name', 'url', 'kind', 'active', 'last_run_at']

class AnnouncementSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True)
    project_details = ProjectSerializer(source='project', read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'source', 'source_name', 'project', 'project_details',
            'title', 'body', 'ai_summary', 'requirements', 'suggested_program_name',
            'source_url', 'status', 'published_at', 'scraped_at',
        ]


class AnnouncementScrapeImportSerializer(serializers.ModelSerializer):
    """Used by the gov-scraper microservice's ingestion endpoint.

    Mirrors apps.listings.ScrapedListingCreateSerializer: the scraper sends
    structured JSON already normalized by its own OpenAI step, this
    serializer just validates the shape and resolves `source`/`project` by
    stable identifiers rather than requiring the scraper to know internal
    UUIDs.
    """
    source_name = serializers.CharField(write_only=True)
    project_slug = serializers.SlugField(write_only=True, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'source_name', 'project_slug', 'title', 'body',
            'ai_summary', 'requirements', 'suggested_program_name',
            'source_url', 'published_at',
        ]
        read_only_fields = ['id']

    def validate_source_name(self, value):
        try:
            self._source = ScrapeSource.objects.get(name=value)
        except ScrapeSource.DoesNotExist:
            raise serializers.ValidationError(
                f"Unknown source '{value}' — create it in Django admin first (ScrapeSource)."
            )
        return value

    def validate_project_slug(self, value):
        if not value:
            self._project = None
            return value
        try:
            self._project = Project.objects.get(slug=value, type='government')
            return value
        except Project.DoesNotExist:
            pass

        # Auto-create only for this one safe, fully-deterministic family —
        # a new "سكن لكل المصريين N" phase shouldn't need a manual
        # migration/admin step every time the ministry announces one, and
        # both the slug and name here are mechanically derived from the
        # captured number, not free-form AI text. Any other unrecognized
        # slug stays a hard rejection — genuinely new/differently-named
        # programs go through the semantic-match + AI-suggestion path
        # instead (gov-scraper/matcher.py), surfaced via
        # Announcement.suggested_program_name for a human to confirm, never
        # auto-linked.
        phase_match = _SAKAN_PHASE_SLUG_RE.match(value)
        if not phase_match:
            raise serializers.ValidationError(
                f"Unknown government project slug '{value}'."
            )
        phase = phase_match.group(1)
        self._project, _ = Project.objects.get_or_create(
            slug=value,
            defaults={
                'type': 'government',
                'name': f'سكن لكل المصريين {phase}',
                'description': f'المرحلة {phase} من مبادرة سكن لكل المصريين للإسكان الاجتماعي.',
                'status': 'announced',
                'governorate': 'جمهورية مصر العربية',
                'city': 'مواقع متعددة',
                'details': {},
            },
        )
        return value

    def validate_source_url(self, value):
        # The model computes this same hash and enforces uniqueness at the
        # DB level, but checking here turns "already scraped this" into a
        # clean 400 the scraper can treat as an expected dedup signal,
        # instead of an unhandled IntegrityError surfacing as a 500 — the
        # scraper's own local SeenURLStore should catch most repeats, but a
        # cold cache or a second scraper instance shouldn't be able to crash
        # this endpoint.
        url_hash = hashlib.sha256(value.strip().encode('utf-8')).hexdigest()
        if Announcement.objects.filter(source_url_hash=url_hash).exists():
            raise serializers.ValidationError('An announcement with this source_url already exists.')
        return value

    def create(self, validated_data):
        validated_data.pop('source_name', None)
        validated_data.pop('project_slug', None)
        return Announcement.objects.create(
            source=self._source,
            project=getattr(self, '_project', None),
            status=AnnouncementStatus.PENDING_REVIEW,
            **validated_data,
        )
