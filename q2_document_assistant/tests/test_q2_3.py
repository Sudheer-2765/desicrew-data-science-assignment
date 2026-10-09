"""
Unit tests for Q2.3 Multi-Turn Conversational Engine.
Tests cover session creation, isolation, bounded memory, follow-up resolution,
topic switching, anti-repetition, mandatory citations, unsupported inquiries,
and ambiguous query handling.
All tests run 100% deterministically and offline without requiring a live Gemini API key.
"""

import time
import pytest

from q2_document_assistant.src.conversation import DocumentSupportAssistant
from q2_document_assistant.src.embeddings import LocalDeterministicEmbeddingProvider
from q2_document_assistant.src.memory import (
    SessionExpiredError,
    SessionMemoryManager,
    SessionNotFoundError,
)
from q2_document_assistant.src.models import AssistantResponse, ConversationTurn
from q2_document_assistant.src.retriever import DocumentRetriever


@pytest.fixture
def local_retriever():
    """Provides a fast, deterministic offline retriever."""
    provider = LocalDeterministicEmbeddingProvider(dimension=1024)
    return DocumentRetriever(embedding_provider=provider)


@pytest.fixture
def assistant(local_retriever):
    """Provides a DocumentSupportAssistant with deterministic components."""
    memory = SessionMemoryManager(max_history_turns=10)
    return DocumentSupportAssistant(retriever=local_retriever, memory_manager=memory)


# 1. Session Creation
def test_create_session(assistant):
    session_id = assistant.create_session()
    assert session_id.startswith("nst_sess_")
    history = assistant.get_history(session_id)
    assert len(history) == 0


# 2. Remembering Prior Turns
def test_remember_prior_turns(assistant):
    sid = assistant.create_session()
    resp1 = assistant.chat(sid, "How many annual leave days are available?")
    assert resp1.turn_index == 0
    assert "18 business days" in resp1.answer

    resp2 = assistant.chat(sid, "How many of those can I carry over?")
    assert resp2.turn_index == 1
    assert "12" in resp2.answer

    history = assistant.get_history(sid)
    assert len(history) == 2
    assert history[0].user_message == "How many annual leave days are available?"
    assert history[1].user_message == "How many of those can I carry over?"


# 3. Session Isolation
def test_session_isolation(assistant):
    s1 = assistant.create_session()
    s2 = assistant.create_session()

    assistant.chat(s1, "How many annual leave days are available?")
    assistant.chat(s2, "What is the Tier-1 hotel reimbursement limit?")

    hist1 = assistant.get_history(s1)
    hist2 = assistant.get_history(s2)

    assert len(hist1) == 1
    assert len(hist2) == 1
    assert "leave" in hist1[0].user_message
    assert "hotel" in hist2[0].user_message


# 4. Follow-Up Pronoun & Anaphora Resolution
def test_follow_up_pronoun_resolution(assistant):
    sid = assistant.create_session()

    assistant.chat(sid, "What is the Tier-1 hotel reimbursement limit?")
    resp2 = assistant.chat(sid, "Does that include meals?")

    assert "hotel" in resp2.resolved_query.lower()
    assert "meal" in resp2.resolved_query.lower()
    assert "No" in resp2.answer or "do not include meals" in resp2.answer
    assert "1,500" in resp2.answer or "1500" in resp2.answer


# 5. Anti-Repetition Phrasing
def test_anti_repetition_phrasing(assistant):
    sid = assistant.create_session()

    # Turn 1: Inquire about leave allotments (Section 2.1)
    resp1 = assistant.chat(sid, "How many annual leave days are available?")
    assert "18 business days" in resp1.answer
    assert "Section 2.1" in resp1.answer

    # Turn 2: Follow-up on carryover
    resp2 = assistant.chat(sid, "How many of those can I carry over?")
    # Must directly answer carry-over without repeating the 18/12/6 baseline breakdown
    assert "12" in resp2.answer
    assert "Regarding your follow-up" in resp2.answer


# 6. Topic Switching Across Domains
def test_topic_switching(assistant):
    sid = assistant.create_session()

    # Domain 1: Leave
    r1 = assistant.chat(sid, "How many annual leave days are available?")
    assert r1.topic == "leave_and_attendance"

    # Domain 2: Expense reimbursement
    r2 = assistant.chat(sid, "What is the Tier-1 hotel reimbursement limit?")
    assert r2.topic == "expense_and_reimbursement"
    assert "6,500" in r2.answer

    # Domain 3: IT Support
    r3 = assistant.chat(sid, "What is the P1 response time?")
    assert r3.topic == "employee_support"
    assert "15 minutes" in r3.answer


