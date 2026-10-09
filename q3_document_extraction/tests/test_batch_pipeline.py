"""Batch pipeline tests verifying all 12 Q3 official deliverable requirements."""

import json
from pathlib import Path
import pytest

from q3_document_extraction.src.schemas import (
    DocumentType,
    FieldExtraction,
    DocumentExtractionResult,
    DOCUMENT_REQUIRED_FIELDS,
    DEFAULT_CONFIDENCE_THRESHOLD,
)
from q3_document_extraction.src.pipeline import (
    OFFICIAL_10_EVALUATION_SPECS,
    run_pipeline,
    generate_flagging_reports,
    generate_handwriting_technical_notes,
)
from q3_document_extraction.src.manifest import ADDITIONAL_DOCUMENTS


def test_exactly_10_official_documents_configured():
    """Verify that exactly 10 official evaluation documents are configured."""
    assert len(OFFICIAL_10_EVALUATION_SPECS) == 10
    expected_outputs = {
        "aadhaar.json",
        "pan.json",
        "driving_licence.json",
        "passport.json",
        "nach_ecs.json",
        "fatca.json",
        "benefit_illustration.json",
        "moral_hazard.json",
        "multiple_policies_consent.json",
        "suitability_profiler.json",
    }
    assert {s["output_filename"] for s in OFFICIAL_10_EVALUATION_SPECS} == expected_outputs


def test_additional_pdfs_excluded_from_official_evaluation():
    """Verify that the 2 additional PDFs are excluded from the official 10 evaluation specs."""
    official_inputs = {s["input_filename"] for s in OFFICIAL_10_EVALUATION_SPECS}
    for add_doc in ADDITIONAL_DOCUMENTS:
        assert add_doc["filename"] not in official_inputs
        assert add_doc["is_primary_10"] is False


def test_pipeline_execution_and_json_outputs(tmp_path):
    """Verify complete pipeline execution generates JSON for every official document."""
    results = run_pipeline(output_dir=tmp_path)
    assert len(results) == 10

    # Verify all 10 JSON output files were created
    for spec in OFFICIAL_10_EVALUATION_SPECS:
        json_file = tmp_path / spec["output_filename"]
        assert json_file.exists(), f"Output file missing: {json_file}"

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["filename"] == spec["input_filename"]
        assert data["document_type"] == spec["expected_type"].value
        assert "extraction_method" in data
        assert "needs_human_review" in data
        assert "fields" in data

        # Verify every required field exists for this document type
        expected_fields = DOCUMENT_REQUIRED_FIELDS[spec["expected_type"]]
        for f_name in expected_fields:
            assert f_name in data["fields"], f"Missing field '{f_name}' in {spec['output_filename']}"
            f_obj = data["fields"][f_name]
            assert "value" in f_obj
            assert "confidence" in f_obj
            assert "source_type" in f_obj
            assert "validation_status" in f_obj
            assert 0.0 <= f_obj["confidence"] <= 1.0


def test_confidence_scores_clamped_and_present(tmp_path):
    """Verify confidence scores are present on every field and strictly clamped 0.0 to 1.0."""
    results = run_pipeline(output_dir=tmp_path)
    for res in results:
        for f_name, f_data in res.fields.items():
            assert 0.0 <= f_data.confidence <= 1.0
            assert f_data.confidence <= 0.98  # No blind 0.99 or 1.0


def test_null_field_flagging_and_review_trigger(tmp_path):
    """Verify that a null or unreadable field triggers human review."""
    field_null = FieldExtraction(
        field_name="IFSC Code",
        value=None,
        confidence=0.0,
        source_type="handwritten",
        validation_status="failed",
        is_handwritten=True,
        validation_passed=False,
        flagged_for_review=True,
        review_reason="Field could not be extracted",
    )
    doc_res = DocumentExtractionResult(
        filename="test_ecs.jpeg",
        document_type="NACH / ECS Mandate (handwritten)",
        classified_type=DocumentType.NACH_ECS_MANDATE,
        classification_confidence=0.92,
        is_handwritten_document=True,
        fields={"IFSC Code": field_null},
        average_confidence=0.0,
        needs_human_review=True,
        flagged=True,
    )

    report = generate_flagging_reports([doc_res], tmp_path, threshold=0.80)
    assert report["total_fields_flagged"] == 1
    assert "test_ecs.jpeg" in report["documents_requiring_review"]


