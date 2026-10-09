"""
Context and follow-up resolution engine for the Document Support Assistant.
Detects domain topics, resolves pronouns and anaphoric references across turns,
detects topic shifts, and flags ambiguous queries requiring clarification.
"""

import logging
import re
from typing import Optional, Tuple

from q2_document_assistant.src.models import ConversationTurn, SessionState

logger = logging.getLogger(__name__)

# Domain keyword maps for topic classification
DOMAIN_KEYWORDS = {
    "leave_and_attendance": [
        "leave", "leaves", "attendance", "absent", "absence", "wfh", "remote",
        "vacation", "carry over", "carry-over", "carryover", "encash", "encashment",
        "earned leave", "sick leave", "casual leave", "maternity", "paternity",
        "bereavement", "comp-off", "comp off", "peoplepulse", "working hours",
        "core hours", "check-in", "late arrival", "grace", "doctor certificate"
    ],
    "expense_and_reimbursement": [
        "reimburse", "reimbursement", "expense", "expenses", "hotel", "lodging",
        "meal", "meals", "transit", "travel", "flight", "airfare", "cab", "taxi",
        "mileage", "conveyance", "allowance", "stipend", "receipt", "receipts",
        "invoice", "expensedesk", "tier-1", "tier-2", "tier-3", "tier 1", "tier 2",
        "tier 3", "lakh", "100000", "25000", "cfo", "controller", "disbursement"
    ],
    "employee_support": [
        "it support", "helpdesk", "servicehub", "laptop", "hardware", "refresh",
        "peripheral", "p1", "p2", "p3", "p4", "sla", "ticket", "escalation",
        "okta", "sso", "mfa", "password", "lockout", "credentials", "pam",
        "accesshub", "posh", "grievance", "kiosk", "on-call", "insurance", "pf"
    ],
}

PRONOUN_PATTERNS = [
    r"\bthose\b", r"\bthat\b", r"\bit\b", r"\bthey\b", r"\bthem\b",
    r"\bthese\b", r"\bthis\b"
]
ELLIPSIS_PATTERNS = [
    r"^how many (can|of)", r"^who should i (contact|reach)",
    r"^does that include", r"^what about", r"^and what about",
    r"^who approves (that|it)", r"^can i do that", r"^how do i claim that"
]


def classify_topic(text: str) -> Optional[str]:
    """Classify the text into a domain topic based on keyword frequency."""
    text_lower = text.lower()
    scores = {}
    for domain, kws in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in text_lower)
        if score > 0:
            scores[domain] = score

    if not scores:
        return None
    return max(scores, key=scores.get)


