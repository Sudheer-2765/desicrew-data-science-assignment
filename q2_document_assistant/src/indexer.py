"""
Knowledge Base Indexer for Northstar Technologies policy documents.
Builds and persists a reproducible local vector index from markdown documents.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from q2_document_assistant.src.chunker import chunk_documents
from q2_document_assistant.src.document_loader import load_documents
from q2_document_assistant.src.embeddings import BaseEmbeddingProvider, get_embedding_provider
from q2_document_assistant.src.models import Chunk

logger = logging.getLogger(__name__)

DEFAULT_INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "index"
DEFAULT_DOCS_DIR = Path(__file__).resolve().parent.parent / "documents"


class DocumentIndexer:
    """Handles index creation, serialization, and loading."""

    def __init__(
        self,
        docs_dir: Optional[Path] = None,
        index_dir: Optional[Path] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.docs_dir = Path(docs_dir or DEFAULT_DOCS_DIR)
        self.index_dir = Path(index_dir or DEFAULT_INDEX_DIR)
        self.provider = embedding_provider or get_embedding_provider("auto")

    def build_index(self, max_chunk_chars: int = 2000) -> dict:
        """
        Build the vector index from policy documents and persist it to disk.
        Returns summary dictionary.
        """
        self.index_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Loading documents from {self.docs_dir}...")
        documents = load_documents(self.docs_dir)
        if not documents:
            raise ValueError(f"No policy documents found in {self.docs_dir}")

        logger.info(f"Loaded {len(documents)} documents. Chunking by sections...")
        chunks = chunk_documents(documents, max_chunk_chars=max_chunk_chars, include_preamble=True)
        logger.info(f"Generated {len(chunks)} chunks.")

        # Compute embeddings
        texts = [chunk.text for chunk in chunks]
        logger.info(f"Embedding {len(texts)} chunks with provider '{self.provider.name}'...")
        embeddings = self.provider.embed_batch(texts)

        # File paths
        chunks_file = self.index_dir / "chunks.json"
        embeddings_file = self.index_dir / "embeddings.npy"
        meta_file = self.index_dir / "index_meta.json"

        # Serialize chunks
        chunks_data = [chunk.model_dump() for chunk in chunks]
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)

        # Serialize embeddings
        np.save(embeddings_file, embeddings.astype(np.float32))

        # Serialize index metadata
        index_meta = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "provider_name": self.provider.name,
            "embedding_dimension": self.provider.dimension,
            "document_count": len(documents),
            "documents": [d.filename for d in documents],
            "chunk_count": len(chunks),
            "index_version": "1.0",
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(index_meta, f, indent=2)

        logger.info(f"Index successfully built and saved to {self.index_dir}")
        return index_meta

    def load_index(self) -> Tuple[List[Chunk], np.ndarray, dict]:
        """
        Load chunks, embeddings, and metadata from disk.
        """
        chunks_file = self.index_dir / "chunks.json"
        embeddings_file = self.index_dir / "embeddings.npy"
        meta_file = self.index_dir / "index_meta.json"

        if not chunks_file.exists() or not embeddings_file.exists():
            raise FileNotFoundError(
                f"Index files missing at {self.index_dir}. Run indexer to build the index."
            )

        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        chunks = [Chunk(**item) for item in chunks_data]

        embeddings = np.load(embeddings_file)

        meta = {}
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

        return chunks, embeddings, meta


def rebuild_index(
    docs_dir: Optional[Path] = None,
    index_dir: Optional[Path] = None,
    provider_type: str = "auto",
) -> dict:
    """Convenience function to build/rebuild the index."""
    provider = get_embedding_provider(provider_type)
    indexer = DocumentIndexer(docs_dir=docs_dir, index_dir=index_dir, embedding_provider=provider)
    return indexer.build_index()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("=" * 60)
    print("Building Northstar Technologies Knowledge Base Index")
    print("=" * 60)
    meta = rebuild_index()
    print("\nIndex Build Summary:")
    print(f"  - Document Count: {meta['document_count']}")
    print(f"  - Documents: {', '.join(meta['documents'])}")
    print(f"  - Chunks Indexed: {meta['chunk_count']}")
    print(f"  - Provider: {meta['provider_name']}")
    print(f"  - Vector Dimension: {meta['embedding_dimension']}")
    print(f"  - Created At: {meta['created_at']}")
    print("\nIndex creation complete.")