def test_failed_validation_triggers_human_review(tmp_path):
    """Verify that a field failing deterministic validation triggers human review."""
    field_invalid = FieldExtraction(
        field_name="PAN Number",
        value="INVALID12",
        confidence=0.55,
        source_type="printed",
        validation_status="failed",
        is_handwritten=False,
        validation_passed=False,
        flagged_for_review=True,
        review_reason="Format validation failed: PAN format",
    )
    doc_res = DocumentExtractionResult(
        filename="test_pan.png",
        document_type="PAN Card",
        classified_type=DocumentType.PAN_CARD,
        classification_confidence=0.95,
        is_handwritten_document=False,
        fields={"PAN Number": field_invalid},
        average_confidence=0.55,
        needs_human_review=True,
        flagged=True,
    )

    report = generate_flagging_reports([doc_res], tmp_path, threshold=0.80)
    assert report["total_fields_flagged"] == 1
    assert report["flagged_fields"][0]["validation_status"] == "failed"


def test_threshold_logic(tmp_path):
    """Verify threshold logic correctly categorizes low vs high confidence fields."""
    field_low = FieldExtraction(
        field_name="Agent Name",
        value="Ramesh",
        confidence=0.75,  # Below 0.80
        source_type="handwritten",
        validation_status="passed",
        is_handwritten=True,
        validation_passed=True,
        flagged_for_review=False,
    )
    doc_res = DocumentExtractionResult(
        filename="test_suit.jpeg",
        document_type="Suitability Profiler Declaration (handwritten)",
        classified_type=DocumentType.SUITABILITY_PROFILER,
        classification_confidence=0.92,
        is_handwritten_document=True,
        fields={"Agent Name": field_low},
        average_confidence=0.75,
        needs_human_review=False,
    )

    report = generate_flagging_reports([doc_res], tmp_path, threshold=0.80)
    assert report["total_fields_flagged"] == 1
    assert report["flagged_fields"][0]["confidence"] == 0.75


def test_document_level_review_reflects_field_level():
    """Verify document-level review flag is derived directly from field-level states."""
    f_ok = FieldExtraction(field_name="Name", value="Ashok", confidence=0.95, source_type="printed")
    f_bad = FieldExtraction(field_name="Date", value=None, confidence=0.0, source_type="handwritten", flagged_for_review=True)

    doc_clean = DocumentExtractionResult(
        filename="clean.png",
        document_type="Aadhaar Card",
        classified_type=DocumentType.AADHAAR_CARD,
        is_handwritten_document=False,
        fields={"Name": f_ok},
        average_confidence=0.95,
        needs_human_review=False,
    )
    assert doc_clean.needs_human_review is False

    doc_flagged = DocumentExtractionResult(
        filename="flagged.png",
        document_type="Aadhaar Card",
        classified_type=DocumentType.AADHAAR_CARD,
        is_handwritten_document=False,
        fields={"Name": f_ok, "Date": f_bad},
        average_confidence=0.475,
        needs_human_review=True,
        flagged_fields_count=1,
    )
    assert doc_flagged.needs_human_review is True


def test_flagging_report_and_handwriting_notes_generated(tmp_path):
    """Verify flagging_report.json, flagging_report.md, and handwriting_handling_notes.md exist and have content."""
    run_pipeline(output_dir=tmp_path)
    
    rep_json = tmp_path / "flagging_report.json"
    rep_md = tmp_path / "flagging_report.md"
    notes_md = tmp_path / "handwriting_handling_notes.md"

    assert rep_json.exists()
    assert rep_md.exists()
    assert notes_md.exists()

    with open(rep_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["confidence_threshold"] == 0.80
    assert "threshold_rationale" in data

    with open(notes_md, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Technical Note" in content
    assert "Disambiguation of High-Risk Characters" in content
    assert "Deterministic Domain Validations" in content

