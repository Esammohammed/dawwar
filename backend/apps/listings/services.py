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

_IMAGE_MIME_TYPES: frozenset[str] = frozenset({
    'image/jpeg',
    'image/png',
    'image/webp',
})

# Contract/payment-receipt uploads are frequently PDF scans, so those two
# kinds additionally accept application/pdf; photo/video/floorplan stay
# images-only.
_DOCUMENT_KINDS: frozenset[str] = frozenset({MediaKind.CONTRACT, MediaKind.PAYMENT_RECEIPT})
_NON_DOCUMENT_KINDS: frozenset[str] = frozenset({MediaKind.PHOTO, MediaKind.VIDEO, MediaKind.FLOORPLAN})
_DOCUMENT_MIME_TYPES: frozenset[str] = _IMAGE_MIME_TYPES | frozenset({'application/pdf'})

_MAX_IMAGES_PER_LISTING: int = 10
_MAX_DOCUMENTS_PER_LISTING: int = 5

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

    def upload(
        self,
        files: list[InMemoryUploadedFile],
        kind: str = MediaKind.PHOTO,
    ) -> list[Media]:
        """Validate *files*, persist them, and return the created Media rows.

        Args:
            files: A list of uploaded file objects from ``request.FILES``.
            kind: The :class:`MediaKind` all files in this batch share —
                ``photo``/``video``/``floorplan`` are images-only;
                ``contract``/``payment_receipt`` also accept PDF, and count
                against a separate per-listing cap.

        Returns:
            The newly created :class:`Media` instances in sort-order.

        Raises:
            :class:`django.core.exceptions.ValidationError` if any file
            fails validation.
        """
        self._validate_batch(files, kind)

        # Determine the starting sort_order so we append after existing media.
        next_order = self._next_sort_order()
        is_document = kind in _DOCUMENT_KINDS
        has_primary = self._listing.media.filter(is_primary=True).exists()

        created: list[Media] = []
        for index, file in enumerate(files):
            # Documents are never flagged as the listing's primary/cover image.
            is_primary = not is_document and not has_primary and index == 0
            media = self._persist(file, kind=kind, sort_order=next_order + index, is_primary=is_primary)
            created.append(media)

        return created

    # ── Private helpers ───────────────────────────────────────────────────────

    def _validate_batch(self, files: list[InMemoryUploadedFile], kind: str) -> None:
        """Run all validations on the incoming file batch."""
        is_document = kind in _DOCUMENT_KINDS
        cap = _MAX_DOCUMENTS_PER_LISTING if is_document else _MAX_IMAGES_PER_LISTING
        existing_count = self._listing.media.filter(
            kind__in=(_DOCUMENT_KINDS if is_document else _NON_DOCUMENT_KINDS)
        ).count()
        if existing_count + len(files) > cap:
            noun = 'documents' if is_document else 'images'
            raise ValidationError(
                f"A listing may have at most {cap} {noun} "
                f"(currently has {existing_count})."
            )

        for file in files:
            self._validate_file(file, kind)

    def _validate_file(self, file: InMemoryUploadedFile, kind: str) -> None:
        """Validate a single uploaded file."""
        allowed = _DOCUMENT_MIME_TYPES if kind in _DOCUMENT_KINDS else _IMAGE_MIME_TYPES
        content_type = getattr(file, 'content_type', '')
        if content_type not in allowed:
            allowed_label = 'PDF, JPEG, PNG, WebP' if kind in _DOCUMENT_KINDS else 'JPEG, PNG, WebP'
            raise ValidationError(
                f"'{file.name}' has unsupported type '{content_type}'. "
                f"Allowed types: {allowed_label}."
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
        kind: str,
        sort_order: int,
        is_primary: bool,
    ) -> Media:
        """Create and return a single Media row with the uploaded file."""
        media = Media(
            listing=self._listing,
            kind=kind,
            sort_order=sort_order,
            is_primary=is_primary,
        )
        # Assign via FileField so Django handles the file path and storage backend.
        media.file.save(file.name, file, save=True)
        return media