# 7. Returning to Previously Discussed Topic
def test_return_to_previous_topic(assistant):
    sid = assistant.create_session()

    assistant.chat(sid, "How many annual leave days are available?")
    assistant.chat(sid, "What is the Tier-1 hotel reimbursement limit?")
    assistant.chat(sid, "What is the P1 response time?")

    # Return to leave
    r4 = assistant.chat(sid, "Going back to leave, what happens if my manager does not approve my request?")
    assert r4.topic == "leave_and_attendance"
    assert "48 hours" in r4.answer
    assert "Section 2.4" in r4.answer


# 8. Mandatory Citations on All Substantive Answers
def test_mandatory_citations_present(assistant):
    sid = assistant.create_session()
    queries = [
        "How many annual leave days are available?",
        "What is the Tier-1 hotel reimbursement limit?",
        "What is the P1 response time?",
        "Who approves expenses above 1 lakh?",
    ]
    for q in queries:
        resp = assistant.chat(sid, q)
        assert len(resp.citations) >= 1
        assert "[Source:" in resp.citations[0]
        assert "Section" in resp.citations[0]
        assert resp.citations[0] in resp.answer


# 9. Citations Match Retrieved Metadata
def test_citations_match_retrieved_metadata(assistant):
    sid = assistant.create_session()
    resp = assistant.chat(sid, "Who approves expenses above 1 lakh?")

    assert "reimbursement_policy.md" in resp.citations[0]
    assert "3.2" in resp.citations[0]
    assert "Approval Hierarchies" in resp.citations[0]
    assert any("3.2" in sec for sec in resp.retrieved_sections)


# 10. Unsupported Questions Handling
def test_unsupported_questions(assistant):
    sid = assistant.create_session()
    resp = assistant.chat(sid, "Can I bring my pet iguana to work in the office?")

    assert "does not specify" in resp.answer.lower()
    assert len(resp.citations) == 0


# 11. Ambiguous Follow-Ups Trigger Clarification
def test_ambiguous_queries_trigger_clarification(assistant):
    sid = assistant.create_session()
    resp = assistant.chat(sid, "Tell me more")

    assert resp.follow_up_required is True
    assert resp.clarification_question is not None
    assert "Could you please specify" in resp.answer


# 12. Expired or Unknown Session Handling
def test_unknown_session_error(assistant):
    with pytest.raises(SessionNotFoundError):
        assistant.chat("non_existent_session_123", "Hello")


def test_expired_session_error():
    # TTL of 0.6 seconds
    memory = SessionMemoryManager(max_history_turns=5, ttl_seconds=0.6)
    assistant = DocumentSupportAssistant(memory_manager=memory)
    sid = assistant.create_session()
    assistant.chat(sid, "How many annual leave days are available?")

    # Wait for expiry
    time.sleep(0.7)
    with pytest.raises(SessionExpiredError):
        assistant.chat(sid, "How many can I carry over?")


# 13. Bounded Conversation History
def test_bounded_conversation_history():
    memory = SessionMemoryManager(max_history_turns=3)
    assistant = DocumentSupportAssistant(memory_manager=memory)
    sid = assistant.create_session()

    assistant.chat(sid, "How many annual leave days are available?")
    assistant.chat(sid, "How many can I carry over?")
    assistant.chat(sid, "What is the Tier-1 hotel reimbursement limit?")
    assistant.chat(sid, "What is the P1 response time?")

    history = assistant.get_history(sid)
    # Memory must be capped at 3 turns
    assert len(history) == 3
    assert history[0].user_message == "How many can I carry over?"
    assert history[-1].user_message == "What is the P1 response time?"


# 14. Local Deterministic Operation (No Network/API Key Required)
def test_local_deterministic_offline_operation(assistant, monkeypatch):
    # Strip any possible API keys from environment
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    sid = assistant.create_session()
    resp = assistant.chat(sid, "What is the Tier-1 hotel reimbursement limit?")
    assert "6,500" in resp.answer
    assert len(resp.citations) >= 1
