"""
Data models for the Q2 document indexing and retrieval system.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Represents a full policy document loaded from disk."""
    document_id: str = Field(description="Unique identifier (e.g. employee_support_policy)")
    filename: str = Field(description="Filename of the document (e.g. employee_support_policy.md)")
    title: str = Field(description="Document title extracted from header")
    content: str = Field(description="Full raw markdown text")
    source: str = Field(description="Relative or absolute file path to the source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional document metadata")


class Chunk(BaseModel):
    """Represents a chunk derived from an explicit document section."""
    chunk_id: str = Field(description="Unique identifier (e.g. employee_support_policy_1_1_0)")
    document: str = Field(description="Document filename (e.g. employee_support_policy.md)")
    document_id: str = Field(description="Document identifier (e.g. employee_support_policy)")
    document_title: str = Field(description="Document title")
    section_number: str = Field(description="Section number (e.g. 1.1, 2.3)")
    section_title: str = Field(description="Section title (e.g. Support Channels)")
    chunk_index: int = Field(default=0, description="Sequential index within the section")
    source: str = Field(description="Source file path")
    text: str = Field(description="Section chunk text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")

    @property
    def citation(self) -> str:
        """Formatted source citation string."""
        return f"[Source: {self.document}, Section {self.section_number} — {self.section_title}]"


class RetrievalResult(BaseModel):
    """Result returned by the retrieval system for a user query."""
    chunk_id: str = Field(description="ID of retrieved chunk")
    document: str = Field(description="Document filename")
    document_id: str = Field(description="Document ID")
    document_title: str = Field(description="Document title")
    section_number: str = Field(description="Section number")
    section_title: str = Field(description="Section title")
    source: str = Field(description="Document source path")
    text: str = Field(description="Chunk content text")
    relevance_score: float = Field(description="Computed relevance/similarity score (0.0 to 1.0)")
    citation: str = Field(description="Standardized citation string")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Associated chunk metadata")

    @classmethod
    def from_chunk(cls, chunk: Chunk, relevance_score: float) -> "RetrievalResult":
        """Construct a RetrievalResult from a Chunk and a score."""
        return cls(
            chunk_id=chunk.chunk_id,
            document=chunk.document,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            section_number=chunk.section_number,
            section_title=chunk.section_title,
            source=chunk.source,
            text=chunk.text,
            relevance_score=round(float(relevance_score), 4),
            citation=chunk.citation,
            metadata=chunk.metadata,
        )


class ConversationTurn(BaseModel):
    """Represents a single exchange between user and assistant within a session."""
    turn_index: int = Field(description="0-indexed turn number in session")
    user_message: str = Field(description="Raw user query")
    resolved_query: str = Field(description="Standalone or contextual query used for retrieval")
    assistant_response: str = Field(description="Answer text generated for the user")
    topic: str = Field(description="Domain topic identified (e.g. leave, reimbursement, it_support)")
    citations: list[str] = Field(default_factory=list, description="Citations attached to response")
    retrieved_sections: list[str] = Field(default_factory=list, description="Section numbers referenced")
    timestamp: str = Field(default="", description="ISO timestamp of turn")


class AssistantResponse(BaseModel):
    """Structured response returned by DocumentSupportAssistant.chat()."""
    session_id: str = Field(description="Active session identifier")
    answer: str = Field(description="Grounded, plain English response")
    citations: list[str] = Field(default_factory=list, description="List of source citation strings")
    retrieved_sections: list[str] = Field(default_factory=list, description="Section identifiers used")
    resolved_query: str = Field(description="Contextually rewritten or standalone query")
    topic: str = Field(description="Active conversation topic")
    follow_up_required: bool = Field(default=False, description="True if clarification is needed from user")
    clarification_question: Optional[str] = Field(default=None, description="Clarification prompt if ambiguous")
    turn_index: int = Field(default=0, description="Sequential turn index")


class SessionState(BaseModel):
    """Maintains active state, turns, and context memory for a single session."""
    session_id: str = Field(description="Unique session identifier")
    turns: list[ConversationTurn] = Field(default_factory=list, description="History of conversation turns")
    active_topic: Optional[str] = Field(default=None, description="Current domain topic")
    topic_history: list[str] = Field(default_factory=list, description="Sequence of topics discussed")
    provided_sections: list[str] = Field(default_factory=list, description="Unique section numbers already provided")
    created_at: str = Field(default="", description="Session creation ISO timestamp")
    last_active_at: str = Field(default="", description="Last activity ISO timestamp")

