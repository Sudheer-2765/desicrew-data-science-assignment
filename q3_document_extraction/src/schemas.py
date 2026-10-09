"""Schema definitions, Pydantic models, and document types for Q3 extraction pipeline."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    AADHAAR_CARD = "Aadhaar Card"
    PAN_CARD = "PAN Card"
    DRIVING_LICENCE = "Driving Licence"
    PASSPORT = "Passport"
    NACH_ECS_MANDATE = "NACH / ECS Mandate (handwritten)"
    FATCA_ANNEXURE = "FATCA Annexure Form (handwritten)"
    BENEFIT_ILLUSTRATION = "Benefit Illustration Declaration (handwritten)"
    MORAL_HAZARD = "Moral Hazard Questionnaire (handwritten)"
    MULTIPLE_POLICIES = "Multiple Policies Consent Form (handwritten)"
    SUITABILITY_PROFILER = "Suitability Profiler Declaration (handwritten)"


# Official target fields specified in assignment/Questions.docx
DOCUMENT_REQUIRED_FIELDS: Dict[DocumentType, List[str]] = {
    DocumentType.AADHAAR_CARD: [
        "Aadhaar Number",
        "Full Name",
        "Date of Birth",
        "Address",
    ],
    DocumentType.PAN_CARD: [
        "PAN Number",
        "Full Name",
        "Father's Name",
        "Date of Birth",
    ],
    DocumentType.DRIVING_LICENCE: [
        "DL Number",
        "Name",
        "Date of Issue",
        "Valid Till date",
    ],
    DocumentType.PASSPORT: [
        "Passport Number",
        "Date of Birth",
        "Date of Expiry",
        "MRZ Line 2",
    ],
    DocumentType.NACH_ECS_MANDATE: [
        "Bank Account Number",
        "IFSC Code",
        "Bank Name",
        "Amount (figures)",
        "Frequency",
    ],
    DocumentType.FATCA_ANNEXURE: [
        "Policy Number",
        "TIN / PAN",
        "Father's Name",
        "Place of Birth",
        "Nationality",
    ],
    DocumentType.BENEFIT_ILLUSTRATION: [
        "Application Number",
        "Policyholder Name",
        "Date",
        "Place",
    ],
    DocumentType.MORAL_HAZARD: [
        "Application Number",
        "Name of Life Assured",
        "Nominee Relationship",
        "Date",
        "Place",
    ],
    DocumentType.MULTIPLE_POLICIES: [
        "Proposer Name",
        "Reason for Multiple Policies (selected checkbox)",
        "Date",
        "Place",
    ],
    DocumentType.SUITABILITY_PROFILER: [
        "Application Number",
        "Name of Life Assured",
        "Name of Agent/SP",
        "Date",
        "Place",
    ],
}

HANDWRITTEN_DOCUMENT_TYPES = {
    DocumentType.NACH_ECS_MANDATE,
    DocumentType.FATCA_ANNEXURE,
    DocumentType.BENEFIT_ILLUSTRATION,
    DocumentType.MORAL_HAZARD,
    DocumentType.MULTIPLE_POLICIES,
    DocumentType.SUITABILITY_PROFILER,
}

# Configurable confidence threshold for human review flagging
DEFAULT_CONFIDENCE_THRESHOLD = 0.80


from typing import Literal

SourceType = Literal["printed", "handwritten", "checkbox", "mrz"]
ValidationStatus = Literal["passed", "failed", "not_applicable"]


class FieldExtraction(BaseModel):
    """Detailed extraction result and confidence scoring for an individual field."""
    field_name: str
    value: Optional[str] = None
    raw_value: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    source_type: SourceType = "printed"
    validation_status: ValidationStatus = "passed"
    is_handwritten: bool = False
    validation_passed: bool = True
    flagged_for_review: bool = False
    review_reason: Optional[str] = None


class ClassificationResult(BaseModel):
    """Result of document type classification."""
    filename: str
    document_type: DocumentType
    classification_confidence: float = Field(ge=0.0, le=1.0)
    classification_reason: str


class DocumentExtractionResult(BaseModel):
    """Complete structured extraction result for a processed document."""
    filename: str
    document_type: str
    classified_type: DocumentType
    classification_confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    extraction_method: str = "optical_fallback"
    is_handwritten_document: bool
    fields: Dict[str, FieldExtraction]
    average_confidence: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool = False
    flagged: bool = False
    flagged_fields_count: int = 0
    raw_model_response: Optional[Dict[str, Any]] = None


class FlaggedFieldRecord(BaseModel):
    """Entry in the human review flagging report."""
    filename: str
    document_type: str
    field_name: str
    extracted_value: Optional[str]
    confidence: float
    threshold: float
    reason: str

