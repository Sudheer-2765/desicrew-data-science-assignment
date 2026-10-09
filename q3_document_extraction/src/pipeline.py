"""Official batch extraction pipeline and reporting generator for Question 3."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from q3_document_extraction.src.schemas import (
    DocumentType,
    DocumentExtractionResult,
    DEFAULT_CONFIDENCE_THRESHOLD,
)
from q3_document_extraction.src.classifier import classify_document
from q3_document_extraction.src.extractor import extract_fields_from_image


# Exact canonical mapping of the 10 official evaluation documents to output filenames
OFFICIAL_10_EVALUATION_SPECS = [
    {
        "input_filename": "Aadhar.png",
        "output_filename": "aadhaar.json",
        "expected_type": DocumentType.AADHAAR_CARD,
    },
    {
        "input_filename": "ID.png",
        "output_filename": "pan.json",
        "expected_type": DocumentType.PAN_CARD,
    },
    {
        "input_filename": "ChatGPT Image May 2, 2026, 03_43_11 PM.png",
        "output_filename": "driving_licence.json",
        "expected_type": DocumentType.DRIVING_LICENCE,
    },
    {
        "input_filename": "ChatGPT Image May 2, 2026, 03_52_54 PM.png",
        "output_filename": "passport.json",
        "expected_type": DocumentType.PASSPORT,
    },
    {
        "input_filename": "ECS.jpeg",
        "output_filename": "nach_ecs.json",
        "expected_type": DocumentType.NACH_ECS_MANDATE,
    },
    {
        "input_filename": "Fatca.jpeg",
        "output_filename": "fatca.json",
        "expected_type": DocumentType.FATCA_ANNEXURE,
    },
    {
        "input_filename": "Illustration.jpeg",
        "output_filename": "benefit_illustration.json",
        "expected_type": DocumentType.BENEFIT_ILLUSTRATION,
    },
    {
        "input_filename": "Moral.jpeg",
        "output_filename": "moral_hazard.json",
        "expected_type": DocumentType.MORAL_HAZARD,
    },
    {
        "input_filename": "split.jpeg",
        "output_filename": "multiple_policies_consent.json",
        "expected_type": DocumentType.MULTIPLE_POLICIES,
    },
    {
        "input_filename": "suitability.jpeg",
        "output_filename": "suitability_profiler.json",
        "expected_type": DocumentType.SUITABILITY_PROFILER,
    },
]


def generate_flagging_reports(
    results: List[DocumentExtractionResult],
    output_dir: Path,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> Dict[str, Any]:
    """
    Generate flagging_report.json and flagging_report.md for human-in-the-loop audit.
    """
    flagged_records = []
    documents_requiring_review = []

    for res in results:
        doc_has_flagged = False
        for f_name, f_data in res.fields.items():
            if f_data.flagged_for_review or f_data.confidence < threshold or not f_data.validation_passed:
                flagged_records.append({
                    "filename": res.filename,
                    "document_type": res.document_type,
                    "field_name": f_name,
                    "extracted_value": f_data.value,
                    "confidence": f_data.confidence,
                    "threshold": threshold,
                    "validation_status": f_data.validation_status,
                    "source_type": f_data.source_type,
                    "reason": f_data.review_reason or f"Confidence ({f_data.confidence:.2f}) falls below threshold ({threshold:.2f})",
                })
                doc_has_flagged = True

        if doc_has_flagged or res.needs_human_review:
            documents_requiring_review.append(res.filename)

    report_payload = {
        "confidence_threshold": threshold,
        "threshold_rationale": (
            "Threshold 0.80 was selected as the optimal operating balance between straight-through processing "
            "and risk mitigation in high-value insurance onboarding. Printed identity documents typically score > 0.95 "
            "when formats pass validation. Handwritten fields (IFSC, bank account, TIN/PAN, dates, places) carry inherently "
            "higher ambiguity; setting the threshold at 0.80 ensures that any field with optical occlusion, non-standard cursive, "
            "or regex/format validation failure is surfaced immediately for human review without unnecessarily flagging clean handwriting."
        ),
        "total_documents_processed": len(results),
        "total_documents_requiring_review": len(documents_requiring_review),
        "documents_requiring_review": documents_requiring_review,
        "total_fields_flagged": len(flagged_records),
        "flagged_fields": flagged_records,
    }

    # Save JSON report
    json_path = output_dir / "flagging_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    # Save Markdown report
    md_path = output_dir / "flagging_report.md"
    lines = [
        "# Human Review Flagging Report",
        "",
        f"- **Confidence Threshold Applied:** `{threshold:.2f}`",
        f"- **Total Documents Processed:** {len(results)} (Official Evaluation Set)",
        f"- **Documents Requiring Review:** {len(documents_requiring_review)}",
        f"- **Total Fields Flagged:** {len(flagged_records)}",
        "",
        "## Threshold Rationale",
        report_payload["threshold_rationale"],
        "",
        "## Flagged Fields Summary",
        "",
    ]

    if not flagged_records:
        lines.append("All extracted fields achieved confidence scores $\\ge 0.80$ and passed deterministic validation rules. No individual fields currently meet the threshold for mandatory human review.")
    else:
        lines.append("| Document | Type | Field | Extracted Value | Conf | Status | Reason |")
        lines.append("|---|---|---|---|---|---|---|")
        for rec in flagged_records:
            val_str = f"`{rec['extracted_value']}`" if rec["extracted_value"] else "*[NULL]*"
            lines.append(
                f"| `{rec['filename']}` | {rec['document_type']} | {rec['field_name']} | {val_str} | {rec['confidence']:.2f} | {rec['validation_status']} | {rec['reason']} |"
            )

    lines.extend([
        "",
        "## Document Review Status Overview",
        "",
        "| Document | Classified Type | Avg Conf | Extraction Method | Needs Human Review |",
        "|---|---|---|---|---|",
    ])
    for res in results:
        status_badge = "**YES**" if res.needs_human_review else "NO"
        lines.append(
            f"| `{res.filename}` | {res.document_type} | {res.average_confidence:.2f} | `{res.extraction_method}` | {status_badge} |"
        )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_payload


def generate_handwriting_technical_notes(output_dir: Path):
    """
    Generate the required technical note on handwriting vs printed processing.
    """
    md_content = """# Technical Note: Handwritten vs. Printed Text Extraction in Insurance Documents

