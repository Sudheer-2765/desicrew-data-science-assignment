"""Tests for Q1 Gemini Agent, tools, and orchestration."""

from unittest.mock import MagicMock
import pytest
from q1_excel_agent.gemini_client import get_api_key, create_gemini_client
from q1_excel_agent.search_tool import search_inventory_context
from q1_excel_agent.agent import ExcelInventoryAgent, _clean_response_text


def test_gemini_client_missing_key(monkeypatch):
    """Verify clean ValueError without secret leakage when API key is missing."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError) as excinfo:
        get_api_key(None)
    assert "GEMINI_API_KEY is not set" in str(excinfo.value)


def test_search_tool_glossary_lookups():
    """Verify search tool handles representative inventory domain questions."""
    # Safety stock
    res_safety = search_inventory_context("What is safety stock?")
    assert res_safety["found"] is True
    assert "buffer" in res_safety["definition"].lower()

    # Inventory turnover
    res_turnover = search_inventory_context("What does inventory turnover mean?")
    assert res_turnover["found"] is True
    assert "Cost of Goods Sold" in res_turnover["definition"]

    # EOQ
    res_eoq = search_inventory_context("What is EOQ?")
    assert res_eoq["found"] is True
    assert "Economic Order Quantity" in res_eoq["term"]

    # Stock discrepancy / reconciliation
    res_discrepancy = search_inventory_context("Explain inventory stock discrepancy")
    assert res_discrepancy["found"] is True
    assert "discrepancy" in res_discrepancy["definition"].lower()

    # Unrecognized query
    res_unknown = search_inventory_context("Quantum computing algorithms")
    assert res_unknown["found"] is False


def test_agent_initialization():
    """Verify ExcelInventoryAgent initializes properly with DataFrame loaded."""
    agent = ExcelInventoryAgent()
    assert agent.df is not None
    assert len(agent.df) == 46
    assert agent.model_name is not None


def test_agent_missing_api_key_graceful_handling(monkeypatch):
    """Verify agent returns user-facing response when API key is missing without crashing."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    agent = ExcelInventoryAgent(api_key=None)
    resp = agent.ask("What is the total inventory value?")
    assert resp.success is False
    assert "GEMINI_API_KEY is not configured" in resp.answer
    assert resp.error is not None


def test_agent_empty_question():
    """Verify agent rejects empty questions gracefully."""
    agent = ExcelInventoryAgent()
    resp = agent.ask("   ")
    assert resp.success is False
    assert "valid question" in resp.answer.lower()


def test_clean_response_text_removes_thought():
    """Verify hidden thought reasoning parts are excluded from final output."""
    mock_part_thought = MagicMock()
    mock_part_thought.thought = True
    mock_part_thought.text = "Internal hidden reasoning"

    mock_part_text = MagicMock()
    mock_part_text.thought = False
    mock_part_text.text = "The total value of inventory is $359,760."

    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part_thought, mock_part_text]

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    clean = _clean_response_text(mock_response)
    assert clean == "The total value of inventory is $359,760."
    assert "hidden" not in clean


def test_mock_agent_data_query_flow():
    """Verify agent orchestrates data query tool and plain-English answer."""
    # 1. First model call: requests function call 'execute_data_query'
    mock_call = MagicMock()
    mock_call.name = "execute_data_query"
    mock_call.args = {"code": "df.sort_values(by='Number of Units Sold', ascending=False).iloc[0]['Product Name']"}

    resp1 = MagicMock()
    resp1.function_calls = [mock_call]

    # 2. Second model call after tool output: produces final text
    resp2 = MagicMock()
    resp2.function_calls = []
    resp2.candidates = [
        MagicMock(content=MagicMock(parts=[
            MagicMock(thought=False, text="The product with the highest units sold is the Wireless Mouse with 25 units sold.")
        ]))
    ]

    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = [resp1, resp2]

    mock_client = MagicMock()
    mock_client.chats.create.return_value = mock_chat

    agent = ExcelInventoryAgent(client=mock_client)
    resp = agent.ask("Which product has the highest units sold?")

    assert resp.success is True
    assert "Wireless Mouse" in resp.answer
    assert len(resp.tools_used) == 1
    assert resp.tools_used[0]["tool"] == "execute_data_query"
    assert resp.tools_used[0]["success"] is True


def test_mock_agent_search_tool_flow():
    """Verify agent orchestrates glossary search tool and plain-English synthesis."""
    mock_call = MagicMock()
    mock_call.name = "search_inventory_context"
    mock_call.args = {"query": "safety stock"}

    resp1 = MagicMock()
    resp1.function_calls = [mock_call]

    resp2 = MagicMock()
    resp2.function_calls = []
    resp2.candidates = [
        MagicMock(content=MagicMock(parts=[
            MagicMock(thought=False, text="Safety stock is a buffer quantity held to protect against sudden surges in demand.")
        ]))
    ]

    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = [resp1, resp2]

    mock_client = MagicMock()
    mock_client.chats.create.return_value = mock_chat

    agent = ExcelInventoryAgent(client=mock_client)
    resp = agent.ask("What does safety stock mean?")

    assert resp.success is True
    assert "Safety stock" in resp.answer
    assert len(resp.tools_used) == 1
    assert resp.tools_used[0]["tool"] == "search_inventory_context"
    assert resp.tools_used[0]["success"] is True


def test_mock_agent_combined_flow():
    """Verify agent handles combined queries calling both search and data tools."""
    call_search = MagicMock()
    call_search.name = "search_inventory_context"
    call_search.args = {"query": "stock discrepancy"}

    resp1 = MagicMock()
    resp1.function_calls = [call_search]

    call_query = MagicMock()
    call_query.name = "execute_data_query"
    call_query.args = {"code": "len(df[df['Hand-In-Stock'] != (df['Opening Stock'] + df['Purchase/Stock in'] - df['Number of Units Sold'])])"}

    resp2 = MagicMock()
    resp2.function_calls = [call_query]

    resp3 = MagicMock()
    resp3.function_calls = []
    resp3.candidates = [
        MagicMock(content=MagicMock(parts=[
            MagicMock(thought=False, text="A stock discrepancy occurs when recorded inventory differs from formula expectations. In our dataset, 12 products exhibit discrepancies.")
        ]))
    ]

    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = [resp1, resp2, resp3]

    mock_client = MagicMock()
    mock_client.chats.create.return_value = mock_chat

    agent = ExcelInventoryAgent(client=mock_client)
    resp = agent.ask("Explain the inventory stock discrepancy in simple terms and tell me how many products have it.")

    assert resp.success is True
    assert "12 products" in resp.answer
    assert len(resp.tools_used) == 2
    tool_names = [t["tool"] for t in resp.tools_used]
    assert "search_inventory_context" in tool_names
    assert "execute_data_query" in tool_names

