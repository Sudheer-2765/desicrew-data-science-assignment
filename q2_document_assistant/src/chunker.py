"""
Section-aware chunker for Northstar Technologies policy documents.
Chunks primarily by explicit numbered policy sections, preserving section boundaries
and metadata for exact citation.
"""

import re
from typing import List, Optional

from q2_document_assistant.src.models import Chunk, Document


SECTION_HEADER_PATTERN = re.compile(
    r"^###\s+Section\s+([0-9]+\.[0-9]+):\s*(.+)$", re.MULTILINE
)
CATEGORY_HEADER_PATTERN = re.compile(
    r"^##\s+([0-9]+\..+)$", re.MULTILINE
)


def split_large_section(text: str, max_chars: int = 2000) -> List[str]:
    """
    Split a large section text into smaller logical units by paragraph,
    ensuring each unit does not exceed max_chars when possible.
    """
    if len(text) <= max_chars:
        return [text.strip()]

    paragraphs = text.split("\n\n")
    sub_chunks: List[str] = []
    current_buf: List[str] = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current_len + len(para) + 2 > max_chars and current_buf:
            sub_chunks.append("\n\n".join(current_buf))
            current_buf = [para]
            current_len = len(para)
        else:
            current_buf.append(para)
            current_len += len(para) + 2

    if current_buf:
        sub_chunks.append("\n\n".join(current_buf))

    return sub_chunks or [text.strip()]


def chunk_document(
    doc: Document,
    max_chunk_chars: int = 2000,
    include_preamble: bool = True,
) -> List[Chunk]:
    """
    Parse a policy document into chunks by explicit numbered sections.
    Preserves document, section number, section title, and source citation metadata.
    """
    chunks: List[Chunk] = []
    content = doc.content

    # Find all section headers with their start and end positions
    matches = list(SECTION_HEADER_PATTERN.finditer(content))

    if not matches:
        # Fallback if no numbered sections found: return entire document as one chunk
        chunks.append(
            Chunk(
                chunk_id=f"{doc.document_id}_0_0_0",
                document=doc.filename,
                document_id=doc.document_id,
                document_title=doc.title,
                section_number="1.0",
                section_title=doc.title,
                chunk_index=0,
                source=doc.source,
                text=content.strip(),
                metadata=doc.metadata,
            )
        )
        return chunks

    # Handle preamble before the first section (if present and requested)
    first_section_start = matches[0].start()
    if include_preamble and first_section_start > 0:
        preamble_text = content[:first_section_start].strip()
        # Only include preamble if it contains meaningful text beyond title
        if len(preamble_text) > 100:
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.document_id}_0_0_0",
                    document=doc.filename,
                    document_id=doc.document_id,
                    document_title=doc.title,
                    section_number="0.0",
                    section_title="Document Overview and Metadata",
                    chunk_index=0,
                    source=doc.source,
                    text=preamble_text,
                    metadata={**doc.metadata, "is_preamble": True},
                )
            )

    # Process each numbered section
    for i, match in enumerate(matches):
        section_number = match.group(1).strip()
        section_title = match.group(2).strip()

        # Section body runs until the next section header or EOF
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        raw_body = content[body_start:body_end]

        # Clean trailing horizontal rules and excess whitespace
        clean_body = re.sub(r"\n---\s*\n", "\n\n", raw_body).strip()
        # Combine section header with body for complete context
        full_section_text = f"### Section {section_number}: {section_title}\n\n{clean_body}".strip()

        # Split if section exceeds max_chunk_chars
        text_units = split_large_section(full_section_text, max_chars=max_chunk_chars)
        for chunk_idx, unit_text in enumerate(text_units):
            chunk_slug = section_number.replace(".", "_")
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.document_id}_{chunk_slug}_{chunk_idx}",
                    document=doc.filename,
                    document_id=doc.document_id,
                    document_title=doc.title,
                    section_number=section_number,
                    section_title=section_title,
                    chunk_index=chunk_idx,
                    source=doc.source,
                    text=unit_text,
                    metadata={
                        **doc.metadata,
                        "section_number": section_number,
                        "section_title": section_title,
                        "chunk_index": chunk_idx,
                    },
                )
            )

    return chunks


def chunk_documents(
    documents: List[Document],
    max_chunk_chars: int = 2000,
    include_preamble: bool = True,
) -> List[Chunk]:
    """Chunk a list of loaded documents."""
    all_chunks: List[Chunk] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, max_chunk_chars=max_chunk_chars, include_preamble=include_preamble))
    return all_chunks