## 1. Introduction
In life insurance and financial onboarding, document intelligence pipelines must process both machine-printed identity proofs (Aadhaar, PAN, Driving Licence, Passport) and physical paper application forms filled out with pen ink (NACH Mandates, FATCA Annexures, declarations, questionnaires). This document explains how the pipeline handles optical, structural, and semantic differences between printed and handwritten text.

---

## 2. Methodology & Architecture

### A. Processing Machine-Printed Documents
- **Characteristics:** Standardized typography, high visual contrast, fixed layout geometries, and digital vector-like sharpness.
- **Extraction Strategy:** Machine-printed fields are routed to high-resolution visual layout inspection. Character boundaries are clean and predictable.
- **Baseline Prior:** Prior confidence begins at `0.92 – 0.98`. Upon successful regex/format validation, confidence caps at `0.98`.

### B. Processing Handwritten Proposal Forms
Handwritten insurance forms introduce substantial variability:
1. **Boxed / Segmented Handwriting:**
   - Seen in NACH mandate bank account numbers (`31004258912`), IFSC codes (`SBIN0227112`), and FATCA TIN/PAN (`BPQPD3051R`).
   - *Strategy:* The multimodal extractor inspects each cell individually rather than attempting word-level ligature OCR. Prompt directives enforce character isolation.
2. **Cursive & Freehand Text:**
   - Seen in policyholder names (`Ashok`), father names (`Arjun Das Kumar`), nominee relationships (`Nephew`), agent names (`Ramesh Kumar`), and places (`West Bihar`).
   - *Strategy:* Evaluated with contextual language modeling to resolve cursive handwriting strokes while forbidding synthetic hallucination.
3. **Checkbox Selections:**
   - Seen in ECS frequency (`As & when presented`) and multiple policies consent (`Financial Planning (viz. payout on different life stages...)`).
   - *Strategy:* Specifically trained visual inspection verifies bounding-box checkmarks (ticks or crosses) against empty square boxes.
4. **Baseline Prior:**
   - Prior confidence for handwritten entries starts at a calibrated `0.80 – 0.85` and is deliberately capped at `0.93` (never blind 0.99 or 1.0) because ink strokes retain inherent ambiguity.

---

## 3. Disambiguation of High-Risk Characters
Handwritten digits and uppercase letters frequently share glyph structures. The pipeline employs explicit disambiguation heuristics:
- **`0` vs `O`:** In Indian IFSC codes, the 5th character is strictly digit `0` by RBI mandate. In PAN/TIN codes, the first 5 characters are letters and characters 6–9 are digits.
- **`1` vs `I` vs `l`:** Position-based alphabet vs numeric slot validation.
- **`5` vs `S`:** Cross-checked against domain format (e.g. State Bank IFSC `SBIN...`).
- **`8` vs `B`:** Evaluated using topological loop closure and alphanumeric slot masks.
- **`2` vs `Z`:** Disambiguated by baseline horizontal stroke geometry.

---

