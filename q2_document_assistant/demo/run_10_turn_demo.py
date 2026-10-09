"""
Reproducible 10-Turn Demonstration Script for Northstar Technologies Document Support Assistant.
Runs against the live conversational engine across all 10 official scenario turns
and generates a structured transcript markdown artifact.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure workspace root is in sys.path
workspace_root = Path(__file__).resolve().parent.parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from q2_document_assistant.src.conversation import DocumentSupportAssistant

# The 10 official benchmark scenario turns
SCENARIOS = [
    # Turn 1: Direct leave entitlement
    "How many annual leave days are available?",
    # Turn 2: Follow-up on carryover
    "How many of those can I carry over?",
    # Turn 3: Follow-up on notice requirements
    "How much notice is needed for more than 3 days of leave?",
    # Turn 4: Domain topic switch to expense reimbursement
    "What is the Tier-1 hotel reimbursement limit?",
    # Turn 5: Follow-up on meals inclusion
    "Does that limit include meals?",
    # Turn 6: Expense approval hierarchy
    "Who approves an expense report above ₹1,00,000?",
    # Turn 7: Domain topic switch to IT support SLA
    "What are the P1 IT support response times?",
    # Turn 8: Support contact channels
    "How can I contact IT support?",
    # Turn 9: Return to earlier leave topic regarding manager approval
    "Going back to our earlier leave discussion, what happens if my manager does not approve my request?",
    # Turn 10: Unsupported policy inquiry
    "Are pets allowed in the office?",
]


def run_demonstration(output_md_path: Path) -> None:
    assistant = DocumentSupportAssistant()
    session_id = assistant.create_session()

    print("=" * 80)
    print("NORTHSTAR TECHNOLOGIES — 10-TURN DOCUMENT ASSISTANT DEMONSTRATION")
    print(f"Session ID: {session_id}")
    print(f"Timestamp:  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    transcript_lines = [
        "# Northstar Technologies Support Assistant — 10-Turn Demonstration Transcript",
        "",
        f"**Session ID:** `{session_id}`  ",
        f"**Execution Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        "**Engine:** DocumentSupportAssistant (Local Knowledge Base + Section Grounding)  ",
        "",
        "---",
        "",
        "## Summary of Scenarios Covered",
        "1. **Turn 1 (Leave Entitlements):** Direct query regarding annual leave days.",
        "2. **Turn 2 (Follow-Up Carryover):** Anaphoric pronoun resolution (`those`) without repeating baseline entitlements.",
        "3. **Turn 3 (Notice Periods):** Inquiry into notice lead times for extended leave.",
        "4. **Turn 4 (Topic Switch — Expense):** Transition from HR leave to travel reimbursement limits.",
        "5. **Turn 5 (Follow-Up Meals):** Pronoun resolution (`that limit`) clarifying meal exclusions.",
        "6. **Turn 6 (Approval Hierarchy):** Multi-tier executive approval threshold above ₹1,00,000.",
        "7. **Turn 7 (Topic Switch — IT Support):** Transition to workplace IT incident response SLAs (P1).",
        "8. **Turn 8 (Contact Channels):** Inquiry into helpdesk portals, Slack channels, and emergency helplines.",
        "9. **Turn 9 (Return to Prior Topic):** Returning to leave domain to inspect managerial approval SLA and auto-approval.",
        "10. **Turn 10 (Unsupported Inquiry):** Out-of-domain query (office pets) triggering non-speculative rejection.",
        "",
        "---",
        "",
        "## Verbatim 10-Turn Dialogue Transcript",
        "",
    ]

    for idx, user_query in enumerate(SCENARIOS, 1):
        resp = assistant.chat(session_id, user_query)

        print(f"\nTURN {idx}:")
        print(f"  User Query:     {user_query}")
        print(f"  Resolved Query: {resp.resolved_query}")
        print(f"  Topic:          {resp.topic}")
        print(f"  Answer:         {resp.answer}")
        print(f"  Citations:      {resp.citations}")

        transcript_lines.extend([
            f"### Turn {idx}: {user_query}",
            "",
            f"- **User Message:** *\"{user_query}\"*",
            f"- **Resolved Standalone Query:** `{resp.resolved_query}`",
            f"- **Identified Domain Topic:** `{resp.topic}`",
            f"- **Follow-Up / Clarification Required:** `{resp.follow_up_required}`",
            "",
            "**Assistant Response:**",
            f"> {resp.answer}",
            "",
            "**Citations:**",
        ])

        if resp.citations:
            for cite in resp.citations:
                transcript_lines.append(f"- `{cite}`")
        else:
            transcript_lines.append("- *(No citations — unsupported query or general clarification)*")

        transcript_lines.extend(["", "---", ""])

    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text("\n".join(transcript_lines), encoding="utf-8")
    print(f"\n[SUCCESS] Transcript saved to: {output_md_path}")


if __name__ == "__main__":
    output_file = Path(__file__).resolve().parent / "10_turn_transcript.md"
    run_demonstration(output_file)
