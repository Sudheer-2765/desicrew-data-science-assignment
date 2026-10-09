"""
Document loader for Northstar Technologies policy documents.
Loads markdown files and extracts core document-level metadata.
"""

from pathlib import Path
import re
from typing import List, Optional

from q2_document_assistant.src.models import Document

# Supported policy document filenames
POLICY_DOCUMENTS = [
    "employee_support_policy.md",
    "leave_and_attendance_policy.md",
    "reimbursement_policy.md",
]


def extract_document_title(content: str, default_title: str) -> str:
    """Extract the main H1 title from markdown content."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            # Clean up potential em-dash or prefix if present
            if "—" in title:
                return title.split("—")[-1].strip()
            if "-" in title and "Northstar" in title:
                return title.split("-")[-1].strip()
            return title
    return default_title


def extract_metadata_fields(content: str) -> dict:
    """Extract metadata headers such as Document Reference, Effective Date, etc."""
    meta = {}
    patterns = {
        "doc_ref": r"\*\*Document Reference:\*\*\s*([^\n\r]+)",
        "effective_date": r"\*\*Effective Date:\*\*\s*([^\n\r]+)",
        "last_revised": r"\*\*Last Revised:\*\*\s*([^\n\r]+)",
        "custodian": r"\*\*Custodian:\*\*\s*([^\n\r]+)",
        "applies_to": r"\*\*Applies To:\*\*\s*([^\n\r]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            meta[key] = match.group(1).strip()
    return meta


def load_document(file_path: Path) -> Document:
    """Load a single markdown policy document."""
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Document not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    filename = file_path.name
    doc_id = file_path.stem
    title = extract_document_title(content, default_title=doc_id.replace("_", " ").title())
    metadata = extract_metadata_fields(content)

    return Document(
        document_id=doc_id,
        filename=filename,
        title=title,
        content=content,
        source=str(file_path.as_posix()),
        metadata=metadata,
    )


def load_documents(directory: Optional[Path] = None) -> List[Document]:
    """
    Load all policy documents from the designated directory.
    Defaults to q2_document_assistant/documents.
    """
    if directory is None:
        directory = Path(__file__).resolve().parent.parent / "documents"

    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Documents directory not found: {directory}")

    documents: List[Document] = []
    for policy_filename in POLICY_DOCUMENTS:
        doc_path = directory / policy_filename
        if doc_path.exists():
            documents.append(load_document(doc_path))

    return documents

