# Question 3: Document Classification & Field Extraction Pipeline

## Purpose
Build an end-to-end automated processing pipeline for mixed identity proofs and insurance proposal onboarding documents. The system:
1. **Classifies** incoming documents into official categories (Aadhaar, PAN, DL, Passport, NACH/ECS, FATCA, Benefit Illustration, Moral Hazard, Multiple Policies, Suitability Profiler).
2. **Extracts** required structured fields using Gemini Multimodal Vision capabilities, specifically tailored for handwritten text.
3. **Validates & Calibrates Confidence** at the individual field level using a hybrid scoring algorithm combining model signals with deterministic regex and checksum rules.
4. **Flags** low-confidence or format-failing fields for human-in-the-loop review.

---

## Document Catalog

### Primary Evaluation Set (10 Documents)
| # | Filename | Classified Document Type | Medium | Key Challenge / Targets |
|---|---|---|---|---|
| 1 | `Aadhar.png` | Aadhaar Card | Printed | 12-digit UID, full address, DOB |
| 2 | `ID.png` | PAN Card | Printed | 10-char alphanumeric PAN (`ABCDE1234F`), father's name |
| 3 | `ChatGPT Image May 2, 2026, 03_43_11 PM.png` | Driving Licence | Printed | DL number, issue date, valid till date |
| 4 | `ChatGPT Image May 2, 2026, 03_52_54 PM.png` | Passport | Printed | Passport number, expiry, 44-char MRZ Line 2 |
| 5 | `ECS.jpeg` | NACH / ECS Mandate (handwritten) | Handwritten | Boxed account number, IFSC code (`SBIN0227112`), frequency checkbox |
| 6 | `Fatca.jpeg` | FATCA Annexure Form (handwritten) | Handwritten | Policy number, TIN/PAN (`BPQPD3051R`), place of birth, father's name |
| 7 | `Illustration.jpeg` | Benefit Illustration Declaration (handwritten) | Handwritten | Application number, policyholder name, date, place |
| 8 | `Moral.jpeg` | Moral Hazard Questionnaire (handwritten) | Handwritten | Application number, life assured name, nominee relationship (`Nephew`) |
| 9 | `split.jpeg` | Multiple Policies Consent Form (handwritten) | Handwritten | Proposer name, selected checkbox option, date, place |
| 10 | `suitability.jpeg` | Suitability Profiler Declaration (handwritten) | Handwritten | Application number, life assured, agent name (`Ramesh Kumar`), date, place |

### Secondary Documents (Outside Primary 10 Evaluation Set)
- `Assignment Ashok.pdf` — 2-page scanned HDFC Life Assignment Request Form.
- `Proposal Ashok.pdf` — 2-page scanned HDFC Life Customer Declaration / Proposal Form.

---

## Planned Architecture

```
                       Input Document (PNG/JPEG)
                                  │
                                  ▼
                   [1. Preprocessing & Inspection]
                                  │
                                  ▼
                     [2. Multimodal LLM Extraction]
                     Gemini Vision (Structured Pydantic)
                     - Document Type Classification
                     - Raw Field Extractions
                                  │
                                  ▼
                   [3. Deterministic Validation]
                   - Regex checks (PAN, Aadhaar, IFSC, DL)
                   - Date & currency format verification
                   - Account number digit & length checks
                                  │
                                  ▼
                 [4. Hybrid Confidence Scoring Engine]
                 - Base model visual probability
                 - Printed vs Handwritten calibration
                 - Format validation bonus / penalty
                                  │
                                  ▼
                 [5. Flagging & Reporting Generator]
                 - Threshold comparison (e.g. threshold = 0.80)
                 - Structured extraction JSON per document
                 - Human-review flagging report
```

---

## Handling Handwritten vs. Printed Text

- **Printed Text (IDs):** Standard layout, high OCR contrast, predictable font structures. Baseline confidence prior is high (0.92–0.98).
- **Handwritten Text (Forms):** Lower contrast, cursive variations, individual letter box alignments, varying ink strokes, and checkbox selections.
  - Requires higher resolution visual inspection.
  - Baseline confidence prior starts lower (0.80–0.85) and requires deterministic validation confirmation to pass high confidence.
  - Unrecognized or ambiguous characters trigger review flags rather than hallucinated corrections.

---

## Project Structure

```
q3_document_extraction/
├── input/                   # Supplied image and PDF documents
├── output/                  # Generated structured JSONs and flagging reports
├── src/
│   ├── __init__.py
│   ├── schemas.py           # Pydantic schemas, DocumentType enum, field targets
│   ├── manifest.py          # Document catalog, file mappings, and layout metadata
│   ├── validator.py         # Regex, date, IFSC, account format validation rules
│   └── confidence.py        # Hybrid confidence calibration algorithm
├── tests/
│   ├── __init__.py
│   └── test_foundation.py   # Unit tests for schemas, manifest, validators, and scoring
├── README.md                # System documentation
└── requirements.txt         # Minimal dependencies (pydantic, pillow, PyMuPDF, pytest, google-genai, python-dotenv)
```

---

## Testing

Run Q3 unit tests:
```bash
python -m pytest q3_document_extraction/tests -v
```

