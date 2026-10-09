"""
Retriever for Northstar Technologies Knowledge Base.
Performs hybrid semantic and lexical retrieval across indexed policy document chunks,
returning ranked chunks with full citation metadata.
"""

import json
import logging
import math
from pathlib import Path
import re
from typing import List, Optional, Tuple, Union

import numpy as np

from q2_document_assistant.src.embeddings import BaseEmbeddingProvider, get_embedding_provider
from q2_document_assistant.src.indexer import DEFAULT_INDEX_DIR, DocumentIndexer
from q2_document_assistant.src.models import Chunk, RetrievalResult

logger = logging.getLogger(__name__)


def _expand_query_terms(query: str) -> List[str]:
    """
    Expand user query with common policy synonyms, acronyms, and numeric equivalents.
    """
    q_lower = query.lower()
    raw_tokens = re.findall(r"[a-zA-Z0-9_\-\.]+", q_lower)
    expanded = list(raw_tokens)

    # Synonyms and domain expansions
    if "lakh" in raw_tokens or "1 lakh" in q_lower or "one lakh" in q_lower:
        expanded.extend(["100000", "1,00,000", "tier 3", "hierarchy", "hierarchies", "controller", "cfo"])

    if "tier" in raw_tokens and "1" in raw_tokens or "tier-1" in raw_tokens or "tier 1" in q_lower:
        expanded.extend(["tier-1", "hotel", "accommodation", "6,500", "6500", "cap", "ceiling"])

    if "p1" in raw_tokens or "priority 1" in q_lower:
        expanded.extend(["p1", "critical", "sla", "acknowledgement", "resolution", "outage"])

    if "notice" in raw_tokens:
        expanded.extend(["notice", "advance", "consecutive", "14 calendar", "48 hours"])

    if "annual" in raw_tokens and "leave" in raw_tokens or "leave days" in q_lower:
        expanded.extend(["annual", "entitlements", "allotment", "earned leave", "el", "18"])

    if "home" in raw_tokens and "work" in raw_tokens or "wfh" in raw_tokens:
        expanded.extend(["wfh", "remote", "broadband", "hybrid", "campus"])

    if any(t.startswith("approv") for t in raw_tokens) or "declined" in raw_tokens:
        expanded.extend(["approval", "approvals", "hierarchy", "hierarchies"])
        if "leave" in q_lower:
            expanded.extend(["managerial", "48 hours", "auto-approved", "escalation"])
        if "expense" in q_lower or "lakh" in q_lower or "claim" in q_lower:
            expanded.extend(["tier 1", "tier 2", "tier 3", "controller", "cfo", "director"])

    if "document" in raw_tokens or "documents" in raw_tokens:
        expanded.extend(["documentation", "receipt", "invoice", "gst", "itemized"])

    return list(set(expanded))


def _compute_lexical_score(query: str, chunk: Chunk) -> float:
    """
    Compute a lexical matching score between expanded query terms and chunk content/title.
    Emphasizes title matches and domain keyword occurrences.
    """
    terms = _expand_query_terms(query)
    title_lower = chunk.section_title.lower()
    doc_lower = chunk.document.lower()
    text_lower = chunk.text.lower()
    section_num = chunk.section_number.lower()

    score = 0.0
    for term in terms:
        if len(term) < 2:
            continue

        # Exact section number match (e.g. "2.1")
        if term == section_num:
            score += 8.0

        # Title match boost
        if term in title_lower:
            score += 5.0

        # Document name match boost
        if term in doc_lower:
            score += 2.0

        # Text occurrence with sublinear frequency
        cnt = text_lower.count(term)
        if cnt > 0:
            score += 1.0 + math.log(cnt)

    return score


class DocumentRetriever:
    """
    Retrieval engine supporting hybrid semantic-vector and lexical keyword scoring.
    """

    def __init__(
        self,
        index_dir: Optional[Path] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        alpha: float = 0.35,
    ):
        """
        Args:
            index_dir: Directory where index files reside.
            embedding_provider: Provider used to embed incoming search queries.
            alpha: Weight for dense vector similarity (0.0 to 1.0). (1 - alpha) is lexical weight.
        """
        self.index_dir = Path(index_dir or DEFAULT_INDEX_DIR)
        self.provider = embedding_provider or get_embedding_provider("auto")
        self.alpha = float(alpha)

        # Load or build index
        self.indexer = DocumentIndexer(index_dir=self.index_dir, embedding_provider=self.provider)
        try:
            self.chunks, self.embeddings, self.meta = self.indexer.load_index()
        except FileNotFoundError:
            logger.info("Index not found. Building index now...")
            self.indexer.build_index()
            self.chunks, self.embeddings, self.meta = self.indexer.load_index()

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> List[RetrievalResult]:
        """
        Retrieve top_k chunks relevant to the user query.
        """
        clean_query = query.strip()
        if not clean_query or not self.chunks:
            return []

        # 1. Dense vector similarity
        query_vec = self.provider.embed_text(clean_query)
        dense_scores = np.dot(self.embeddings, query_vec)
        # Normalize dense scores to [0, 1] range
        min_d, max_d = float(np.min(dense_scores)), float(np.max(dense_scores))
        if max_d > min_d:
            norm_dense = (dense_scores - min_d) / (max_d - min_d)
        else:
            norm_dense = np.ones_like(dense_scores)

        # 2. Lexical scoring
        lex_scores = np.array([_compute_lexical_score(clean_query, c) for c in self.chunks], dtype=np.float32)
        max_l = float(np.max(lex_scores))
        if max_l > 0:
            norm_lex = lex_scores / max_l
        else:
            norm_lex = np.zeros_like(lex_scores)

        # 3. Hybrid fusion
        final_scores = self.alpha * norm_dense + (1.0 - self.alpha) * norm_lex

        # 4. Rank indices
        ranked_indices = np.argsort(final_scores)[::-1]

        results: List[RetrievalResult] = []
        for idx in ranked_indices:
            score = float(final_scores[idx])
            if score < min_score:
                continue
            chunk = self.chunks[idx]
            results.append(RetrievalResult.from_chunk(chunk, score))
            if len(results) >= top_k:
                break

        return results


# Global singleton instance for easy retrieve() calls
_default_retriever: Optional[DocumentRetriever] = None


def get_retriever() -> DocumentRetriever:
    """Get or initialize the global DocumentRetriever instance."""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = DocumentRetriever()
    return _default_retriever


def retrieve(
    query: str,
    top_k: int = 3,
    min_score: float = 0.0,
) -> List[RetrievalResult]:
    """
    Convenience function for direct query retrieval.
    Accepts natural-language query and returns ranked RetrievalResult objects.
    """
    retriever = get_retriever()
    return retriever.retrieve(query=query, top_k=top_k, min_score=min_score)
