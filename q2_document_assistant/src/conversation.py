"""
Multi-turn conversational engine for the Document-Aware Support Assistant.
Coordinates session memory, context resolution, retrieval, answer generation,
and citation enforcement.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional

from q2_document_assistant.src.answer_generator import (
    BaseAnswerGenerator,
    DeterministicAnswerGenerator,
    GeminiAnswerGenerator,
)
from q2_document_assistant.src.context_resolver import resolve_contextual_query
from q2_document_assistant.src.memory import (
    SessionExpiredError,
    SessionMemoryManager,
    SessionNotFoundError,
)
from q2_document_assistant.src.models import AssistantResponse, ConversationTurn
from q2_document_assistant.src.retriever import DocumentRetriever, get_retriever

logger = logging.getLogger(__name__)


class DocumentSupportAssistant:
    """
    Document-Aware Conversational Support Assistant for Northstar Technologies.
    Manages multi-turn state, resolves follow-ups, queries the knowledge base,
    and returns grounded responses with citations.
    """

    def __init__(
        self,
        retriever: Optional[DocumentRetriever] = None,
        memory_manager: Optional[SessionMemoryManager] = None,
        answer_generator: Optional[BaseAnswerGenerator] = None,
        use_gemini: bool = False,
    ):
        """
        Initialize the conversational assistant.

        Args:
            retriever: DocumentRetriever instance (defaults to shared global retriever).
            memory_manager: SessionMemoryManager instance (defaults to new manager).
            answer_generator: Answer generator strategy.
            use_gemini: If True, uses GeminiAnswerGenerator with local fallback.
        """
        self.retriever = retriever or get_retriever()
        self.memory = memory_manager or SessionMemoryManager(max_history_turns=20)

        if answer_generator:
            self.generator = answer_generator
        elif use_gemini:
            self.generator = GeminiAnswerGenerator()
        else:
            self.generator = DeterministicAnswerGenerator()

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session and return the session ID."""
        return self.memory.create_session(session_id=session_id)

    def chat(self, session_id: str, user_message: str) -> AssistantResponse:
        """
        Process a user message within an active session.

        1. Retrieves session state and validates session ID.
        2. Resolves pronouns, anaphoric references, and topic shifts.
        3. Asks clarification if query is ambiguous.
        4. Retrieves relevant policy chunks from knowledge base.
        5. Generates grounded answer with mandatory citations and anti-repetition.
        6. Updates session memory with the new conversation turn.
        """
        clean_msg = user_message.strip()
        if not clean_msg:
            raise ValueError("User message cannot be empty.")

        # 1. Retrieve session state (raises SessionNotFoundError or SessionExpiredError if invalid)
        session = self.memory.get_session(session_id)
        current_turn_index = len(session.turns)

        # 2. Resolve context and check for ambiguity
        resolved_query, active_topic, is_clarification, prompt = resolve_contextual_query(
            clean_msg, session
        )

        # 3. Handle ambiguous queries that require clarification
        if is_clarification:
            resp = AssistantResponse(
                session_id=session_id,
                answer=prompt or "Could you please provide more details?",
                citations=[],
                retrieved_sections=[],
                resolved_query=clean_msg,
                topic=active_topic,
                follow_up_required=True,
                clarification_question=prompt,
                turn_index=current_turn_index,
            )
            # Record turn in memory
            turn = ConversationTurn(
                turn_index=current_turn_index,
                user_message=clean_msg,
                resolved_query=clean_msg,
                assistant_response=resp.answer,
                topic=active_topic,
                citations=[],
                retrieved_sections=[],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self.memory.add_turn(session_id, turn)
            return resp

        # 4. Retrieve policy chunks from knowledge base
        retrieved_chunks = self.retriever.retrieve(query=resolved_query, top_k=3)

        # 5. Generate grounded answer
        response = self.generator.generate(
            session_id=session_id,
            query=clean_msg,
            resolved_query=resolved_query,
            topic=active_topic,
            retrieved_chunks=retrieved_chunks,
            session=session,
            turn_index=current_turn_index,
        )

        # 6. Record turn in session memory
        turn = ConversationTurn(
            turn_index=current_turn_index,
            user_message=clean_msg,
            resolved_query=resolved_query,
            assistant_response=response.answer,
            topic=active_topic,
            citations=response.citations,
            retrieved_sections=response.retrieved_sections,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.memory.add_turn(session_id, turn)

        return response

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[ConversationTurn]:
        """Return chronological conversation history for the session."""
        return self.memory.get_history(session_id, limit=limit)

    def clear_session(self, session_id: str) -> None:
        """Clear turn history for an active session."""
        self.memory.clear_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session entirely."""
        return self.memory.delete_session(session_id)

