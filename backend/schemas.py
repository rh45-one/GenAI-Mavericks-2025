"""Shared DTOs and schema definitions for the backend pipeline."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentInput(BaseModel):
    """Input payload expected by POST /process_document."""

    sourceType: str = Field(..., description="text | pdf | image")
    fileContent: Optional[str] = Field(
        default=None, description="Placeholder for binary payload or base64 buffer."
    )
    plainText: Optional[str] = Field(
        default=None, description="Populated when the citizen pastes text directly."
    )


class LegalGuide(BaseModel):
    """Four-block legal guidance returned to the citizen."""

    meaningForYou: Optional[str] = None
    whatToDoNow: Optional[str] = None
    whatHappensNext: Optional[str] = None
    deadlinesAndRisks: Optional[str] = None


class ProcessedDocument(BaseModel):
    """Container for the evolving document state through the pipeline."""

    rawText: Optional[str] = None  # Raw text extracted from ingestion/OCR.
    sections: Optional[List[str]] = None  # Ordered sections detected by normalization.
    docType: Optional[str] = None  # E.g., RESOLUCION_JURIDICA.
    docSubtype: Optional[str] = None  # E.g., SENTENCIA.
    simplifiedText: Optional[str] = None  # Plain-language summary built later.


class IngestResult(BaseModel):
    """Output of IngestService before normalization occurs."""

    rawText: Optional[str] = None
    metadata: Optional[dict] = None  # Could include detected language, page count, etc.


class SegmentedDocument(BaseModel):
    """Normalized representation used by classification and simplification."""

    normalizedText: Optional[str] = None
    sections: Optional[List[str]] = None


class ClassificationResult(BaseModel):
    """LLM-driven classification describing document type and confidence."""

    docType: Optional[str] = None
    docSubtype: Optional[str] = None
    confidence: Optional[float] = Field(
        default=None, description="Classifier confidence or probability score."
    )


class SimplificationResult(BaseModel):
    """Result of the simplification step, ready for the legal guide."""

    simplifiedText: Optional[str] = None
    importantSections: Optional[List[str]] = None  # Snippets to feed into the guide prompt.
    docType: Optional[str] = None
    docSubtype: Optional[str] = None


class SafetyCheckResult(BaseModel):
    """Aggregated view of the rule-based and LLM verification checks."""

    warnings: List[str] = Field(default_factory=list)
    ruleBasedFindings: Optional[List[str]] = None
    llmFindings: Optional[List[str]] = None


class ProcessDocumentResponse(BaseModel):
    """Structured response returned to the frontend."""

    docType: Optional[str] = None
    docSubtype: Optional[str] = None
    simplifiedText: Optional[str] = None
    legalGuide: Optional[LegalGuide] = None
    warnings: List[str] = Field(default_factory=list)
