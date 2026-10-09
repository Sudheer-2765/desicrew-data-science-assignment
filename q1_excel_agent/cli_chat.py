"""Interactive CLI Chat Interface for Q1 Excel Inventory Agent."""

import sys
from q1_excel_agent.agent import ExcelInventoryAgent
from q1_excel_agent.data_loader import inspect_dataset


SAMPLE_QUESTIONS = [
    "Which product has the highest units sold?",
    "What is the total inventory value?",
    "Which products have stock reconciliation discrepancies?",
    "What does safety stock mean?",
    "What is EOQ?",
    "Which product has the highest inventory value and what is that value?",
    "What does inventory turnover mean?",
]


def print_banner(agent: ExcelInventoryAgent):
    metadata = inspect_dataset(agent.df)
    print("=" * 72)
    print("   DESICREW DATA SCIENCE INTERNSHIP - QUESTION 1 EXCEL AGENT")
    print("=" * 72)
    print(f" Dataset Loaded: {metadata['sheet_name']}")
    print(f" Products: {metadata['row_count']} items | Columns: {metadata['column_count']}")
    print(f" Total Inventory Valuation: ${metadata['summary_statistics']['total_inventory_valuation_usd']:,} USD")
    print(f" Reconciled Anomaly Count: {metadata['stock_formula_discrepancies_count']} items flagged")
    print("-" * 72)
    print(" Type your questions below. Commands: /help, /sample, /info, /exit")
    print("=" * 72)
    print()


def run_cli_chat():
    agent = ExcelInventoryAgent()
    print_banner(agent)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("/exit", "exit", "quit", ":q"):
                print("\nGoodbye!\n")
                break

            if user_input.lower() == "/help":
                print("\nCommands:")
                print("  /sample - Display suggested example questions")
                print("  /info   - Show dataset overview & statistics")
                print("  /exit   - Exit the chat interface")
                continue

            if user_input.lower() == "/sample":
                print("\nSample Questions to try:")
                for i, q in enumerate(SAMPLE_QUESTIONS, 1):
                    print(f"  {i}. {q}")
                continue

            if user_input.lower() == "/info":
                metadata = inspect_dataset(agent.df)
                print("\nDataset Overview:")
                print(f"  Total records: {metadata['row_count']}")
                print(f"  Columns: {', '.join(metadata['columns'])}")
                print(f"  Total inventory value: ${metadata['summary_statistics']['total_inventory_valuation_usd']:,} USD")
                print(f"  Total units on hand: {metadata['summary_statistics']['total_hand_in_stock_units']:,}")
                print(f"  Total units sold: {metadata['summary_statistics']['total_units_sold']:,}")
                continue

            # Query agent
            print("\nAgent thinking...", end="\r", flush=True)
            response = agent.ask(user_input)
            print(" " * 30, end="\r", flush=True)  # Clear thinking indicator

            print(f"\nAgent:\n{response.answer}\n")

            if response.tools_used:
                print("─" * 40)
                print("Tools Used:")
                for t in response.tools_used:
                    tool_name = t.get("tool", "unknown")
                    success_icon = "✓" if t.get("success", False) else "✗"
                    print(f"  {success_icon} [{tool_name}]")
                print("─" * 40)

        except (KeyboardInterrupt, EOFError):
            print("\nSession ended. Goodbye!\n")
            break


if __name__ == "__main__":
    run_cli_chat()

