# Question 2: Document-Aware Support Assistant

A section-grounded, multi-turn conversational support assistant for **Northstar Technologies** internal operations policies.

---

## 1. System Architecture Overview

The system is organized into modular indexing, retrieval, memory, context resolution, generation, and presentation layers:

```
q2_document_assistant/
├── documents/                                  # Source knowledge base Markdown documents (Q2.1)
│   ├── employee_support_policy.md              # 7 numbered sections (SLA, channels, access, etc.)
│   ├── leave_and_attendance_policy.md          # 10 numbered sections (hours, leave, WFH, sick leave)
│   ├── reimbursement_policy.md                 # 9 numbered sections (caps, receipts, approvals, mileage)
│   └── README.md                               # Catalog and section reference index
├── src/                                        # Core application package
│   ├── __init__.py                             # Package initialization
│   ├── models.py                               # Pydantic models (Document, Chunk, RetrievalResult, ConversationTurn, AssistantResponse, SessionState)
│   ├── document_loader.py                      # Markdown document loader and metadata parser
│   ├── chunker.py                              # Section-aware parser (boundaries preserved)
│   ├── embeddings.py                           # Hybrid embedding provider with deterministic local fallback
│   ├── indexer.py                              # Local vector index builder & serializer
│   ├── retriever.py                            # Hybrid vector + lexical retriever with citations
│   ├── memory.py                               # Isolated multi-turn session memory manager (bounded history, TTL)
│   ├── context_resolver.py                     # Follow-up pronoun resolution, domain classification, and ambiguity handler
│   ├── answer_generator.py                     # Grounded answer synthesizer with anti-repetition and mandatory citations
│   ├── conversation.py                         # Top-level DocumentSupportAssistant coordinator
│   └── web_chat.py                             # FastAPI REST API & interactive web application
├── demo/                                       # Official 10-turn reproducible demonstration
│   ├── run_10_turn_demo.py                     # Executable demonstration script
│   └── 10_turn_transcript.md                   # Verbatim 10-turn conversational transcript
├── data/
│   └── index/                                  # Local reproducible index storage
│       ├── chunks.json                         # Chunk texts, section numbers, titles, sources
│       ├── embeddings.npy                      # 1024-dim normalized vector matrix
│       └── index_meta.json                     # Index metadata, timestamps, chunk counts
├── tests/
│   ├── test_q2_2.py                            # Indexer & retrieval tests (19 tests)
│   ├── test_q2_3.py                            # Conversational engine & multi-turn memory tests (15 tests)
│   └── test_q2_4.py                            # Web API & chat integration tests (13 tests)
├── web_chat.py                                 # Top-level CLI launcher for the web application
├── requirements.txt                            # Dependencies (pydantic, numpy, fastapi, uvicorn, etc.)
└── README.md                                   # Comprehensive technical guide
```

---

## 2. Interactive Web Chat Interface (Task Q2.4)

### 2.1 Starting the Web Application
From the workspace root (`C:\Documents\Desi_crew`), launch the interactive server in Windows PowerShell:

```powershell
python -m q2_document_assistant.web_chat
```
*Alternatively, start directly via Uvicorn:*
```powershell
python -m uvicorn q2_document_assistant.src.web_chat:app --host 127.0.0.1 --port 8002
```

- **Local Web Interface URL:** `http://127.0.0.1:8002`
- **Stopping the Server:** Press `Ctrl + C` in the PowerShell terminal.

### 2.2 Web Interface Features
- **Branded Workplace UI:** Clear Northstar Technologies portal header with live session ID badge.
- **Turn Transcript:** Color-coded conversational message bubbles for both employee and assistant.
- **Domain Topic Badges:** Automatically tags responses with active domain (e.g. `[Leave & Attendance]`, `[Expense & Reimbursement]`, `[Employee Support]`).
- **Citation Badges:** Displays verifiable source citations in formatted pills at the bottom of substantive answers.
- **Ambiguity & Clarification Callouts:** Visually highlights clarification prompts when an inquiry is ambiguous.
- **Session Controls:** 
  - Click **New Session** to generate a fresh isolated session ID and reset conversation history.
  - Click **Clear** to wipe the visual transcript.
