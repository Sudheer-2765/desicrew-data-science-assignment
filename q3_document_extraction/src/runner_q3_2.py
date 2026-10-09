"""Q3.2 Development test runner for the 10 official documents."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from q3_document_extraction.src.schemas import DocumentExtractionResult
from q3_document_extraction.src.classifier import classify_document
from q3_document_extraction.src.extractor import extract_fields_from_image
from q3_document_extraction.src.manifest import PRIMARY_MANIFEST


PRIMARY_FILES = [
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
]


def run_q3_2_evaluation(
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> List[DocumentExtractionResult]:
    """
    Run classification and extraction over the 10 official documents,
    saving development outputs to output/q3_2/.
    """
    base_dir = Path(__file__).resolve().parent.parent
    in_dir = input_dir or (base_dir / "input")
    out_dir = output_dir or (base_dir / "output" / "q3_2")
    out_dir.mkdir(parents=True, exist_ok=True)

    results: List[DocumentExtractionResult] = []

    print("=" * 80)
    print("   Q3.2 DOCUMENT CLASSIFICATION & MULTIMODAL EXTRACTION TEST RUNNER")
    print("=" * 80)

    for i, fname in enumerate(PRIMARY_FILES, 1):
        file_path = in_dir / fname
        if not file_path.exists():
            print(f"[{i}/10] Missing file: {fname}")
            continue

        print(f"\n[{i}/10] Processing: {fname}...")

        # 1. Classification
        cls_result = classify_document(file_path)
        print(f"   Predicted Type: {cls_result.document_type.value} (Confidence: {cls_result.classification_confidence:.2f})")
        print(f"   Reason: {cls_result.classification_reason}")

        # 2. Field Extraction & Calibration
        doc_result = extract_fields_from_image(file_path, cls_result.document_type)
        doc_result.classification_confidence = cls_result.classification_confidence
        results.append(doc_result)

        # 3. Save development JSON
        out_file = out_dir / f"{fname}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(doc_result.model_dump(), f, indent=2)

        print(f"   Extracted {len(doc_result.fields)} fields (Avg Confidence: {doc_result.average_confidence:.2f})")
        for f_name, f_data in doc_result.fields.items():
            val_display = f_data.value if f_data.value else "<NULL>"
            flag_str = "[FLAGGED]" if f_data.flagged_for_review else "[OK]"
            print(f"     * {f_name}: {val_display} (conf={f_data.confidence}, type={f_data.source_type}, status={f_data.validation_status}) {flag_str}")

    print("\n" + "=" * 80)
    print(f"Completed Q3.2 processing of {len(results)} documents.")
    print(f"Development JSON results saved in: {out_dir}")
    print("=" * 80)
    return results


if __name__ == "__main__":
    from typing import Optional
    run_q3_2_evaluation()
