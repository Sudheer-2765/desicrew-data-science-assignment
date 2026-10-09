# DesiCrew Data Science Internship — Technical Assessment

A production-grade, enterprise-ready implementation of the DesiCrew Data Science Technical Assessment covering three core domains:
1. **Autonomous Excel Query Agent** (Natural Language to Data Analysis with CLI & Web UI)
2. **Context-Aware Document Assistant** (Multi-Turn RAG with Session Memory, Section Citations, and Web Chat)
3. **Multimodal Document Extraction Pipeline** (Classification, Field Extraction, Confidence Scoring, and Human-Review Flagging)

---

## 📊 Summary of Deliverables & Test Verification

| Module | Core Functionality | Test Suite | User Interface | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Question 1: Excel Agent** | Formula evaluation, multi-turn data analysis, natural language queries | 24 Passed | CLI & FastAPI Web UI (`:8000`) | ✅ Complete |
| **Question 2: Document Assistant** | Context memory, topic switching, anti-repetition, section citations | 47 Passed | 10-Turn CLI Demo & Web Chat (`:8002`) | ✅ Complete |
| **Question 3: Document Extraction** | 10-doc classification, multimodal extraction, confidence scores, review flagging | 27 Passed | Automated Batch Pipeline & Reports | ✅ Complete |
| **Total Test Suite** | **Full workspace test verification** | **98 Passed** | **All tests verified passing** | **100% Passed** |

---

## 📁 Repository Structure

```text
desicrew-data-science-assignment/
├── .gitignore                          # Strict gitignore protecting secrets and PII
├── README.md                           # Master project documentation
├── assignment/
│   └── Questions.docx                  # Official assignment requirements document
│
├── q1_excel_agent/                     # Question 1: Excel Query Agent
│   ├── README.md                       # Comprehensive Q1 documentation
│   ├── requirements.txt                # Dependencies for Q1
│   ├── .env.example                    # Sample environment file template
│   ├── input/
│   │   └── Inventory-Records-Sample-Data.xlsx  # Sample inventory dataset
│   ├── src/
│   │   ├── agent.py                    # Autonomous Excel analytical agent
│   │   ├── cli.py                      # Interactive terminal CLI runner
│   │   ├── config.py                   # Configuration and LLM initialization
│   │   ├── excel_tools.py              # Excel schema extraction & openpyxl query engine
│   │   └── web.py                      # FastAPI Web application (port 8000)
│   ├── tests/                          # 24 unit tests for Excel agent
│   └── Screenshots/                    # Visual proof of CLI & Web UI execution
│       ├── Screenshot1.png
│       ├── Screenshot2.png
│       └── Screenshot3.png
│
├── q2_document_assistant/              # Question 2: Context-Aware Document Assistant
│   ├── README.md                       # Comprehensive Q2 documentation
│   ├── requirements.txt                # Dependencies for Q2
│   ├── web_chat.py                     # Standalone FastAPI web chat application (port 8002)
│   ├── data/
│   │   └── index/                      # Precomputed embeddings and vector chunks
│   ├── demo/
│   │   ├── run_10_turns.py             # Reproducible 10-turn demonstration script
│   │   └── transcript_10_turns.json    # Exact recorded 10-turn conversation transcript
│   ├── documents/                      # Northstar Technologies fictional policy documents
│   │   ├── employee_support_policy.md
│   │   ├── leave_and_attendance_policy.md
│   │   └── reimbursement_policy.md
│   ├── src/
│   │   ├── answer_generator.py         # Response synthesis with section-level citations
│   │   ├── context_resolver.py         # Multi-turn anaphora and query resolution
│   │   ├── conversation.py             # Orchestration engine with anti-repetition guards
│   │   ├── embeddings.py               # Local semantic embedding generator
│   │   ├── indexer.py                  # Document chunking and vector indexer
│   │   ├── memory.py                   # Sliding-window session conversation memory
│   │   ├── models.py                   # Data models and Pydantic schemas
│   │   └── retriever.py                # Hybrid semantic & lexical retrieval system
│   ├── tests/                          # 47 unit tests for Document Assistant
│   └── Screenshots/                    # Visual proof of 10-turn demo & Web Chat
│       ├── Screenshot1.png ... Screenshot5.png
│
└── q3_document_extraction/             # Question 3: Multimodal Extraction Pipeline
    ├── README.md                       # Comprehensive Q3 documentation
    ├── requirements.txt                # Dependencies for Q3
    ├── input/
    │   └── README.md                   # Note on PII protection & document placement
    ├── output/                         # Structured deliverables for 10 documents
    │   ├── aadhaar.json
    │   ├── pan.json
    │   ├── driving_licence.json
    │   ├── passport.json
    │   ├── nach_ecs.json
    │   ├── fatca.json
    │   ├── benefit_illustration.json
    │   ├── moral_hazard.json
    │   ├── multiple_policies_consent.json
    │   ├── suitability_profiler.json
    │   ├── flagging_report.json        # Low-confidence human review report (JSON)
    │   ├── flagging_report.md          # Human review summary & threshold rationale
    │   └── handwriting_handling_notes.md # Deep dive into handwriting challenges & fallbacks
    ├── src/
    │   ├── confidence.py               # Mathematical confidence scoring engine
    │   ├── document_manifest.py        # Official document taxonomy and field registry
    │   ├── extractor.py                # Dual-tier multimodal vision & optical extractor
    │   ├── models.py                   # Pydantic schemas for all 10 document types
    │   ├── pipeline.py                 # End-to-end batch processing pipeline
    │   └── validator.py                # Format, regex, checksum, and date validators
    ├── tests/                          # 27 unit tests for Document Extraction
    └── Screenshots/                    # Visual proof of pipeline runs and test results
        ├── Screenshot1.png ... Screenshot5.png
```

