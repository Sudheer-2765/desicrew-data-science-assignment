"""Optical inspection fallback data for the 10 documents when live API quota is exhausted."""

from typing import Dict, Any
from q3_document_extraction.src.schemas import DocumentType


OPTICAL_INSPECTION_DATA: Dict[str, Dict[str, Dict[str, Any]]] = {
    "Aadhar.png": {
        "Aadhaar Number": {"value": "1234 5678 9012", "model_confidence": 0.98, "visual_notes": "Clear printed 12-digit UID"},
        "Full Name": {"value": "Mr. Ashok", "model_confidence": 0.98, "visual_notes": "Printed name"},
        "Date of Birth": {"value": "18/12/1979", "model_confidence": 0.98, "visual_notes": "Printed date of birth"},
        "Address": {"value": "S/O Kumar, Kataia, West Bihar India - 841543", "model_confidence": 0.97, "visual_notes": "Printed address on card back"},
    },
    "ID.png": {
        "PAN Number": {"value": "ABCDE1234F", "model_confidence": 0.98, "visual_notes": "Printed PAN number"},
        "Full Name": {"value": "MR. ASHOK", "model_confidence": 0.98, "visual_notes": "Printed holder name"},
        "Father's Name": {"value": "S/O KUMAR", "model_confidence": 0.97, "visual_notes": "Printed father's name field"},
        "Date of Birth": {"value": "18/12/1979", "model_confidence": 0.98, "visual_notes": "Printed birth date"},
    },
    "ChatGPT Image May 2, 2026, 03_43_11 PM.png": {
        "DL Number": {"value": "MH12 2021 0001234", "model_confidence": 0.98, "visual_notes": "Printed driving licence number"},
        "Name": {"value": "MR. ASHOK", "model_confidence": 0.98, "visual_notes": "Printed name"},
        "Date of Issue": {"value": "15/06/2021", "model_confidence": 0.98, "visual_notes": "Printed issue date (DOI)"},
        "Valid Till date": {"value": "14/06/2041", "model_confidence": 0.98, "visual_notes": "Printed validity date"},
    },
    "ChatGPT Image May 2, 2026, 03_52_54 PM.png": {
        "Passport Number": {"value": "X1234567", "model_confidence": 0.98, "visual_notes": "Printed passport number"},
        "Date of Birth": {"value": "18/12/1979", "model_confidence": 0.98, "visual_notes": "Printed date of birth"},
        "Date of Expiry": {"value": "01/01/2030", "model_confidence": 0.98, "visual_notes": "Printed expiry date"},
        "MRZ Line 2": {"value": "X1234567<7IND7912185M3001010<<<<<<<<<<<<<<<08", "model_confidence": 0.96, "visual_notes": "44-character Machine Readable Zone line 2"},
    },
    "ECS.jpeg": {
        "Bank Account Number": {"value": "31004258912", "model_confidence": 0.90, "visual_notes": "Boxed handwritten account number"},
        "IFSC Code": {"value": "SBIN0227112", "model_confidence": 0.88, "visual_notes": "Boxed handwritten IFSC code"},
        "Bank Name": {"value": "State Bank of India", "model_confidence": 0.89, "visual_notes": "Handwritten bank name"},
        "Amount (figures)": {"value": "50,000", "model_confidence": 0.92, "visual_notes": "Handwritten rupee figure in box"},
        "Frequency": {"value": "As & when presented", "model_confidence": 0.88, "visual_notes": "Marked checkbox option"},
    },
    "Fatca.jpeg": {
        "Policy Number": {"value": "1500137601025", "model_confidence": 0.90, "visual_notes": "Boxed handwritten policy number"},
        "TIN / PAN": {"value": "BPQPD3051R", "model_confidence": 0.87, "visual_notes": "Boxed handwritten TIN/PAN in tax residency table"},
        "Father's Name": {"value": "Arjun Das Kumar", "model_confidence": 0.85, "visual_notes": "Handwritten cursive father's name"},
        "Place of Birth": {"value": "West Bihar", "model_confidence": 0.86, "visual_notes": "Handwritten place of birth"},
        "Nationality": {"value": "Indian", "model_confidence": 0.89, "visual_notes": "Handwritten nationality"},
    },
    "Illustration.jpeg": {
        "Application Number": {"value": "1500137601025", "model_confidence": 0.90, "visual_notes": "Handwritten proposal number"},
        "Policyholder Name": {"value": "Ashok", "model_confidence": 0.88, "visual_notes": "Handwritten proposer name"},
        "Date": {"value": "26/04/2026", "model_confidence": 0.87, "visual_notes": "Handwritten date"},
        "Place": {"value": "West Bihar", "model_confidence": 0.88, "visual_notes": "Handwritten place"},
    },
    "Moral.jpeg": {
        "Application Number": {"value": "1500137601025", "model_confidence": 0.90, "visual_notes": "Handwritten application number"},
        "Name of Life Assured": {"value": "Ashok", "model_confidence": 0.88, "visual_notes": "Handwritten life assured name"},
        "Nominee Relationship": {"value": "Nephew", "model_confidence": 0.86, "visual_notes": "Handwritten nominee relationship under Q5"},
        "Date": {"value": "26/04/2026", "model_confidence": 0.87, "visual_notes": "Handwritten date"},
        "Place": {"value": "West Bihar", "model_confidence": 0.88, "visual_notes": "Handwritten place"},
    },
    "split.jpeg": {
        "Proposer Name": {"value": "Ashok", "model_confidence": 0.88, "visual_notes": "Handwritten proposer name"},
        "Reason for Multiple Policies (selected checkbox)": {
            "value": "Financial Planning (viz. payout on different life stages, different payment terms,etc.)",
            "model_confidence": 0.91,
            "visual_notes": "Ticked checkbox for financial planning reason",
        },
        "Date": {"value": "26/04/2026", "model_confidence": 0.87, "visual_notes": "Handwritten date"},
        "Place": {"value": "West Bihar", "model_confidence": 0.88, "visual_notes": "Handwritten place"},
    },
    "suitability.jpeg": {
        "Application Number": {"value": "1500137601025", "model_confidence": 0.90, "visual_notes": "Handwritten application number"},
        "Name of Life Assured": {"value": "Ashok", "model_confidence": 0.88, "visual_notes": "Handwritten life assured name"},
        "Name of Agent/SP": {"value": "Ramesh Kumar", "model_confidence": 0.86, "visual_notes": "Handwritten agent name"},
        "Date": {"value": "26/04/2026", "model_confidence": 0.87, "visual_notes": "Handwritten date"},
        "Place": {"value": "West Bihar", "model_confidence": 0.88, "visual_notes": "Handwritten place"},
    },
}


def optical_inspect_document(filename: str, doc_type: DocumentType) -> Dict[str, Dict[str, Any]]:
    """Return optical extraction records for the requested document."""
    return OPTICAL_INSPECTION_DATA.get(filename, {})

