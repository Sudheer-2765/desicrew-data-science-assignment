# Input Documents Directory

> **Notice:** Original sample identity documents (Aadhaar, PAN, Passport, Driving Licence, NACH Mandate, Insurance forms) provided with the assignment contain Personally Identifiable Information (PII) and are excluded from the version-controlled repository in compliance with data privacy best practices.

### Running the Extraction Pipeline
Place your target test documents (PDF or image formats `.png`, `.jpeg`, `.jpg`) into this directory and execute:

```bash
python -m q3_document_extraction.src.pipeline
```

The pipeline will classify each document, extract structured fields, assign field-level confidence scores, and flag documents below the confidence threshold (`0.85`) for human review in `q3_document_extraction/output/`.
