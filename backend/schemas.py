"""Shared DTOs and schema definitions for the backend pipeline."""
from __future__ import annotations

from typing import Dict, List, Optional

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


class DocumentMetadata(BaseModel):
    """Common metadata captured during ingestion."""

    sourceType: str
    language: Optional[str] = None
    pageCount: Optional[int] = None
    charLength: Optional[int] = None
    extra: Dict[str, str] = Field(default_factory=dict)


class DocumentSection(BaseModel):
    """Named section extracted from a legal document."""

    name: str
    content: Optional[str] = None
    confidence: Optional[float] = Field(
        default=None, description="Confidence score from heuristics or ML models."
    )


class IngestResult(BaseModel):
    """Output of IngestService before normalization occurs."""

    rawText: str
    metadata: DocumentMetadata


class SegmentedDocument(BaseModel):
    """Normalized representation used by classification and simplification."""

    rawText: str
    normalizedText: str
    sections: List[DocumentSection] = Field(default_factory=list)
    metadata: Optional[DocumentMetadata] = None


class ClassificationResult(BaseModel):
    """Document type and subtype plus diagnostic information."""

    docType: str
    docSubtype: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str = Field(..., description="RULES_ONLY | LLM | HYBRID | ML")
    explanations: List[str] = Field(default_factory=list)


class SimplificationResult(BaseModel):
    """Result of the simplification step, ready for the legal guide."""

    simplifiedText: str
    docType: str
    docSubtype: str
    importantSections: List[DocumentSection] = Field(default_factory=list)
    strategy: str = Field(..., description="Which simplification branch was applied.")
    provider: str = Field(..., description="LLM/ML backend used for simplification.")
    truncated: bool = False
    warnings: List[str] = Field(default_factory=list)


class LegalGuide(BaseModel):
    """Four-block legal guidance returned to the citizen."""

    meaningForYou: str
    whatToDoNow: str
    whatHappensNext: str
    deadlinesAndRisks: str
    provider: str = Field(..., description="LLM/ML backend used for legal guide.")


class SafetyIssue(BaseModel):
    """Structured issue produced by the safety checker."""

    code: str
    message: str
    severity: str = Field(default="warning")


class SafetyCheckResult(BaseModel):
    """Aggregated view of the rule-based and model verification checks."""

    isSafe: bool
    issues: List[SafetyIssue] = Field(default_factory=list)
    ruleBasedFlags: List[str] = Field(default_factory=list)
    llmVerdict: Optional[str] = None


class ProcessDocumentResponse(BaseModel):
    """Structured response returned to the frontend."""

    docType: Optional[str] = None
    docSubtype: Optional[str] = None
    simplifiedText: Optional[str] = None
    legalGuide: Optional[LegalGuide] = None
    warnings: List[str] = Field(default_factory=list)
