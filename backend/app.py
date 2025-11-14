"""Main FastAPI application for Justice Made Clear.

This module exposes the POST /process_document endpoint that orchestrates
all internal services: ingestion/OCR, normalization, classification,
simplification, legal guide generation, and safety checks.
"""
from fastapi import FastAPI, Depends

from . import dependencies
from . import schemas


app = FastAPI(title="Justice Made Clear API")


class BackendAPI:
    """Facade that mirrors the class diagram responsibilities."""

    def processDocument(self, document_input: schemas.DocumentInput) -> schemas.ProcessDocumentResponse:
        """Run the entire pipeline end-to-end.

        Orchestration order:
        1. ingestAndOcr -> produces raw text plus metadata.
        2. normalizeAndSegment -> cleans text and identifies sections.
        3. classifyDocument -> decides between resolution vs procedural writing.
        4. simplifyDocument -> branches to resolution/procedural methods.
        5. generateLegalGuide -> builds four-block LegalGuide DTO.
        6. safetyCheck -> aggregates warnings for the frontend.
        """
        # TODO: Wiring once services are implemented.
        raise NotImplementedError("Pipeline orchestration to be implemented during the prototype sprint.")

    def ingestAndOcr(self, document_input: schemas.DocumentInput):
        """Decide how to ingest based on sourceType, call OCR if needed."""
        raise NotImplementedError

    def normalizeAndSegment(self, ingest_result: schemas.IngestResult):
        """Invoke NormalizationService to clean text and compute sections."""
        raise NotImplementedError

    def classifyDocument(self, segmented_document: schemas.SegmentedDocument):
        """Call ClassificationService.classifyWithLLM via LLMClient."""
        raise NotImplementedError

    def simplifyDocument(self, classification_result: schemas.ClassificationResult, normalized_document: schemas.SegmentedDocument):
        """Branch to SimplificationService.simplifyResolution or simplifyProceduralWriting."""
        raise NotImplementedError

    def generateLegalGuide(self, simplification_result: schemas.SimplificationResult):
        """Delegate to LegalGuideService.buildGuide to assemble LegalGuide DTO."""
        raise NotImplementedError

    def safetyCheck(self, simplification_result: schemas.SimplificationResult, original_document: schemas.SegmentedDocument):
        """Call SafetyCheckService.ruleBasedCheck + llmVerification to produce warnings."""
        raise NotImplementedError


@app.post("/process_document")
def process_document_endpoint(
    document_input: schemas.DocumentInput,
    llm_client=Depends(dependencies.get_llm_client),
    ocr_service=Depends(dependencies.get_ocr_service),
    app_config=Depends(dependencies.get_config),
) -> schemas.ProcessDocumentResponse:
    """Entry point invoked by the frontend upload form.

    Expected request body (DocumentInput):
    - sourceType: text | pdf | image.
    - fileContent: binary upload for pdf/image (TBD) or base64 placeholder.
    - plainText: optional field when users directly provide text.

    Expected response skeleton:
    {
      "docType": "RESOLUCION_JURIDICA",
      "docSubtype": "SENTENCIA",
      "simplifiedText": "...",
      "legalGuide": {
        "meaningForYou": "...",
        "whatToDoNow": "...",
        "whatHappensNext": "...",
        "deadlinesAndRisks": "..."
      },
      "warnings": []
    }

    TODO: instantiate BackendAPI, inject services, run pipeline, and return DTO.
    """
    # Placeholder response so the endpoint shape is visible to integrators.
    return schemas.ProcessDocumentResponse(
        docType=None,
        docSubtype=None,
        simplifiedText="",
        legalGuide=None,
        warnings=[],
    )