---

## 🔒 Data Privacy & PII Compliance

> **Important Privacy Notice:**
> In accordance with international data privacy standards and security compliance guidelines, raw identity documents (Aadhaar cards, PAN cards, Passports, Driving Licences, and bank ECS mandates) containing real personal identification details, photographs, and signatures are **strictly excluded from this public Git repository** via `.gitignore`.
>
> All **structured extraction outputs**, **field-level confidence metrics**, **validation reports**, and **human-review audit flags** are fully preserved under `q3_document_extraction/output/`. New test documents can be placed into `q3_document_extraction/input/` for local processing at any time.

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12 / Windows 11)
- Git 2.40+

### 2. Environment Setup
Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/Sudheer-2765/desicrew-data-science-assignment.git
cd desicrew-data-science-assignment

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate  # On Linux/macOS
```

### 3. Install Dependencies
Install dependencies for all projects:

```bash
pip install -r q1_excel_agent/requirements.txt
pip install -r q2_document_assistant/requirements.txt
pip install -r q3_document_extraction/requirements.txt
pip install pytest pytest-asyncio
```

### 4. Configure API Keys (Optional)
Create `q1_excel_agent/.env` using `q1_excel_agent/.env.example` as a template if you wish to run with Google Gemini:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*(Note: All systems include full local heuristic and deterministic offline fallbacks; an active API key is not required for testing or offline execution).*

---

## 🧪 Unified Test Suite Verification

Run the entire test suite across all three projects simultaneously:

```bash
python -m pytest -q
```

**Expected Result:**
```text
..................................................................................................
98 passed in 8.24s
```

Run individual test suites:
```bash
# Question 1: 24 tests
python -m pytest q1_excel_agent/tests -q

# Question 2: 47 tests
python -m pytest q2_document_assistant/tests -q

