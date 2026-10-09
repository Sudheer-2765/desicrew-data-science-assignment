"""
Embedding providers for Q2 document indexing and retrieval.
Supports Google Gemini embeddings with automatic, deterministic local fallback.
Does not hardcode credentials or depend on external services for offline testing.
"""

from abc import ABC, abstractmethod
import hashlib
import logging
import math
import os
import re
from typing import List, Optional, Set, Union

import numpy as np

logger = logging.getLogger(__name__)

# Standard English stopwords to eliminate lexical noise
STOPWORDS: Set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "to", "from", "in", "out",
    "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "just", "should", "now", "of", "for", "at", "by", "with", "about",
    "against", "between", "into", "through", "during", "before", "after",
    "above", "below", "up", "down", "what", "which", "who", "whom", "this",
    "that", "these", "those", "am", "it", "its", "as", "if"
}


def _tokenize(text: str) -> List[str]:
    """
    Extract informative word tokens, word bigrams, and character n-grams
    while filtering common stopwords.
    """
    clean = re.sub(r"[^\w\s\-\.]", " ", text.lower())
    raw_words = [w.strip() for w in clean.split() if len(w.strip()) > 1]
    words = [w for w in raw_words if w not in STOPWORDS]
    tokens = list(words)

    # Word bigrams for phrase matching (e.g., 'annual_leave', 'tier_1')
    for i in range(len(raw_words) - 1):
        w1, w2 = raw_words[i], raw_words[i + 1]
        if w1 not in STOPWORDS or w2 not in STOPWORDS:
            tokens.append(f"{w1}_{w2}")

    # Character n-grams for acronyms and stems (e.g., 'p1', 'wfh', 'sla')
    for word in words:
        if len(word) >= 3:
            for n in (3, 4):
                for i in range(len(word) - n + 1):
                    tokens.append(f"char_{word[i:i+n]}")

    return tokens


class BaseEmbeddingProvider(ABC):
    """Abstract base class for all embedding providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string into a 1D numpy array."""
        pass

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed a batch of text strings into a 2D numpy array [N, dim]."""
        return np.vstack([self.embed_text(t) for t in texts])


class LocalDeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic local embedding provider based on hashed token/subword TF-IDF
    feature projection with L2 normalization.
    Completely offline, reproducible, and requires no external API or model weights.
    """

    def __init__(self, dimension: int = 1024):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return "local_deterministic"

    def _hash_token(self, token: str) -> int:
        """Deterministic integer hash for a token across Python processes."""
        md5_hash = hashlib.md5(token.encode("utf-8")).hexdigest()
        return int(md5_hash[:8], 16) % self._dim

    def embed_text(self, text: str) -> np.ndarray:
        """Generate a normalized feature vector for the given text."""
        tokens = _tokenize(text)
        vec = np.zeros(self._dim, dtype=np.float32)

        if not tokens:
            return vec

        # Term frequency accumulation with sublinear scaling
        tf_counts = {}
        for token in tokens:
            tf_counts[token] = tf_counts.get(token, 0) + 1

        for token, count in tf_counts.items():
            idx = self._hash_token(token)
            weight = 1.0 + math.log(count)
            # Give higher weight to exact word and bigram tokens
            if token.startswith("char_"):
                weight *= 0.25
            elif "_" in token:
                weight *= 1.5
            vec[idx] += weight

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Gemini embedding provider utilizing the Google Gemini API (google-genai SDK).
    Requires GEMINI_API_KEY in the environment or passed during initialization.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "models/gemini-embedding-001",
        dimension: int = 768,
    ):
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key:
            env_file = os.path.join("q1_excel_agent", ".env")
            if os.path.isfile(env_file):
                from dotenv import dotenv_values
                vals = dotenv_values(env_file)
                self._api_key = vals.get("GEMINI_API_KEY")

        if not self._api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or .env file.")

        self._model_name = os.environ.get("GEMINI_EMBEDDING_MODEL", model_name)
        self._dim = dimension

        from google import genai
        self._client = genai.Client(api_key=self._api_key)

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return f"gemini_{self._model_name.replace('/', '_')}"

    def embed_text(self, text: str) -> np.ndarray:
        clean_text = text.strip()
        if not clean_text:
            return np.zeros(self._dim, dtype=np.float32)

        result = self._client.models.embed_content(
            model=self._model_name,
            contents=clean_text,
        )

        if hasattr(result, "embedding") and result.embedding:
            vals = result.embedding.values
        elif hasattr(result, "embeddings") and result.embeddings:
            vals = result.embeddings[0].values
        else:
            raise RuntimeError(f"Unexpected Gemini embed response structure: {result}")

        vec = np.array(vals, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec


class HybridEmbeddingProvider(BaseEmbeddingProvider):
    """
    Hybrid provider that attempts to use Gemini embeddings when available,
    but automatically falls back to LocalDeterministicEmbeddingProvider if the API
    is missing, denied, quota-exhausted, or encounters an error.
    """

    def __init__(self, preferred: Optional[BaseEmbeddingProvider] = None):
        self._local = LocalDeterministicEmbeddingProvider(dimension=1024)
        self._remote: Optional[BaseEmbeddingProvider] = None

        if preferred:
            self._remote = preferred
        else:
            try:
                self._remote = GeminiEmbeddingProvider()
            except Exception as e:
                logger.info(f"Gemini embedding provider unavailable ({e}); using local fallback.")
                self._remote = None

        self._active_provider = self._remote if self._remote else self._local

    @property
    def dimension(self) -> int:
        return self._active_provider.dimension

    @property
    def name(self) -> str:
        return f"hybrid({self._active_provider.name})"

    @property
    def is_using_fallback(self) -> bool:
        return self._active_provider is self._local

    def embed_text(self, text: str) -> np.ndarray:
        if self._remote:
            try:
                return self._remote.embed_text(text)
            except Exception as e:
                logger.warning(f"Remote embedding call failed ({e}); falling back to local deterministic.")
                self._active_provider = self._local
                self._remote = None
                return self._local.embed_text(text)
        return self._local.embed_text(text)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        if self._remote:
            try:
                return self._remote.embed_batch(texts)
            except Exception as e:
                logger.warning(f"Remote batch embedding call failed ({e}); falling back to local deterministic.")
                self._active_provider = self._local
                self._remote = None
                return self._local.embed_batch(texts)
        return self._local.embed_batch(texts)


def get_embedding_provider(provider_type: str = "auto") -> BaseEmbeddingProvider:
    """
    Factory function to get an embedding provider.
    - 'local': strictly deterministic local provider.
    - 'gemini': strictly Gemini provider (raises if key unavailable).
    - 'auto' / 'hybrid': hybrid provider with graceful fallback.
    """
    provider_type = provider_type.lower()
    if provider_type == "local":
        return LocalDeterministicEmbeddingProvider()
    elif provider_type == "gemini":
        return GeminiEmbeddingProvider()
    else:
        return HybridEmbeddingProvider()

