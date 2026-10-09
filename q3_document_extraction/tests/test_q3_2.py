"""Unit tests for Q3.2 classification, extraction schemas, and confidence calibration."""

from unittest.mock import MagicMock
from pathlib import Path
import pytest

from q3_document_extraction.src.schemas import (
    DocumentType,
    FieldExtraction,
    DocumentExtractionResult,
    ClassificationResult,
    DOCUMENT_REQUIRED_FIELDS,
)
from q3_document_extraction.src.confidence import calculate_field_confidence
from q3_document_extraction.src.extractor import extract_fields_from_image, build_extraction_prompt
from q3_document_extraction.src.classifier import classify_document


def test_classification_response_schema():
    """Verify ClassificationResult schema structure and constraints."""
    result = ClassificationResult(
        filename="test.png",
        document_type=DocumentType.PAN_CARD,
        classification_confidence=0.95,
        classification_reason="Observed Permanent Account Number card layout and Income Tax header",
    )
    assert result.filename == "test.png"
    assert result.document_type == DocumentType.PAN_CARD
    assert 0.0 <= result.classification_confidence <= 1.0
    assert len(result.classification_reason) > 5


def test_extraction_response_schema():
    """Verify DocumentExtractionResult schema structure and required attributes."""
    field = FieldExtraction(
        field_name="PAN Number",
        value="ABCDE1234F",
        confidence=0.96,
        source_type="printed",
        validation_status="passed",
        is_handwritten=False,
    )
    doc_res = DocumentExtractionResult(
        filename="ID.png",
        document_type=DocumentType.PAN_CARD.value,
        classified_type=DocumentType.PAN_CARD,
        classification_confidence=0.95,
        is_handwritten_document=False,
        fields={"PAN Number": field},
        average_confidence=0.96,
        needs_human_review=False,
    )
    assert doc_res.filename == "ID.png"
    assert doc_res.fields["PAN Number"].value == "ABCDE1234F"
    assert doc_res.needs_human_review is False
    assert 0.0 <= doc_res.average_confidence <= 1.0


def test_each_document_type_required_fields():
    """Verify extraction handles all 10 document types with their exact target field schemas."""
    for doc_type in DocumentType:
        prompt = build_extraction_prompt(doc_type)
        assert doc_type.value in prompt
        for req_field in DOCUMENT_REQUIRED_FIELDS[doc_type]:
            assert req_field in prompt


def test_confidence_range_strictly_clamped():
    """Verify confidence scores are strictly clamped between 0.0 and 1.0."""
    # Test high prior + bonus does not exceed 1.0
    field_high = calculate_field_confidence(
        field_name="PAN Number",
        extracted_value="ABCDE1234F",
        model_score=0.99,
        is_handwritten=False,
    )
    assert 0.0 <= field_high.confidence <= 1.0
    assert field_high.confidence <= 0.98

    # Test negative or zero prior does not fall below 0.0
    field_low = calculate_field_confidence(
        field_name="IFSC Code",
        extracted_value="INVALID",
        model_score=0.0,
        is_handwritten=True,
    )
    assert 0.0 <= field_low.confidence <= 1.0


def test_validation_integration():
    """Verify deterministic format validation updates status and flags."""
    # Valid Aadhaar
    f_valid = calculate_field_confidence("Aadhaar Number", "1234 5678 9012", is_handwritten=False)
    assert f_valid.validation_status == "passed"
    assert f_valid.validation_passed is True
    assert f_valid.flagged_for_review is False

    # Invalid Aadhaar
    f_invalid = calculate_field_confidence("Aadhaar Number", "1234ABCD", is_handwritten=False)
    assert f_invalid.validation_status == "failed"
    assert f_invalid.validation_passed is False
    assert f_invalid.flagged_for_review is True


def test_handwritten_source_type_handling():
    """Verify source_type is set to 'handwritten' for fields in handwritten proposal forms."""
    field = calculate_field_confidence(
        field_name="Bank Account Number",
        extracted_value="31004258912",
        is_handwritten=True,
    )
    assert field.source_type == "handwritten"
    assert field.is_handwritten is True
    # Boxed handwriting has calibrated confidence below printed baseline
    assert field.confidence <= 0.95


def test_checkbox_source_type_handling():
    """Verify checkbox selections receive 'checkbox' source_type."""
    field = calculate_field_confidence(
        field_name="Reason for Multiple Policies (selected checkbox)",
        extracted_value="Financial Planning",
        is_handwritten=True,
    )
    assert field.source_type == "checkbox"


def test_mrz_source_type_handling():
    """Verify passport MRZ field receives 'mrz' source_type and validated."""
    valid_mrz = "X1234567<7IND7912185M3001010<<<<<<<<<<<<<<<08"
    field = calculate_field_confidence(
        field_name="MRZ Line 2",
        extracted_value=valid_mrz,
        is_handwritten=False,
    )
    assert field.source_type == "mrz"
    assert field.validation_status == "passed"


def test_null_handling_for_unreadable_fields():
    """Verify unreadable or null fields receive 0.0 confidence and human review flag."""
    field = calculate_field_confidence(
        field_name="TIN / PAN",
        extracted_value=None,
        is_handwritten=True,
    )
    assert field.value is None
    assert field.confidence == 0.0
    assert field.validation_status == "failed"
    assert field.flagged_for_review is True
    assert "empty/null" in field.review_reason


def test_prevention_of_fabricated_values():
    """Verify empty/whitespace strings are not fabricated into valid values."""
    field = calculate_field_confidence(
        field_name="Application Number",
        extracted_value="   ",
        is_handwritten=True,
    )
    assert field.value is None
    assert field.confidence == 0.0
    assert field.flagged_for_review is True


def test_mock_gemini_multimodal_extraction(monkeypatch):
    """Verify extractor properly handles and calibrates mock Gemini multimodal responses."""
    mock_resp = MagicMock()
    mock_resp.text = """{
      "fields": {
        "PAN Number": {"value": "ABCDE1234F", "model_confidence": 0.95},
        "Full Name": {"value": "MR. ASHOK", "model_confidence": 0.95},
        "Father's Name": {"value": "S/O KUMAR", "model_confidence": 0.94},
        "Date of Birth": {"value": "18/12/1979", "model_confidence": 0.96}
      }
    }"""

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    test_file = Path(__file__).resolve().parent.parent / "input" / "ID.png"
    result = extract_fields_from_image(
        image_path=test_file,
        doc_type=DocumentType.PAN_CARD,
        client=mock_client,
    )

    assert result.document_type == "PAN Card"
    assert len(result.fields) == 4
    assert result.fields["PAN Number"].value == "ABCDE1234F"
    assert result.fields["PAN Number"].validation_status == "passed"
    assert result.fields["PAN Number"].confidence >= 0.90