# Question 3: 27 tests
python -m pytest q3_document_extraction/tests -q
```

---

## 📘 Project 1: Autonomous Excel Query Agent (`q1_excel_agent`)

An intelligent natural-language assistant that analyzes Excel spreadsheets, calculates formulas, resolves multi-step questions, and validates results against ground truth.

### Key Features
- **Dual Interface**: Interactive CLI runner + clean FastAPI Web UI with chat layout and table viewer.
- **Dynamic Formula & Computation Engine**: Direct calculation of averages, aggregations, conditional filtering, and revenue analysis on `Inventory-Records-Sample-Data.xlsx`.
- **Robust Guardrails**: Handles missing columns, schema mismatches, and malformed queries gracefully.

### Running Q1
```bash
# Run interactive CLI
python -m q1_excel_agent.src.cli

# Launch Web Application on port 8000
python -m uvicorn q1_excel_agent.src.web:app --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 📗 Project 2: Context-Aware Document Assistant (`q2_document_assistant`)

A multi-turn document conversational assistant engineered for corporate policy retrieval (Northstar Technologies).

### Key Features
- **Context Retention**: Remembers previous questions and resolves anaphoric references (e.g., *"How do I claim it?"* after asking about gym reimbursement).
- **Anti-Repetition Engine**: Tracks already-delivered facts within the session and synthesizes concise, non-redundant answers.
- **Seamless Topic Switching**: Handles sudden transitions between Leave Policies, Mental Health Support, and Travel Allowances without hallucination.
- **Mandatory Section Citations**: Every response cites the exact document title and section heading (e.g., `[Reimbursement Policy > Section 4.1]`).
- **Reproducible 10-Turn Demo**: Complete recorded dialogue demonstrating all required conversational capabilities.

### Running Q2
```bash
# Run the reproducible 10-turn demonstration
python q2_document_assistant/demo/run_10_turns.py

# Launch the Web Chat Interface on port 8002
python q2_document_assistant/web_chat.py
```
Open [http://127.0.0.1:8002](http://127.0.0.1:8002) in your browser.

---

## 📙 Project 3: Multimodal Document Extraction (`q3_document_extraction`)

A production pipeline for classifying and extracting critical fields from 10 diverse identity proofs and insurance documents.

### Key Features
- **Official 10-Document Taxonomy**: Aadhaar Card, PAN Card, Driving Licence, Passport, NACH/ECS Mandate, FATCA Annexure, Benefit Illustration, Moral Hazard Questionnaire, Multiple Policies Consent, and Suitability Profiler.
- **Dual-Tier Extraction Architecture**: Primary multimodal vision extraction with automated optical/regex fallbacks for quota limits and offline execution.
- **Field-Level Confidence Scoring**: Rigorous mathematical formula evaluating field presence, format validity, regex adherence, date sanity, and checksums.
- **Human-Review Flagging**: Configurable threshold (`0.85`) flags noisy, ambiguous, or handwritten documents for human validation.
- **Handwriting Robustness**: Dedicated technical review analyzing stroke variations, cursive handwriting, OCR degradation, and mitigation strategies.

### Running Q3
```bash
# Execute batch extraction pipeline over documents
python -m q3_document_extraction.src.pipeline
```
Review generated reports in `q3_document_extraction/output/`:
- `flagging_report.md`
- `flagging_report.json`
- `handwriting_handling_notes.md`

---

## 📷 Screenshots & Visual Proof

Screenshots verifying active execution and passing tests are archived in each project directory:
- **Q1**: `q1_excel_agent/Screenshots/` (CLI runs, Web UI dashboard)
- **Q2**: `q2_document_assistant/Screenshots/` (10-turn demo output, Web Chat interface)
- **Q3**: `q3_document_extraction/Screenshots/` (Pipeline execution, flagging reports)

---

## 👨‍💻 Author

**Sudheer Kumar Poluru**  
GitHub: [@Sudheer-2765](https://github.com/Sudheer-2765)  
Email: sudheerkumarpoluru2688@gmail.com
