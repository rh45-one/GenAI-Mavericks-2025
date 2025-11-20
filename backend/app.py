"""Main FastAPI application for Justice Made Clear."""
from __future__ import annotations

import base64
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from . import dependencies, schemas
from .config import Settings, get_settings
from .services.classification_service import ClassificationService
from .services.ingest_service import IngestService
from .services.legal_guide_service import LegalGuideService
from .services.normalization_service import NormalizationService
from .services.safety_check_service import SafetyCheckService
from .services.simplification_service import SimplificationService


def _configure_app(settings: Settings) -> FastAPI:
    """Instantiate FastAPI with CORS middleware."""
    app = FastAPI(title=settings.api_title, version=settings.api_version)

    origins = [origin.strip() for origin in settings.backend_cors_origins.split(",") if origin.strip()]
    if not origins:
        origins = ["*"]
    if "*" in origins:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


settings = get_settings()
app = _configure_app(settings)


@app.get("/health")
async def health() -> dict:
    """Simple health probe."""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict:
    """Root endpoint to help local development and health checks.

    The frontend doesn't require this, but it's convenient when visiting
    the server root in a browser or quick smoke tests.
    """
    return {"message": "Justice Made Clear backend is running"}


@app.post(
    "/process_document",
    response_model=schemas.ProcessDocumentResponse,
)
async def process_document_endpoint(
    request: Request,
    ingest_service: IngestService = Depends(dependencies.get_ingest_service),
    normalization_service: NormalizationService = Depends(dependencies.get_normalization_service),
    classification_service: ClassificationService = Depends(dependencies.get_classification_service),
    simplification_service: SimplificationService = Depends(dependencies.get_simplification_service),
    legal_guide_service: LegalGuideService = Depends(dependencies.get_legal_guide_service),
    safety_check_service: SafetyCheckService = Depends(dependencies.get_safety_check_service),
) -> schemas.ProcessDocumentResponse:
    """Process uploaded/legal text documents end-to-end."""
    document_input = await _parse_document_input(request)

    ingest_result = ingest_service.ingest(document_input)
    segmented_document = normalization_service.normalize(ingest_result)
    classification = classification_service.classify(segmented_document)
    simplification = simplification_service.simplify(segmented_document, classification)
    legal_guide = legal_guide_service.build_guide(segmented_document, classification, simplification)
    safety = safety_check_service.evaluate(segmented_document, simplification, legal_guide)

    warnings = _merge_warnings(simplification.warnings, safety)

    return schemas.ProcessDocumentResponse(
        docType=classification.docType,
        docSubtype=classification.docSubtype,
        simplifiedText=simplification.simplifiedText,
        legalGuide=legal_guide,
        warnings=warnings,
    )


async def _parse_document_input(request: Request) -> schemas.DocumentInput:
    """Support JSON or multipart payloads from the frontend."""
    content_type = (request.headers.get("content-type") or "").lower()

    if "multipart/form-data" in content_type:
        form = await request.form()
        source_type = form.get("sourceType") or form.get("source_type")
        plain_text = form.get("plainText") or form.get("plain_text")
        upload = form.get("file")

        if upload is not None:
            file_bytes = await upload.read()
            file_content = base64.b64encode(file_bytes).decode("utf-8")
        else:
            file_content = None

        data = {
            "sourceType": source_type,
            "plainText": plain_text,
            "fileContent": file_content,
        }
        return _build_document_input(data)

    # Default to JSON parsing (also covers empty content-type when JSON is sent).
    try:
        payload = await request.json()
    except Exception as exc:  # pragma: no cover - FastAPI handles most cases
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request payload.",
        ) from exc

    return _build_document_input(payload)


def _build_document_input(payload: dict) -> schemas.DocumentInput:
    """Validate DocumentInput payload and raise HTTP 400 on errors."""
    try:
        return schemas.DocumentInput(**payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.errors(),
        ) from exc


def _merge_warnings(
    simplification_warnings: List[str],
    safety_result: schemas.SafetyCheckResult,
) -> List[str]:
    """Combine simplification + safety warnings preserving order."""
    combined = list(simplification_warnings or [])
    combined.extend(issue.message for issue in safety_result.issues)

    seen: set[str] = set()
    deduped: List[str] = []
    for warning in combined:
        if warning and warning not in seen:
            seen.add(warning)
            deduped.append(warning)
    return deduped
