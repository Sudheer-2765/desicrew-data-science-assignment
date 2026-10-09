"""
Unit and API integration tests for Q2.4 Web Chat Interface and REST API.
Tests cover health, session creation, chat endpoints, history, reset, validation,
error handling, and deterministic offline operation.
"""

from fastapi.testclient import TestClient
import pytest

from q2_document_assistant.src.web_chat import app

client = TestClient(app)


# 1. Health Endpoint
def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "northstar_document_assistant"


# 2. Frontend Chat Page Availability
def test_root_chat_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Northstar Technologies" in res.text
    assert "Document Support Assistant" in res.text


# 3. Session Creation API
def test_session_creation_api():
    res = client.post("/api/session")
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert data["session_id"].startswith("nst_sess_")
    assert data["status"] == "created"


# 4. Chat Endpoint — Basic Policy Turn
def test_chat_endpoint_valid_turn():
    sess_res = client.post("/api/session")
    sid = sess_res.json()["session_id"]

    res = client.post("/api/chat", json={
        "session_id": sid,
        "message": "How many annual leave days are available?"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == sid
    assert data["turn_index"] == 0
    assert "18 business days" in data["answer"]
    assert data["topic"] == "leave_and_attendance"
    assert len(data["citations"]) >= 1
    assert "leave_and_attendance_policy.md" in data["citations"][0]


# 5. Multiple Messages in One Session with Follow-Up Resolution
def test_multiple_messages_in_session():
    sess_res = client.post("/api/session")
    sid = sess_res.json()["session_id"]

    # Turn 1
    res1 = client.post("/api/chat", json={
        "session_id": sid,
        "message": "What is the Tier-1 hotel reimbursement limit?"
    })
    assert res1.status_code == 200
    assert "6,500" in res1.json()["answer"]
    assert res1.json()["turn_index"] == 0

    # Turn 2: Follow-up on meals
    res2 = client.post("/api/chat", json={
        "session_id": sid,
        "message": "Does that limit include meals?"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["turn_index"] == 1
    assert "hotel" in data2["resolved_query"].lower()
    assert "No" in data2["answer"] or "do not include" in data2["answer"]
    assert "1,500" in data2["answer"]


# 6. Session Isolation Across Different Users
def test_session_isolation_api():
    s1 = client.post("/api/session").json()["session_id"]
    s2 = client.post("/api/session").json()["session_id"]

    client.post("/api/chat", json={"session_id": s1, "message": "How many annual leave days are available?"})
    client.post("/api/chat", json={"session_id": s2, "message": "What is the P1 response time?"})

    h1 = client.get(f"/api/history/{s1}").json()["turns"]
    h2 = client.get(f"/api/history/{s2}").json()["turns"]

    assert len(h1) == 1
    assert len(h2) == 1
    assert "leave" in h1[0]["user_message"]
    assert "p1" in h2[0]["user_message"].lower()


# 7. Session History Endpoint
def test_session_history_endpoint():
    sid = client.post("/api/session").json()["session_id"]
    client.post("/api/chat", json={"session_id": sid, "message": "What is the P1 response time?"})

    res = client.get(f"/api/history/{sid}")
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == sid
    assert len(data["turns"]) == 1
    assert "15 minutes" in data["turns"][0]["assistant_response"]


# 8. Session Reset Endpoint
def test_session_reset_endpoint():
    sid = client.post("/api/session").json()["session_id"]
    client.post("/api/chat", json={"session_id": sid, "message": "What is the P1 response time?"})

    reset_res = client.post(f"/api/reset/{sid}")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "reset"

    h = client.get(f"/api/history/{sid}").json()["turns"]
    assert len(h) == 0


# 9. Request Validation on Empty Message
def test_chat_validation_empty_message():
    sid = client.post("/api/session").json()["session_id"]
    res = client.post("/api/chat", json={"session_id": sid, "message": "   "})
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"]


# 10. Error Handling on Unknown Session
def test_chat_unknown_session():
    res = client.post("/api/chat", json={"session_id": "non_existent_sid_999", "message": "Hello"})
    assert res.status_code == 404
    assert "Session not found" in res.json()["detail"]


# 11. Unsupported Query API Behavior
def test_unsupported_query_api():
    sid = client.post("/api/session").json()["session_id"]
    res = client.post("/api/chat", json={"session_id": sid, "message": "Are pets allowed in the office?"})
    assert res.status_code == 200
    data = res.json()
    assert "does not specify" in data["answer"].lower()
    assert len(data["citations"]) == 0


# 12. Ambiguous Query Triggering Clarification
def test_ambiguous_query_api():
    sid = client.post("/api/session").json()["session_id"]
    res = client.post("/api/chat", json={"session_id": sid, "message": "Tell me more"})
    assert res.status_code == 200
    data = res.json()
    assert data["follow_up_required"] is True
    assert data["clarification_question"] is not None
    assert "Could you please specify" in data["answer"]


# 13. Deterministic Offline Operation Without API Key
def test_offline_operation_without_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    sid = client.post("/api/session").json()["session_id"]
    res = client.post("/api/chat", json={"session_id": sid, "message": "How much notice is needed for more than 3 days of leave?"})
    assert res.status_code == 200
    data = res.json()
    assert "14 calendar days" in data["answer"]
    assert len(data["citations"]) >= 1