- **Quick Prompts:** Clickable pills for common policy questions (Leave allotments, Hotel spending caps, P1 SLAs, WFH rules).

---

## 3. REST API Endpoints

| Method | Endpoint | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Web Chat HTML Application | None | HTML page |
| `GET` | `/health` | Health Check | None | `{"status": "healthy", "service": "...", "version": "1.0.0"}` |
| `POST` | `/api/session` | Create new isolated session | None | `{"session_id": "nst_sess_...", "status": "created"}` |
| `POST` | `/api/chat` | Submit conversational turn | `{"session_id": "...", "message": "..."}` | `{"session_id": "...", "answer": "...", "citations": [...], "retrieved_sections": [...], "resolved_query": "...", "topic": "...", "follow_up_required": bool, "clarification_question": str\|null, "turn_index": int}` |
| `GET` | `/api/history/{id}` | Retrieve session turns | None | `{"session_id": "...", "turns": [...]}` |
| `POST` | `/api/reset/{id}` | Reset session history | None | `{"status": "reset", "session_id": "..."}` |

---

## 4. Multi-Turn Conversational Engine

### 4.1 Session Isolation & Bounded Memory
- Each client maintains an isolated session state in memory. No context leaks across different users or browser tabs.
- Bounded sliding window (`max_history_turns=20`) prevents memory bloat while preserving immediate multi-turn conversational context.
- Configurable session TTL expires inactive sessions gracefully.

### 4.2 Context & Pronoun Resolution
- **Anaphoric Pronoun Resolution:** Resolves conversational references (`those`, `that`, `it`, `who should I contact next?`, `does that include meals?`) by inspecting preceding turn entities:
  - *Turn 1:* "How many annual leave days are available?" $\rightarrow$ *Turn 2:* "How many of those can I carry over?" resolves to *"How many annual leave days or earned leave days can I carry over to the next year?"*.
  - *Turn 4:* "What is the Tier-1 hotel reimbursement limit?" $\rightarrow$ *Turn 5:* "Does that limit include meals?" resolves to *"Does the hotel accommodation reimbursement limit include meals and incidentals?"*.
- **Topic Switching:** Identifies transitions across domains (Leave, Expense, IT Support) and resets referents cleanly.
- **Ambiguity Guard:** Underspecified inputs (e.g., *"Tell me more"*, *"What else?"*) trigger an immediate clarification prompt rather than guessing or fabricating.

### 4.3 Anti-Repetition Phrasing
- Tracks document-scoped section keys (`f"{doc_name}:{sec_num}"`) already communicated in the active session.
- On follow-up questions referencing previously delivered sections, the assistant prefixes: `"Regarding your follow-up on Section X.Y..."` and directly provides the new details without re-dumping previously provided facts.

### 4.4 Grounding & Citation Enforcement
- **Strict Evidence Grounding:** Answers are synthesized exclusively from retrieved policy sections.
- **Unsupported Question Protection:** Out-of-domain questions (e.g. office pets, stock options) fail the evidence check and trigger:
  *"The Northstar Technologies knowledge base does not specify information regarding this query. Please reach out to the relevant internal department (People Operations at #help-hr-operations or IT Support at #help-it-support) for direct guidance."* with zero fabricated citations.
- **Mandatory Source Citations:** Every substantive answer concludes with an exact, verified source citation:
  `[Source: <filename>, Section <X.Y> — <Section Title>]`

---

## 5. Official 10-Turn Demonstration

The reproducible demonstration script is located at:
`q2_document_assistant/demo/run_10_turn_demo.py`

### 5.1 Running the Demonstration
```powershell
python -m q2_document_assistant.demo.run_10_turn_demo
```

### 5.2 Generated Transcript
The complete markdown dialogue transcript is persisted at:
[`q2_document_assistant/demo/10_turn_transcript.md`](./demo/10_turn_transcript.md)

### 5.3 Dialogue Summary Across All 10 Turns

