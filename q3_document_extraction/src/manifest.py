"""Manifest mapping supplied files to official document types and extraction expectations."""

from typing import Dict, Any, List
from q3_document_extraction.src.schemas import DocumentType, DOCUMENT_REQUIRED_FIELDS


PRIMARY_MANIFEST: Dict[str, Dict[str, Any]] = {
    "Aadhar.png": {
        "filename": "Aadhar.png",
        "document_type": DocumentType.AADHAAR_CARD,
        "is_handwritten": False,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.AADHAAR_CARD],
        "layout_notes": "Printed digital Aadhaar card showing both front and back faces. High contrast.",
    },
    "ID.png": {
        "filename": "ID.png",
        "document_type": DocumentType.PAN_CARD,
        "is_handwritten": False,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.PAN_CARD],
        "layout_notes": "Printed Permanent Account Number (PAN) Card with photo, QR code, and standard layout.",
    },
    "ChatGPT Image May 2, 2026, 03_43_11 PM.png": {
        "filename": "ChatGPT Image May 2, 2026, 03_43_11 PM.png",
        "document_type": DocumentType.DRIVING_LICENCE,
        "is_handwritten": False,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.DRIVING_LICENCE],
        "layout_notes": "Printed Indian Union Driving Licence (Maharashtra State) with smart chip and QR code.",
    },
    "ChatGPT Image May 2, 2026, 03_52_54 PM.png": {
        "filename": "ChatGPT Image May 2, 2026, 03_52_54 PM.png",
        "document_type": DocumentType.PASSPORT,
        "is_handwritten": False,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.PASSPORT],
        "layout_notes": "Printed Indian Passport data page featuring two-line Machine Readable Zone (MRZ) at bottom.",
    },
    "ECS.jpeg": {
        "filename": "ECS.jpeg",
        "document_type": DocumentType.NACH_ECS_MANDATE,
        "is_handwritten": True,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.NACH_ECS_MANDATE],
        "layout_notes": "Scanned HDFC Life NACH Mandate instruction form with boxed handwritten account/IFSC characters and checkboxes.",
    },
    "Fatca.jpeg": {
        "filename": "Fatca.jpeg",
        "document_type": DocumentType.FATCA_ANNEXURE,
        "is_handwritten": True,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.FATCA_ANNEXURE],
        "layout_notes": "Scanned HDFC Life FATCA Annexure Form with tabular and boxed handwritten text (TIN/PAN, place, names).",
    },
    "Illustration.jpeg": {
        "filename": "Illustration.jpeg",
        "document_type": DocumentType.BENEFIT_ILLUSTRATION,
        "is_handwritten": True,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.BENEFIT_ILLUSTRATION],
        "layout_notes": "Scanned Customer Declaration - Benefit Illustration with handwritten application number, name, date, place.",
    },
    "Moral.jpeg": {
        "filename": "Moral.jpeg",
        "document_type": DocumentType.MORAL_HAZARD,
        "is_handwritten": True,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.MORAL_HAZARD],
        "layout_notes": "Scanned Moral Hazard Questionnaire with handwritten application number, life assured name, and nephew relationship.",
    },
    "split.jpeg": {
        "filename": "split.jpeg",
        "document_type": DocumentType.MULTIPLE_POLICIES,
        "is_handwritten": True,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.MULTIPLE_POLICIES],
        "layout_notes": "Scanned Split & Multiple Policies Customer Consent form with checked box and handwritten details.",
    },
    "suitability.jpeg": {
        "filename": "suitability.jpeg",
        "document_type": DocumentType.SUITABILITY_PROFILER,
        "is_handwritten": True,
        "required_fields": DOCUMENT_REQUIRED_FIELDS[DocumentType.SUITABILITY_PROFILER],
        "layout_notes": "Scanned Customer Declaration - Suitability Profiler with handwritten proposer name and agent name.",
    },
}

# Secondary documents supplied in workspace but outside official 10-document evaluation set
ADDITIONAL_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "filename": "Assignment Ashok.pdf",
        "format": "PDF (2 pages, scanned images)",
        "description": "Scanned HDFC Life Assignment Request Form (assigning policy to HDFC Bank for loan protection).",
        "is_primary_10": False,
    },
    {
        "filename": "Proposal Ashok.pdf",
        "format": "PDF (2 pages, scanned images)",
        "description": "Scanned HDFC Life Customer Declaration - Application/Proposal Form for Sanjay Par Advantage product.",
        "is_primary_10": False,
    },
]


def get_manifest_entry(filename: str) -> Dict[str, Any]:
    """Retrieve manifest entry for a specific document file."""
    if filename in PRIMARY_MANIFEST:
        return PRIMARY_MANIFEST[filename]
    raise KeyError(f"File '{filename}' is not in the primary 10-document manifest.")

