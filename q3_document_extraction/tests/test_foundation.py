"""Unit tests for Q3 schemas, manifest, format validators, and hybrid confidence scoring."""

import pytest
from pathlib import Path
from q3_document_extraction.src.schemas import (
    DocumentType,
    DOCUMENT_REQUIRED_FIELDS,
    HANDWRITTEN_DOCUMENT_TYPES,
    DEFAULT_CONFIDENCE_THRESHOLD,
)
from q3_document_extraction.src.manifest import PRIMARY_MANIFEST, ADDITIONAL_DOCUMENTS
from q3_document_extraction.src.validator import (
    validate_aadhaar,
    validate_pan,
    validate_ifsc,
    validate_date,
    validate_bank_account,
    validate_field,
)
from q3_document_extraction.src.confidence import calculate_field_confidence


def test_manifest_covers_10_primary_documents():
    """Verify that the manifest exactly registers the 10 official primary documents."""
    assert len(PRIMARY_MANIFEST) == 10
    expected_files = {
        "Aadhar.png",
        "ID.png",
        "ChatGPT Image May 2, 2026, 03_43_11 PM.png",
        "ChatGPT Image May 2, 2026, 03_52_54 PM.png",
        "ECS.jpeg",
        "Fatca.jpeg",
        "Illustration.jpeg",
        "Moral.jpeg",
        "split.jpeg",
        "suitability.jpeg",
    }
    assert set(PRIMARY_MANIFEST.keys()) == expected_files

    # Verify input directory contains all 10 files
    input_dir = Path(__file__).resolve().parent.parent / "input"
    for fname in expected_files:
        assert (input_dir / fname).exists(), f"Input file missing: {fname}"


def test_additional_documents_identified():
    """Verify secondary PDFs are registered separately from primary 10-document set."""
    assert len(ADDITIONAL_DOCUMENTS) == 2
    filenames = [d["filename"] for d in ADDITIONAL_DOCUMENTS]
    assert "Assignment Ashok.pdf" in filenames
    assert "Proposal Ashok.pdf" in filenames
    for d in ADDITIONAL_DOCUMENTS:
        assert d["is_primary_10"] is False


def test_required_fields_match_official_specification():
    """Verify official document types match target field lists from Questions.docx."""
    assert len(DOCUMENT_REQUIRED_FIELDS) == 10
    
    # Aadhaar Card: Aadhaar Number, Full Name, Date of Birth, Address
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.AADHAAR_CARD] == [
        "Aadhaar Number", "Full Name", "Date of Birth", "Address"
    ]
    # PAN Card: PAN Number, Full Name, Father's Name, Date of Birth
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.PAN_CARD] == [
        "PAN Number", "Full Name", "Father's Name", "Date of Birth"
    ]
    # Driving Licence: DL Number, Name, Date of Issue, Valid Till date
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.DRIVING_LICENCE] == [
        "DL Number", "Name", "Date of Issue", "Valid Till date"
    ]
    # Passport: Passport Number, Date of Birth, Date of Expiry, MRZ Line 2
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.PASSPORT] == [
        "Passport Number", "Date of Birth", "Date of Expiry", "MRZ Line 2"
    ]
    # NACH / ECS Mandate: Bank Account Number, IFSC Code, Bank Name, Amount (figures), Frequency
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.NACH_ECS_MANDATE] == [
        "Bank Account Number", "IFSC Code", "Bank Name", "Amount (figures)", "Frequency"
    ]
    # FATCA Annexure Form: Policy Number, TIN / PAN, Father's Name, Place of Birth, Nationality
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.FATCA_ANNEXURE] == [
        "Policy Number", "TIN / PAN", "Father's Name", "Place of Birth", "Nationality"
    ]
    # Benefit Illustration: Application Number, Policyholder Name, Date, Place
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.BENEFIT_ILLUSTRATION] == [
        "Application Number", "Policyholder Name", "Date", "Place"
    ]
    # Moral Hazard: Application Number, Name of Life Assured, Nominee Relationship, Date, Place
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.MORAL_HAZARD] == [
        "Application Number", "Name of Life Assured", "Nominee Relationship", "Date", "Place"
    ]
    # Multiple Policies: Proposer Name, Reason for Multiple Policies (selected checkbox), Date, Place
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.MULTIPLE_POLICIES] == [
        "Proposer Name", "Reason for Multiple Policies (selected checkbox)", "Date", "Place"
    ]
    # Suitability Profiler: Application Number, Name of Life Assured, Name of Agent/SP, Date, Place
    assert DOCUMENT_REQUIRED_FIELDS[DocumentType.SUITABILITY_PROFILER] == [
        "Application Number", "Name of Life Assured", "Name of Agent/SP", "Date", "Place"
    ]


def test_deterministic_format_validators():
    """Verify format validators for regex compliance."""
    # Aadhaar (12 digits)
    assert validate_aadhaar("1234 5678 9012")[0] is True
    assert validate_aadhaar("123456789012")[0] is True
    assert validate_aadhaar("1234 5678")[0] is False  # 8 digits

    # PAN (5 letters + 4 digits + 1 letter)
    assert validate_pan("ABCDE1234F")[0] is True
    assert validate_pan("BPQPD3051R")[0] is True
    assert validate_pan("INVALIDPAN12")[0] is False

    # IFSC (4 letters + 0 + 6 alphanumeric)
    assert validate_ifsc("SBIN0227112")[0] is True
    assert validate_ifsc("HDFC0001234")[0] is True
    assert validate_ifsc("SBIN9227112")[0] is False  # 5th char not '0'

    # Dates
    assert validate_date("18/12/1979")[0] is True
    assert validate_date("26/04/2026")[0] is True
    assert validate_date("32/13/2026")[0] is False

    # Bank Account
    assert validate_bank_account("31004258912")[0] is True
    assert validate_bank_account("3100")[0] is False  # too short


def test_hybrid_confidence_scoring_valid_field():
    """Verify valid field receives boosted confidence and no flag."""
    field = calculate_field_confidence(
        field_name="PAN Number",
        extracted_value="ABCDE1234F",
        is_handwritten=False,
    )
    assert field.confidence >= 0.85
    assert field.confidence <= 0.98
    assert field.validation_passed is True
    assert field.flagged_for_review is False


def test_hybrid_confidence_scoring_invalid_field():
    """Verify invalid/corrupted field receives penalty and is flagged for review."""
    field = calculate_field_confidence(
        field_name="IFSC Code",
        extracted_value="SBIN999",  # Invalid IFSC
        is_handwritten=True,
    )
    assert field.confidence < DEFAULT_CONFIDENCE_THRESHOLD
    assert field.validation_passed is False
    assert field.flagged_for_review is True
    assert "Format validation failed" in field.review_reason


def test_hybrid_confidence_scoring_null_field():
    """Verify empty/null field is scored at 0.0 and flagged."""
    field = calculate_field_confidence(
        field_name="Bank Account Number",
        extracted_value="",
        is_handwritten=True,
    )
    assert field.confidence == 0.0
    assert field.flagged_for_review is True
    assert "empty/null" in field.review_reason