| Turn | User Question | Active Domain | Key Grounded Policy Answer | Citation |
| :--- | :--- | :--- | :--- | :--- |
| **1** | How many annual leave days are available? | `leave_and_attendance` | 18 days EL, 12 days SL, 6 days CL, 26 weeks maternity, 15 days paternity | `[Source: leave_and_attendance_policy.md, Section 2.1 — Leave Categories and Annual Entitlements]` |
| **2** | How many of those can I carry over? | `leave_and_attendance` | Up to 12 unused EL days carried over; excess lapses on Dec 31; SL/CL do not carry over | `[Source: leave_and_attendance_policy.md, Section 2.1 — Leave Categories and Annual Entitlements]` |
| **3** | How much notice is needed for more than 3 days of leave? | `leave_and_attendance` | At least 14 calendar days advance notice for >3 consecutive days | `[Source: leave_and_attendance_policy.md, Section 2.3 — Request Process and Notice Periods]` |
| **4** | What is the Tier-1 hotel reimbursement limit? | `expense_and_reimbursement` | Up to ₹6,500 plus taxes per night in Tier-1 cities | `[Source: reimbursement_policy.md, Section 2.1 — Spending Limits and Daily Caps]` |
| **5** | Does that limit include meals? | `expense_and_reimbursement` | No, meals are separate (capped at ₹1,500/day Tier-1, ₹1,000 Tier-2, ₹750 Tier-3) | `[Source: reimbursement_policy.md, Section 2.1 — Spending Limits and Daily Caps]` |
| **6** | Who approves an expense report above ₹1,00,000? | `expense_and_reimbursement` | Reporting Manager, Department Head (Director), and Corporate Controller / CFO | `[Source: reimbursement_policy.md, Section 3.2 — Approval Hierarchies]` |
| **7** | What are the P1 IT support response times? | `employee_support` | Initial acknowledgment within 15 mins; resolution under 2 hours | `[Source: employee_support_policy.md, Section 1.3 — Service Level Agreements (SLA) and Response Times]` |
| **8** | How can I contact IT support? | `employee_support` | ServiceHub portal (`https://servicehub.northstar.internal`), Slack `#help-it-support`, helpline `ext. 4400` | `[Source: employee_support_policy.md, Section 1.1 — Support Channels]` |
| **9** | Going back to our earlier leave discussion, what happens if my manager does not approve my request? | `leave_and_attendance` | Manager has 48h SLA; auto-escalates to skip-level; auto-approved after additional 24h | `[Source: leave_and_attendance_policy.md, Section 2.4 — Managerial Approval Workflow]` |
| **10** | Are pets allowed in the office? | `leave_and_attendance` | Out of domain: knowledge base does not specify; directs user to People Operations | *(None — unsupported inquiry)* |

---

## 6. Testing & Validation

### 6.1 Running Q2 Unit & API Tests
```powershell
python -m pytest q2_document_assistant/tests -v
```
Output:
```text
47 passed in 4.84s
```

### 6.2 Running Full Workspace Test Suite (Q1, Q2, Q3)
```powershell
python -m pytest -q
```
Output:
```text
98 passed in 142.85s (0:02:22)
```
*(All 24 Q1 tests + 27 Q3 tests + 47 Q2 tests = 98 passing tests).*

---

## 7. Known Limitations & Operating Assumptions

1. **Knowledge Base Scope:** The assistant is grounded exclusively in the three official Northstar Technologies policy documents (`employee_support_policy.md`, `leave_and_attendance_policy.md`, `reimbursement_policy.md`). Policy matters outside these domains (e.g. employee equity, building security, pets) are explicitly flagged as unsupported.
2. **Session Storage:** Active conversation history is maintained in-memory within the running application process. Restarting the server resets active sessions.
3. **Deterministic Offline Operation:** When `GEMINI_API_KEY` is unavailable or denied, the engine utilizes the 1024-dimensional local deterministic feature vectorizer and rule-based grounded synthesizer, ensuring 100% test reproducibility and zero reliance on external network calls.
