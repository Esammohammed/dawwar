"""
Listing media upload service.

Single-responsibility class that owns all image upload logic:
validation, file storage, sort ordering, and primary-image flagging.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from .models import Listing, Media, MediaKind

# ─── Constants ───────────────────────────────────────────────────────────────

_ALLOWED_MIME_TYPES: frozenset[str] = frozenset({
    'image/jpeg',
    'image/png',
    'image/webp',
})

_MAX_IMAGES_PER_LISTING: int = 10

# Resolved at call-time so tests can override settings.MAX_UPLOAD_SIZE easily.
def _max_size() -> int:
    return getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)  # 10 MB default


# ─── Service ─────────────────────────────────────────────────────────────────

class MediaUploadService:
    """Validates and persists uploaded image files for a listing.

    Usage::

        service = MediaUploadService(listing)
        media_objects = service.upload(request.FILES.getlist('images'))
    """

    def __init__(self, listing: Listing) -> None:
        self._listing = listing

    # ── Public API ────────────────────────────────────────────────────────────

    def upload(self, files: list[InMemoryUploadedFile]) -> list[Media]:
        """Validate *files*, persist them, and return the created Media rows.

        Args:
            files: A list of uploaded file objects from ``request.FILES``.

        Returns:
            The newly created :class:`Media` instances in sort-order.

        Raises:
            :class:`django.core.exceptions.ValidationError` if any file
            fails validation.
        """
        self._validate_batch(files)

        # Determine the starting sort_order so we append after existing media.
        next_order = self._next_sort_order()
        has_primary = self._listing.media.filter(is_primary=True).exists()

        created: list[Media] = []
        for index, file in enumerate(files):
            is_primary = not has_primary and index == 0
            media = self._persist(file, sort_order=next_order + index, is_primary=is_primary)
            created.append(media)

        return created

    # ── Private helpers ───────────────────────────────────────────────────────

    def _validate_batch(self, files: list[InMemoryUploadedFile]) -> None:
        """Run all validations on the incoming file batch."""
        existing_count = self._listing.media.count()
        if existing_count + len(files) > _MAX_IMAGES_PER_LISTING:
            raise ValidationError(
                f"A listing may have at most {_MAX_IMAGES_PER_LISTING} images "
                f"(currently has {existing_count})."
            )

        for file in files:
            self._validate_file(file)

    def _validate_file(self, file: InMemoryUploadedFile) -> None:
        """Validate a single uploaded file."""
        content_type = getattr(file, 'content_type', '')
        if content_type not in _ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"'{file.name}' has unsupported type '{content_type}'. "
                f"Allowed types: JPEG, PNG, WebP."
            )

        if file.size > _max_size():
            max_mb = _max_size() / (1024 * 1024)
            raise ValidationError(
                f"'{file.name}' exceeds the {max_mb:.0f} MB size limit."
            )

    def _next_sort_order(self) -> int:
        """Return the next available sort_order for this listing's media."""
        last = self._listing.media.order_by('-sort_order').first()
        return (last.sort_order + 1) if last else 0

    def _persist(
        self,
        file: InMemoryUploadedFile,
        *,
        sort_order: int,
        is_primary: bool,
    ) -> Media:
        """Create and return a single Media row with the uploaded file."""
        media = Media(
            listing=self._listing,
            kind=MediaKind.PHOTO,
            sort_order=sort_order,
            is_primary=is_primary,
        )
        # Assign via ImageField so Django handles the file path and storage backend.
        media.file.save(file.name, file, save=True)
        return media
