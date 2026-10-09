"""
Session memory and state management for the Document Support Assistant.
Provides isolated multi-turn context tracking, history bounding, and expiration checks.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
import uuid

from q2_document_assistant.src.models import ConversationTurn, SessionState

logger = logging.getLogger(__name__)


class SessionNotFoundError(KeyError):
    """Raised when an operation is attempted on a non-existent session ID."""
    pass


class SessionExpiredError(Exception):
    """Raised when an operation is attempted on an expired session."""
    pass


class SessionMemoryManager:
    """
    Manages isolated conversational sessions in memory.
    Enforces per-session boundaries, history caps, and activity timestamps.
    """

    def __init__(self, max_history_turns: int = 20, ttl_seconds: Optional[int] = None):
        """
        Args:
            max_history_turns: Maximum number of previous turns retained per session.
            ttl_seconds: Optional session lifetime in seconds after last activity.
        """
        self.max_history_turns = max_history_turns
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, SessionState] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create and initialize a new isolated session."""
        sid = session_id or f"nst_sess_{uuid.uuid4().hex[:12]}"
        now = self._now_iso()
        self._sessions[sid] = SessionState(
            session_id=sid,
            turns=[],
            active_topic=None,
            topic_history=[],
            provided_sections=[],
            created_at=now,
            last_active_at=now,
        )
        logger.debug(f"Created session {sid}")
        return sid

    def get_session(self, session_id: str) -> SessionState:
        """
        Retrieve state for a session.
        Raises SessionNotFoundError if the ID does not exist.
        Raises SessionExpiredError if the session has timed out.
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(f"Session '{session_id}' not found.")

        state = self._sessions[session_id]

        # Check TTL if configured
        if self.ttl_seconds is not None:
            last_active = datetime.fromisoformat(state.last_active_at)
            elapsed = (datetime.now(timezone.utc) - last_active).total_seconds()
            if elapsed > self.ttl_seconds:
                del self._sessions[session_id]
                raise SessionExpiredError(
                    f"Session '{session_id}' has expired ({int(elapsed)}s > {self.ttl_seconds}s)."
                )

        return state

    def add_turn(self, session_id: str, turn: ConversationTurn) -> None:
        """
        Record a completed conversation turn into the session memory.
        Enforces max_history_turns by trimming older turns from the front.
        """
        state = self.get_session(session_id)
        now = self._now_iso()

        # Update timestamps and active topic
        state.last_active_at = now
        state.active_topic = turn.topic
        if turn.topic and (not state.topic_history or state.topic_history[-1] != turn.topic):
            state.topic_history.append(turn.topic)

        # Record provided sections for anti-repetition tracking
        for sec in turn.retrieved_sections:
            if sec and sec not in state.provided_sections:
                state.provided_sections.append(sec)

        state.turns.append(turn)

        # Bounded history enforcement
        if len(state.turns) > self.max_history_turns:
            state.turns = state.turns[-self.max_history_turns:]

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[ConversationTurn]:
        """Return chronological conversation history for a session."""
        state = self.get_session(session_id)
        turns = state.turns
        if limit is not None and limit > 0:
            return turns[-limit:]
        return list(turns)

    def clear_session(self, session_id: str) -> None:
        """Reset conversation turns for an existing session."""
        state = self.get_session(session_id)
        state.turns.clear()
        state.active_topic = None
        state.topic_history.clear()
        state.provided_sections.clear()
        state.last_active_at = self._now_iso()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session entirely."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[str]:
        """Return list of all active session IDs."""
        return list(self._sessions.keys())
