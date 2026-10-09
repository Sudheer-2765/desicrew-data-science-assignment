"""Tests for Q1 Chat Interfaces (Web and CLI)."""

import pytest
from fastapi.testclient import TestClient
from q1_excel_agent.web_chat import app
from q1_excel_agent.cli_chat import SAMPLE_QUESTIONS


@pytest.fixture(scope="module")
def web_client():
    return TestClient(app)


def test_web_chat_index(web_client):
    """Verify web UI HTML page loads with 200 status."""
    response = web_client.get("/")
    assert response.status_code == 200
    assert "Excel Inventory Assistant" in response.text
    assert "chat-window" in response.text


def test_web_chat_info_api(web_client):
    """Verify info API returns correct dataset metrics."""
    response = web_client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert data["row_count"] == 46
    assert data["column_count"] == 8
    assert data["total_valuation"] == 359760
    assert data["anomalies"] == 12


def test_web_chat_query_api_data(web_client):
    """Verify web chat handles inventory data query."""
    response = web_client.post("/api/chat", json={"message": "What is the total inventory value?"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "$359,760" in data["answer"]
    assert len(data["tools_used"]) >= 1


def test_web_chat_query_api_search(web_client):
    """Verify web chat handles terminology search query."""
    response = web_client.post("/api/chat", json={"message": "What is safety stock?"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Safety Stock" in data["answer"] or "buffer" in data["answer"].lower()


def test_web_chat_empty_query(web_client):
    """Verify empty query returns 400 error."""
    response = web_client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400


def test_sample_questions_list():
    """Verify CLI sample questions list contains all core prompt requirements."""
    assert len(SAMPLE_QUESTIONS) >= 5
    joined = " ".join(SAMPLE_QUESTIONS).lower()
    assert "highest units sold" in joined
    assert "total inventory value" in joined
    assert "safety stock" in joined
    assert "discrepancies" in joined

