"""Text normalization and sectioning helpers."""
from __future__ import annotations

from .. import schemas


class NormalizationService:
    """Clean extracted text and produce structured sections."""

    def normalizeText(self, ingest_result: schemas.IngestResult) -> schemas.SegmentedDocument:
        """Apply whitespace fixes, header removal, and consistent casing."""
        # TODO: rely on utils.text_cleaning to implement actual logic.
        raise NotImplementedError

    def segmentSections(self, normalized_document: schemas.SegmentedDocument) -> schemas.SegmentedDocument:
        """Split normalized text into sections referenced by downstream steps."""
        # TODO: detect headings (Artículo, Considerando, etc.) and store boundaries.
        raise NotImplementedError
