"""
Unit tests for Q2.2 Knowledge Base Indexer and Retrieval System.
Tests run completely offline and deterministically without requiring a live Gemini API key.
"""

from pathlib import Path
import tempfile
import numpy as np
import pytest

from q2_document_assistant.src.chunker import chunk_document, chunk_documents
from q2_document_assistant.src.document_loader import load_document, load_documents
from q2_document_assistant.src.embeddings import (
    BaseEmbeddingProvider,
    HybridEmbeddingProvider,
    LocalDeterministicEmbeddingProvider,
    get_embedding_provider,
)
from q2_document_assistant.src.indexer import DocumentIndexer
from q2_document_assistant.src.models import Chunk, Document, RetrievalResult
from q2_document_assistant.src.retriever import DocumentRetriever, retrieve


@pytest.fixture
def local_provider():
    """Provides a deterministic local embedding provider for fast offline testing."""
    return LocalDeterministicEmbeddingProvider(dimension=1024)


@pytest.fixture
def test_retriever(local_provider):
    """Provides a DocumentRetriever instance using the local embedding provider."""
    return DocumentRetriever(embedding_provider=local_provider)


# 1. Document Loading Tests
def test_load_all_three_documents():
    docs = load_documents()
    assert len(docs) == 3
    filenames = {d.filename for d in docs}
    assert filenames == {
        "employee_support_policy.md",
        "leave_and_attendance_policy.md",
        "reimbursement_policy.md",
    }
    for doc in docs:
        assert doc.title
        assert len(doc.content) > 500
        assert doc.source.endswith(doc.filename)


# 2. Expected Sections Detection
def test_expected_sections_detected():
    docs = load_documents()
    chunks = chunk_documents(docs, include_preamble=False)

    doc_chunks = {}
    for c in chunks:
        doc_chunks.setdefault(c.document, []).append(c)

    # employee_support_policy has 7 sections
    emp_sections = [c.section_number for c in doc_chunks["employee_support_policy.md"]]
    assert emp_sections == ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4"]

    # leave_and_attendance_policy has 10 sections
    leave_sections = [c.section_number for c in doc_chunks["leave_and_attendance_policy.md"]]
    assert leave_sections == ["1.1", "1.2", "2.1", "2.2", "2.3", "2.4", "3.1", "3.2", "3.3", "4.1"]

    # reimbursement_policy has 9 sections
    reimb_sections = [c.section_number for c in doc_chunks["reimbursement_policy.md"]]
    assert reimb_sections == ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "3.3", "4.1", "4.2"]

    # Total numbered sections across all 3 docs is 26
    assert len(chunks) == 26


# 3. Metadata Preservation
def test_metadata_preservation():
    docs = load_documents()
    chunks = chunk_documents(docs, include_preamble=True)

    for c in chunks:
        assert c.document in [
            "employee_support_policy.md",
            "leave_and_attendance_policy.md",
            "reimbursement_policy.md",
        ]
        assert c.section_number
        assert c.section_title
        assert c.source
        assert c.text
        # Citation format test
        assert c.citation.startswith(f"[Source: {c.document}, Section {c.section_number}")


# 4. Local Deterministic Embeddings
def test_local_deterministic_embeddings(local_provider):
    vec = local_provider.embed_text("Test query for leave policy")
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (1024,)
    # Norm must be approximately 1.0 (L2 normalized)
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-4

    # Determinism: same input produces exact same output
    vec2 = local_provider.embed_text("Test query for leave policy")
    assert np.allclose(vec, vec2)

    # Batch embedding shape
    batch_vecs = local_provider.embed_batch(["text one", "text two", "text three"])
    assert batch_vecs.shape == (3, 1024)


# 5. Embedding Fallback When Remote Fails
def test_embedding_fallback_on_failure():
    class FailingProvider(BaseEmbeddingProvider):
        @property
        def dimension(self) -> int:
            return 768

        @property
        def name(self) -> str:
            return "failing_mock"

        def embed_text(self, text: str) -> np.ndarray:
            raise ConnectionError("Simulated API failure or quota exhaustion")

    hybrid = HybridEmbeddingProvider(preferred=FailingProvider())
    # Should seamlessly catch the failure, log a warning, and fall back to local
    vec = hybrid.embed_text("Sample query after remote failure")
    assert isinstance(vec, np.ndarray)
    assert hybrid.is_using_fallback is True
    assert vec.shape == (1024,)


