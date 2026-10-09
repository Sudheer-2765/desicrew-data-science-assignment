# Question 1: Excel Inventory Analysis Agent

## Purpose
An intelligent data-assistant agent built to analyze and query the supplied `Inventory-Records-Sample-Data.xlsx` dataset. The agent can dynamically write and execute Pandas code to perform calculations, filter rows, sort products, and reconcile discrepancies. When users inquire about inventory terminology, business metrics, or operational context, the agent invokes an inventory domain search tool and synthesizes findings into concise, plain-English summaries.

---

## Architecture

The project is structured into modular components:

```
q1_excel_agent/
├── input/
│   └── Inventory-Records-Sample-Data.xlsx   # Supplied sample inventory workbook
├── data_loader.py                           # Workbook loader, header normalizer, and data quality inspector
├── query_engine.py                          # Controlled Python/Pandas query execution engine with security sandboxing
├── search_tool.py                           # Inventory management domain glossary and search tool
├── gemini_client.py                         # Reusable Google GenAI client factory and key loader
├── agent.py                                 # Core ExcelInventoryAgent orchestrator and function-calling loop
├── requirements.txt                         # Minimal dependencies (pandas, openpyxl, google-genai, python-dotenv, pytest)
├── tests/
│   ├── test_foundation.py                   # Tests for dataset loading, inspection, and Pandas query execution (9 tests)
│   └── test_agent.py                        # Tests for agent initialization, tools, mock LLM flows, and security (9 tests)
└── README.md                                # System documentation and usage guide
```

---

## Setup & Installation

### 1. Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`:
  ```bash
  pip install -r q1_excel_agent/requirements.txt
  ```

### 2. Environment Variable Configuration
The agent utilizes the current official Google GenAI Python SDK (`google-genai`). Configure your API key as an environment variable or place it inside a `.env` file at the project root:

**PowerShell (Windows):**
```powershell
$env:GEMINI_API_KEY="your-gemini-api-key-here"
```

**Bash / Linux / macOS:**
```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

*(Optional: Set `GEMINI_MODEL="gemini-2.5-flash"` to configure a specific model).*

> [!NOTE]
> Never commit API keys or credentials to version control. The client gracefully reports configuration issues without leaking secrets or crashing.

### 3. Running the Chat Interfaces

You can interact with the agent via either the **Terminal CLI** or the **Web Interface**:

#### Option A: Terminal CLI Chat Interface
```bash
python -m q1_excel_agent.cli_chat
```
- Interactive chat in the terminal.
- Commands: `/sample` for suggested questions, `/info` for dataset metrics, `/exit` to quit.
- Shows Plain-English answers and badges for tools used.

#### Option B: Lightweight Web Chat Interface
```bash
python -m q1_excel_agent.web_chat
```
- Starts a local web server at `http://127.0.0.1:8000`.
- Includes preset question pills, clean message bubbles, and tool activity badges.

---

## How the Agent Works

1. **User Question Ingestion:** The user submits a natural-language query to `ExcelInventoryAgent.ask(question)`.
2. **Intent & Tool Selection:**
   - **Data Questions:** The agent invokes `execute_data_query(code)` which runs Python/Pandas operations against the loaded DataFrame `df`.
   - **Terminology / Context Questions:** The agent invokes `search_inventory_context(query)` to retrieve operational definitions, accounting formulas, or industry standards.
   - **Combined Questions:** The agent chains both tools in a multi-turn tool calling loop.
3. **Execution & Sandboxing:** Code is executed in an isolated namespace containing `df`, `pd`, and `np`. Unsafe built-ins (e.g., file writes, OS access, network sockets) are blocked.
4. **Plain English Synthesis:** Gemini synthesizes the tool results into a clear, direct explanation. Hidden chain-of-thought tokens are stripped, returning only the final answer and metadata about tools used.

---

## Example Questions Handled

- **Data Analysis & Aggregation:**
  - *"Which product has the highest units sold?"* &rarr; Identifies the top-selling product and exact units.
  - *"What is the total inventory value?"* &rarr; Sums `Cost Price Total (USD)` across all products ($359,760).
  - *"Which product has the highest inventory value and what is that value?"* &rarr; Sorts by total cost and extracts product details.
- **Data Quality & Reconciliation:**
  - *"Which products have stock reconciliation discrepancies?"* &rarr; Compares `Hand-In-Stock` against `Opening Stock + Purchase - Units Sold` and lists the 12 anomalous products.
  - *"Explain the inventory stock discrepancy in simple terms."* &rarr; Explains why physical counts differ from formulaic stock and details common real-world causes (shrinkage, unrecorded wastage).
- **Terminology & Domain Concepts:**
  - *"What does safety stock mean?"* &rarr; Explains buffer inventory purpose and calculation formula.
  - *"What is EOQ?"* &rarr; Details the Economic Order Quantity formula and cost trade-offs.
  - *"What does inventory turnover mean?"* &rarr; Explains COGS / Average Inventory and financial significance.

---

## Running Tests

Run the complete test suite (18 unit tests):
```bash
python -m pytest q1_excel_agent/tests -v
```

All tests run deterministically and fast without consuming paid API credits by utilizing mocked LLM flows for the agent and direct assertion suites for the foundation and tools.

---

## Known Limitations

1. **Header Offsets in Excel:** The original Excel sheet has 5 title/banner rows and an empty Column 0. The loader specifically offsets to header row 5. Other Excel files with different structures would require specifying the header index.
2. **12 Discrepant Inventory Rows:** The dataset contains 12 products where recorded `Hand-In-Stock` does not match the arithmetic sum of purchases and sales. The agent detects and reports these, but cannot alter the source file.
3. **Tool Call Limit:** The function-calling loop enforces a maximum limit of 5 tool turns per question to safeguard against infinite LLM recursion.

