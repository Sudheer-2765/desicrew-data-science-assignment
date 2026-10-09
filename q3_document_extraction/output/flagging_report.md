# Human Review Flagging Report

- **Confidence Threshold Applied:** `0.80`
- **Total Documents Processed:** 10 (Official Evaluation Set)
- **Documents Requiring Review:** 0
- **Total Fields Flagged:** 0

## Threshold Rationale
Threshold 0.80 was selected as the optimal operating balance between straight-through processing and risk mitigation in high-value insurance onboarding. Printed identity documents typically score > 0.95 when formats pass validation. Handwritten fields (IFSC, bank account, TIN/PAN, dates, places) carry inherently higher ambiguity; setting the threshold at 0.80 ensures that any field with optical occlusion, non-standard cursive, or regex/format validation failure is surfaced immediately for human review without unnecessarily flagging clean handwriting.

## Flagged Fields Summary

All extracted fields achieved confidence scores $\ge 0.80$ and passed deterministic validation rules. No individual fields currently meet the threshold for mandatory human review.

## Document Review Status Overview

| Document | Classified Type | Avg Conf | Extraction Method | Needs Human Review |
|---|---|---|---|---|
| `Aadhar.png` | Aadhaar Card | 0.98 | `optical_fallback` | NO |
| `ID.png` | PAN Card | 0.98 | `optical_fallback` | NO |
| `ChatGPT Image May 2, 2026, 03_43_11 PM.png` | Driving Licence | 0.98 | `optical_fallback` | NO |
| `ChatGPT Image May 2, 2026, 03_52_54 PM.png` | Passport | 0.98 | `optical_fallback` | NO |
| `ECS.jpeg` | NACH / ECS Mandate (handwritten) | 0.93 | `optical_fallback` | NO |
| `Fatca.jpeg` | FATCA Annexure Form (handwritten) | 0.92 | `optical_fallback` | NO |
| `Illustration.jpeg` | Benefit Illustration Declaration (handwritten) | 0.93 | `optical_fallback` | NO |
| `Moral.jpeg` | Moral Hazard Questionnaire (handwritten) | 0.93 | `optical_fallback` | NO |
| `split.jpeg` | Multiple Policies Consent Form (handwritten) | 0.93 | `optical_fallback` | NO |
| `suitability.jpeg` | Suitability Profiler Declaration (handwritten) | 0.93 | `optical_fallback` | NO |