# 6. Index Creation
def test_index_can_be_created(tmp_path, local_provider):
    indexer = DocumentIndexer(index_dir=tmp_path, embedding_provider=local_provider)
    meta = indexer.build_index()

    assert (tmp_path / "chunks.json").is_file()
    assert (tmp_path / "embeddings.npy").is_file()
    assert (tmp_path / "index_meta.json").is_file()

    assert meta["chunk_count"] > 0
    assert meta["document_count"] == 3


# 7. Index Loading
def test_index_can_be_loaded(tmp_path, local_provider):
    indexer = DocumentIndexer(index_dir=tmp_path, embedding_provider=local_provider)
    indexer.build_index()

    chunks, embeddings, meta = indexer.load_index()
    assert len(chunks) == meta["chunk_count"]
    assert embeddings.shape[0] == len(chunks)
    assert embeddings.shape[1] == local_provider.dimension
    assert meta["document_count"] == 3


# 8. Retrieval Returns Results
def test_retrieval_returns_ranked_results(test_retriever):
    results = test_retriever.retrieve("What is the reimbursement limit?", top_k=3)
    assert len(results) == 3
    for r in results:
        assert isinstance(r, RetrievalResult)
        assert 0.0 <= r.relevance_score <= 1.0
        assert r.document
        assert r.section_number
        assert r.section_title
        assert r.text


# 9. Relevant Document and Section Retrieval
@pytest.mark.parametrize(
    "query, expected_doc, expected_section",
    [
        ("How many annual leave days are available?", "leave_and_attendance_policy.md", "2.1"),
        ("How much notice is required for more than 3 days of leave?", "leave_and_attendance_policy.md", "2.3"),
        ("What is the Tier-1 hotel reimbursement limit?", "reimbursement_policy.md", "2.1"),
        ("What is the P1 response time?", "employee_support_policy.md", "1.3"),
        ("Who approves expenses above 1 lakh?", "reimbursement_policy.md", "3.2"),
        ("Can I work from home?", "leave_and_attendance_policy.md", "3.2"),
        ("What happens if my manager does not approve my leave?", "leave_and_attendance_policy.md", "2.4"),
        ("What documents are required for reimbursement?", "reimbursement_policy.md", "2.2"),
    ],
)
def test_relevant_document_and_section_retrieved(test_retriever, query, expected_doc, expected_section):
    results = test_retriever.retrieve(query, top_k=1)
    assert len(results) >= 1
    top = results[0]
    assert top.document == expected_doc
    assert top.section_number == expected_section


# 10. Citation Metadata Preserved
def test_citation_metadata_preserved(test_retriever):
    results = test_retriever.retrieve("What is the Tier-1 hotel reimbursement limit?", top_k=1)
    top = results[0]
    expected_citation = "[Source: reimbursement_policy.md, Section 2.1 — Spending Limits and Daily Caps]"
    assert top.citation == expected_citation
    assert top.document == "reimbursement_policy.md"
    assert top.section_number == "2.1"
    assert top.section_title == "Spending Limits and Daily Caps"


# 11. Multi-Document Topic Handling
def test_multi_document_topic_coverage(test_retriever):
    queries = {
        "employee_support_policy.md": "What are the IT helpdesk operating hours and SLAs?",
        "leave_and_attendance_policy.md": "What is the policy for medical leave and doctor certificate?",
        "reimbursement_policy.md": "What is the mileage rate for personal four wheeler car?",
    }
    for expected_doc, q in queries.items():
        results = test_retriever.retrieve(q, top_k=1)
        assert results[0].document == expected_doc


# 12. Convenience retrieve() Function
def test_convenience_retrieve_function():
    results = retrieve("How many annual leave days are available?", top_k=1)
    assert len(results) == 1
    assert results[0].document == "leave_and_attendance_policy.md"
    assert results[0].section_number in ["2.1", "2.2"]
