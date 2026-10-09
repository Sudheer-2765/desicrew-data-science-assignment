"""Hybrid confidence scoring engine combining model signals with deterministic rules."""

from typing import Optional, Tuple
from q3_document_extraction.src.validator import validate_field
from q3_document_extraction.src.schemas import DEFAULT_CONFIDENCE_THRESHOLD, FieldExtraction


def calculate_field_confidence(
    field_name: str,
    extracted_value: Optional[str],
    is_handwritten: bool = False,
    model_score: Optional[float] = None,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> FieldExtraction:
    """
    Calculate a calibrated hybrid confidence score for an extracted field.
    
    Combines:
    1. Base model confidence / visual clarity score
    2. Document medium nuance (handwritten vs printed baseline calibration)
    3. Deterministic regex & format validation
    4. Threshold-based flagging for human review
    """
    # 1. Base confidence depending on whether text is printed or handwritten
    if model_score is not None:
        base_confidence = min(max(model_score, 0.0), 1.0)
    else:
        # Default starting prior: 0.92 for printed text, 0.82 for handwritten text
        base_confidence = 0.82 if is_handwritten else 0.92

    # 2. Check for missing/null value
    if extracted_value is None or not str(extracted_value).strip():
        fn_lower = field_name.lower()
        src_type = "mrz" if "mrz" in fn_lower else ("checkbox" if "checkbox" in fn_lower or "frequency" in fn_lower else ("handwritten" if is_handwritten else "printed"))
        return FieldExtraction(
            field_name=field_name,
            value=None,
            raw_value="",
            confidence=0.0,
            source_type=src_type,
            validation_status="failed",
            is_handwritten=is_handwritten,
            validation_passed=False,
            flagged_for_review=True,
            review_reason="Field could not be extracted (empty/null value)",
        )

    clean_val = str(extracted_value).strip()

    # 3. Deterministic validation check
    valid, err_msg = validate_field(field_name, clean_val)

    # 4. Hybrid calibration
    if valid:
        # Verified format bonus (+0.06), capped at 0.98 (never blind 0.99 or 1.00 for handwriting)
        max_cap = 0.93 if is_handwritten else 0.98
        calibrated_confidence = min(base_confidence + 0.06, max_cap)
        reason = None
        flagged = calibrated_confidence < threshold
    else:
        # Substantial penalty if format verification failed (-0.35)
        calibrated_confidence = max(base_confidence - 0.35, 0.15)
        reason = f"Format validation failed: {err_msg}"
        flagged = True

    # Determine source_type
    fn_lower = field_name.lower()
    if "mrz" in fn_lower:
        source_type = "mrz"
    elif "checkbox" in fn_lower or "frequency" in fn_lower or "reason for multiple" in fn_lower:
        source_type = "checkbox"
    elif is_handwritten:
        source_type = "handwritten"
    else:
        source_type = "printed"

    validation_status = "passed" if valid else "failed"

    return FieldExtraction(
        field_name=field_name,
        value=clean_val,
        raw_value=clean_val,
        confidence=round(calibrated_confidence, 2),
        source_type=source_type,
        validation_status=validation_status,
        is_handwritten=is_handwritten,
        validation_passed=valid,
        flagged_for_review=flagged,
        review_reason=reason if flagged else None,
    )