def is_topic_switch(query: str, current_topic: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Check if the user is explicitly switching to a different topic or returning
    to an earlier topic in the conversation.
    """
    q_lower = query.lower()
    new_topic = classify_topic(query)

    # Explicit transition markers
    switch_markers = ["switching to", "moving to", "what about", "going back to", "returning to", "now for"]
    for marker in switch_markers:
        if marker in q_lower and new_topic and new_topic != current_topic:
            return True, new_topic

    if new_topic and current_topic and new_topic != current_topic:
        # Strong keyword evidence of a new domain
        return True, new_topic

    return False, current_topic or new_topic


def is_follow_up_query(query: str) -> bool:
    """Check if the user query is a follow-up that depends on prior context."""
    q_lower = query.strip().lower()

    # Check for pronouns
    for p in PRONOUN_PATTERNS:
        if re.search(p, q_lower):
            return True

    # Check for short elliptical sentence starts
    for ep in ELLIPSIS_PATTERNS:
        if re.search(ep, q_lower):
            return True

    # Short query under 4 words without explicit domain keyword
    tokens = q_lower.split()
    if len(tokens) <= 4 and classify_topic(query) is None:
        return True

    return False


def is_ambiguous_query(query: str, session: SessionState) -> Tuple[bool, Optional[str]]:
    """
    Identify queries that are too ambiguous or underspecified to resolve even with context.
    """
    q_clean = query.strip().lower()
    ambiguous_prompts = {
        "tell me more": "Could you please specify whether you would like more details on leave policy, expense reimbursements, or IT helpdesk support?",
        "what else?": "Could you clarify which topic you would like additional information on?",
        "explain": "Could you please clarify what specific policy or process you would like explained?",
        "why?": "Could you please clarify what policy rule or procedure you are inquiring about?",
    }

    if q_clean in ambiguous_prompts:
        return True, ambiguous_prompts[q_clean]

    # Vague single word inquiries without session context
    if len(q_clean.split()) <= 2 and not session.turns and classify_topic(query) is None:
        return True, "Could you please provide a few more details so I can look up the correct policy for you?"

    return False, None


def resolve_contextual_query(
    query: str,
    session: SessionState,
) -> Tuple[str, str, bool, Optional[str]]:
    """
    Resolve the incoming user query in the context of the session history.

    Returns:
        resolved_query: Standalone query rewritten with prior entity context if needed.
        active_topic: Identified domain topic for this turn.
        is_clarification_needed: True if the assistant must ask for clarification.
        clarification_prompt: Clarification question to present to user if ambiguous.
    """
    # 1. Check for ambiguous inquiries
    ambiguous, prompt = is_ambiguous_query(query, session)
    if ambiguous:
        return query, session.active_topic or "general", True, prompt

    # 2. Check for explicit topic switch or return to prior topic
    switched, detected_topic = is_topic_switch(query, session.active_topic)

    # 3. Check for return to prior topic (e.g., 'going back to leave')
    q_lower = query.lower()
    if "going back to" in q_lower or "returning to" in q_lower:
        for prev in reversed(session.topic_history):
            if prev in q_lower or any(kw in q_lower for kw in DOMAIN_KEYWORDS.get(prev, [])):
                detected_topic = prev
                break

    # 4. If standalone topic or switched topic, return clean query
    if switched or not session.turns or not is_follow_up_query(query):
        final_topic = detected_topic or session.active_topic or "general"
        return query, final_topic, False, None

    # 5. Handle context-dependent follow-up query
    last_turn: ConversationTurn = session.turns[-1]
    last_user_query = last_turn.user_message.lower()
    last_resolved = last_turn.resolved_query.lower()
    final_topic = last_turn.topic or detected_topic or "general"

    # Context resolution rules for common follow-up patterns
    # A. "How many of those can I carry over?" -> extract subject from last turn
    if re.search(r"carry\s*over", q_lower):
        if "leave" in last_user_query or "annual" in last_user_query or "leave" in last_resolved:
            resolved = "How many annual leave days or earned leave days can I carry over to the next year?"
            return resolved, "leave_and_attendance", False, None

    # B. "Does that include meals?" / "include meals?" -> extract hotel context
    if "meal" in q_lower and ("that" in q_lower or "it" in q_lower or "include" in q_lower):
        if "hotel" in last_user_query or "tier" in last_user_query or "lodging" in last_user_query:
            resolved = "Does the hotel accommodation reimbursement limit include meals and incidentals?"
            return resolved, "expense_and_reimbursement", False, None

    # C. "Who should I contact next?" / "who do I reach?" -> extract escalation or approval context
    if re.search(r"who should i contact|who to contact|who do i reach", q_lower):
        if "leave" in last_user_query or "approved" in last_user_query:
            resolved = "Who should I contact if my leave request is not approved or declined by manager?"
            return resolved, "leave_and_attendance", False, None
        elif "expense" in last_user_query or "claim" in last_user_query:
            resolved = "Who should I contact if my expense reimbursement claim is rejected or disputed?"
            return resolved, "expense_and_reimbursement", False, None
        elif "p1" in last_user_query or "support" in last_user_query or "ticket" in last_user_query:
            resolved = "Who should I contact next in the escalation matrix for an unresolved support ticket?"
            return resolved, "employee_support", False, None

    # D. "Who approves that?" / "Who approves it?"
    if re.search(r"who approves", q_lower) and ("that" in q_lower or "it" in q_lower):
        if "expense" in last_user_query or "reimbursement" in last_user_query or "lakh" in last_user_query:
            resolved = "Who approves expense reimbursement claims?"
            return resolved, "expense_and_reimbursement", False, None
        elif "leave" in last_user_query:
            resolved = "Who approves leave requests?"
            return resolved, "leave_and_attendance", False, None

    # E. General pronoun replacement with previous query subject
    resolved_query = query
    subject_entity = ""
    if "annual leave" in last_user_query or "leave" in last_user_query:
        subject_entity = "leave"
    elif "hotel" in last_user_query or "tier" in last_user_query:
        subject_entity = "hotel reimbursement"
    elif "p1" in last_user_query or "sla" in last_user_query:
        subject_entity = "P1 support incident"

    if subject_entity:
        for pronoun in ["those", "that", "it"]:
            if pronoun == "it":
                pattern = r"\bit\b(?!\s+(?:support|helpdesk|team|department|kiosk|services|portal))"
            else:
                pattern = r"\b" + pronoun + r"\b"
            if re.search(pattern, resolved_query, re.IGNORECASE):
                resolved_query = re.sub(
                    pattern, f"the {subject_entity}", resolved_query, flags=re.IGNORECASE
                )
                break

    return resolved_query, final_topic, False, None

