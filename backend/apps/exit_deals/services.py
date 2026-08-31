from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from .models import ExitListing, ExitDocument, DocumentType

_ALLOWED_MIME_TYPES: frozenset[str] = frozenset({
    'image/jpeg',
    'image/png',
    'image/webp',
    'application/pdf',
})

_MAX_DOCS_PER_LISTING: int = 5

def _max_size() -> int:
    return getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)


class ExitDocumentUploadService:
    def __init__(self, exit_listing: ExitListing) -> None:
        self._exit_listing = exit_listing

    def upload(self, files: list[InMemoryUploadedFile], doc_type: str = DocumentType.OTHER) -> list[ExitDocument]:
        self._validate_batch(files)

        created: list[ExitDocument] = []
        for file in files:
            doc = self._persist(file, doc_type)
            created.append(doc)

        return created

    def _validate_batch(self, files: list[InMemoryUploadedFile]) -> None:
        existing_count = self._exit_listing.documents.count()
        if existing_count + len(files) > _MAX_DOCS_PER_LISTING:
            raise ValidationError(
                f"An exit listing may have at most {_MAX_DOCS_PER_LISTING} documents "
                f"(currently has {existing_count})."
            )

        for file in files:
            self._validate_file(file)

    def _validate_file(self, file: InMemoryUploadedFile) -> None:
        content_type = getattr(file, 'content_type', '')
        if content_type not in _ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"'{file.name}' has unsupported type '{content_type}'. "
                f"Allowed types: PDF, JPEG, PNG, WebP."
            )

        if file.size > _max_size():
            max_mb = _max_size() / (1024 * 1024)
            raise ValidationError(
                f"'{file.name}' exceeds the {max_mb:.0f} MB size limit."
            )

    def _persist(self, file: InMemoryUploadedFile, doc_type: str) -> ExitDocument:
        doc = ExitDocument(
            exit_listing=self._exit_listing,
            doc_type=doc_type
        )
        doc.file.save(file.name, file, save=True)
        return doc
