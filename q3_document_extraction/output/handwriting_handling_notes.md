# Technical Note: Handwritten vs. Printed Text Extraction in Insurance Documents

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
$$\text{Final Confidence} = \min(\max(\text{Base Prior} + \text{Format Bonus} - \text{Validation Penalty}, 0.0), 1.0)$$

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