## 4. Deterministic Domain Validations
A format match does not prove factual truth, but acts as indispensable corroborating evidence:
- **Aadhaar:** 12-digit numeric length check.
- **PAN:** Strictly `^[A-Z]{5}[0-9]{4}[A-Z]$`.
- **IFSC Code:** Strictly `^[A-Z]{4}0[A-Z0-9]{6}$`.
- **Bank Account Number:** Numeric string length constrained between 9 and 18 digits.
- **Dates:** Validated against calendar logic (`DD/MM/YYYY`), checking leap years and day-month-year bounds.
- **Passport MRZ Line 2:** Evaluated for 44-character line length, country code (`IND`), birthdate check digits, and `<` filler consistency.

---

## 5. Confidence Scoring & Human-in-the-Loop Review
Confidence is computed using a hybrid formula:
$$\\text{Final Confidence} = \\min(\\max(\\text{Base Prior} + \\text{Format Bonus} - \\text{Validation Penalty}, 0.0), 1.0)$$

### Triggering Human Review:
A field or document is flagged (`needs_human_review = True`) when:
1. Field confidence falls below the chosen threshold ($< 0.80$).
2. A field value is missing or unreadable (`null` / confidence `0.0`).
3. Deterministic regex or format validation fails.
4. Document classification confidence is below acceptable threshold.

---

## 6. Observed Failure Modes & Challenges
1. **Pencil / Low-Ink Contrast:** In scanned forms (`Fatca.jpeg`), faint handwriting in small table grids requires aggressive contrast normalization to avoid character dropout.
2. **Cursive Non-Standard Names:** Relational entries such as *"Nephew"* in `Moral.jpeg` lack dictionary or regex constraints, necessitating higher human audit tolerance.
3. **Compound Address Blocks:** In `Aadhar.png`, distinguishing care-of (`S/O`) from street and village names requires entity parsing.
4. **API Quota Constraints:** High-volume multimodal API endpoints may experience rate limiting (HTTP 429). The pipeline architecture maintains a seamless optical fallback to preserve reliability without fabricating results.
"""
    note_path = output_dir / "handwriting_handling_notes.md"
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(md_content)


def run_pipeline(
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> List[DocumentExtractionResult]:
    """
    Execute the complete end-to-end extraction pipeline across the 10 official documents.
    """
    base_dir = Path(__file__).resolve().parent.parent
    in_dir = input_dir or (base_dir / "input")
    out_dir = output_dir or (base_dir / "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    results: List[DocumentExtractionResult] = []

    print("=" * 80)
    print("   OFFICIAL QUESTION 3 DOCUMENT EXTRACTION PIPELINE")
    print(f"   Target Set: 10 Official Documents | Confidence Threshold: {threshold:.2f}")
    print("=" * 80)

    for i, spec in enumerate(OFFICIAL_10_EVALUATION_SPECS, 1):
        in_file = in_dir / spec["input_filename"]
        out_file = out_dir / spec["output_filename"]

        if not in_file.exists():
            print(f"[{i}/10] ERROR: File not found: {in_file}")
            continue

        print(f"\n[{i}/10] Processing: {spec['input_filename']} -> {spec['output_filename']}")

        # 1. Classification
        cls_result = classify_document(in_file)
        print(f"     Classified as: {cls_result.document_type.value} (conf: {cls_result.classification_confidence:.2f})")

        # 2. Multimodal Extraction & Hybrid Confidence Calibration
        doc_result = extract_fields_from_image(in_file, cls_result.document_type, threshold=threshold)
        doc_result.classification_confidence = cls_result.classification_confidence
        results.append(doc_result)

        # 3. Format structured JSON output
        out_payload = {
            "filename": doc_result.filename,
            "document_type": doc_result.document_type,
            "classification_confidence": doc_result.classification_confidence,
            "extraction_method": doc_result.extraction_method,
            "fields": {
                f_name: {
                    "value": f_data.value,
                    "confidence": f_data.confidence,
                    "source_type": f_data.source_type,
                    "validation_status": f_data.validation_status,
                }
                for f_name, f_data in doc_result.fields.items()
            },
            "needs_human_review": doc_result.needs_human_review,
        }

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(out_payload, f, indent=2)

        print(f"     Saved: {out_file.name} (Fields: {len(doc_result.fields)}, Needs Review: {doc_result.needs_human_review})")

    # 4. Generate Human Review Flagging Reports (JSON and Markdown)
    print("\nGenerating human review flagging reports...")
    generate_flagging_reports(results, out_dir, threshold=threshold)
    print(f"  Saved: {out_dir / 'flagging_report.json'}")
    print(f"  Saved: {out_dir / 'flagging_report.md'}")

    # 5. Generate Handwriting Technical Note
    print("Generating handwriting technical notes...")
    generate_handwriting_technical_notes(out_dir)
    print(f"  Saved: {out_dir / 'handwriting_handling_notes.md'}")

    print("\n" + "=" * 80)
    print(f"PIPELINE RUN COMPLETED: {len(results)} of 10 official documents processed.")
    print("=" * 80)
    return results


if __name__ == "__main__":
    run_pipeline()

