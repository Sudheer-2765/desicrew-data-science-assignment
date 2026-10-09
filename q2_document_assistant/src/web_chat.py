"""
FastAPI Web Chat Interface and API for Northstar Technologies Document Support Assistant.
Provides clean REST API endpoints and an interactive modern web chat UI.
"""

from contextlib import asynccontextmanager
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from q2_document_assistant.src.conversation import DocumentSupportAssistant
from q2_document_assistant.src.memory import (
    SessionExpiredError,
    SessionMemoryManager,
    SessionNotFoundError,
)
from q2_document_assistant.src.models import AssistantResponse, ConversationTurn
from q2_document_assistant.src.retriever import get_retriever

logger = logging.getLogger(__name__)

# Request & Response schemas
class CreateSessionResponse(BaseModel):
    session_id: str = Field(description="Unique session identifier")
    status: str = Field(default="created")


class ChatRequest(BaseModel):
    session_id: str = Field(description="Session ID for the conversation")
    message: str = Field(description="User prompt or question")


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[str]
    retrieved_sections: List[str]
    resolved_query: str
    topic: str
    follow_up_required: bool
    clarification_question: Optional[str] = None
    turn_index: int


class HistoryResponse(BaseModel):
    session_id: str
    turns: List[Dict[str, Any]]


# Shared singleton assistant
_assistant_instance: Optional[DocumentSupportAssistant] = None


def get_assistant() -> DocumentSupportAssistant:
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = DocumentSupportAssistant()
    return _assistant_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly initialize assistant and index on startup
    get_assistant()
    yield


app = FastAPI(
    title="Northstar Technologies Document Support Assistant",
    description="Interactive conversational interface for internal company policies.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health status endpoint."""
    return {
        "status": "healthy",
        "service": "northstar_document_assistant",
        "version": "1.0.0",
    }


@app.post("/api/session", response_model=CreateSessionResponse)
async def create_session():
    """Create a new isolated conversation session."""
    assistant = get_assistant()
    sid = assistant.create_session()
    return CreateSessionResponse(session_id=sid, status="created")


@app.post("/api/chat", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """Process a chat message within an active session."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    assistant = get_assistant()
    try:
        resp: AssistantResponse = assistant.chat(
            session_id=request.session_id, user_message=request.message.strip()
        )
        return ChatResponse(
            session_id=resp.session_id,
            answer=resp.answer,
            citations=resp.citations,
            retrieved_sections=resp.retrieved_sections,
            resolved_query=resp.resolved_query,
            topic=resp.topic,
            follow_up_required=resp.follow_up_required,
            clarification_question=resp.clarification_question,
            turn_index=resp.turn_index,
        )
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found. Please start a new session.")
    except SessionExpiredError:
        raise HTTPException(status_code=410, detail="Session has expired. Please start a new session.")
    except Exception as e:
        logger.error(f"Error handling chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing policy request.")


@app.get("/api/history/{session_id}", response_model=HistoryResponse)
async def get_session_history(session_id: str):
    """Retrieve full conversation history for a session."""
    assistant = get_assistant()
    try:
        turns: List[ConversationTurn] = assistant.get_history(session_id)
        formatted_turns = [
            {
                "turn_index": t.turn_index,
                "user_message": t.user_message,
                "resolved_query": t.resolved_query,
                "assistant_response": t.assistant_response,
                "topic": t.topic,
                "citations": t.citations,
                "timestamp": t.timestamp,
            }
            for t in turns
        ]
        return HistoryResponse(session_id=session_id, turns=formatted_turns)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found.")


@app.post("/api/reset/{session_id}")
async def reset_session(session_id: str):
    """Reset the history of an existing session."""
    assistant = get_assistant()
    try:
        assistant.clear_session(session_id)
        return {"status": "reset", "session_id": session_id}
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found.")


# Single-Page HTML Frontend
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Northstar Technologies — Document Support Assistant</title>
  <style>
    :root {
      --primary: #0f172a;
      --primary-accent: #2563eb;
      --secondary: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --text-main: #1e293b;
      --text-muted: #64748b;
      --bot-bubble: #f1f5f9;
      --user-bubble: #2563eb;
      --citation-bg: #e0f2fe;
      --citation-border: #bae6fd;
      --citation-text: #0369a1;
      --font-stack: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font-stack);
      background: #f1f5f9;
      color: var(--text-main);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }
    header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-logo {
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, #1e40af, #3b82f6);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 700;
      font-size: 20px;
    }
    .brand-title {
      font-size: 17px;
      font-weight: 700;
      color: var(--primary);
    }
    .brand-subtitle {
      font-size: 12px;
      color: var(--text-muted);
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .session-badge {
      font-size: 11px;
      background: #f8fafc;
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 14px;
      color: var(--text-muted);
      font-family: monospace;
    }
    button.btn-header {
      background: white;
      border: 1px solid var(--border);
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      color: var(--text-main);
      transition: all 0.15s;
    }
    button.btn-header:hover {
      background: #f8fafc;
      border-color: #cbd5e1;
    }
    main {
      flex: 1;
      display: flex;
      flex-direction: column;
      max-width: 950px;
      width: 100%;
      margin: 0 auto;
      padding: 16px 20px;
      height: calc(100vh - 65px);
    }
    #chat-transcript {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding: 12px 6px;
      scroll-behavior: smooth;
    }
    .message-row {
      display: flex;
      width: 100%;
    }
    .message-row.user {
      justify-content: flex-end;
    }
    .message-row.assistant {
      justify-content: flex-start;
    }
    .bubble {
      max-width: 80%;
      padding: 14px 18px;
      border-radius: 14px;
      line-height: 1.55;
      font-size: 14.5px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
      word-break: break-word;
    }
    .message-row.user .bubble {
      background: var(--user-bubble);
      color: white;
      border-bottom-right-radius: 2px;
    }
    .message-row.assistant .bubble {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text-main);
      border-bottom-left-radius: 2px;
    }
    .topic-tag {
      display: inline-block;
      font-size: 10.5px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 2px 8px;
      border-radius: 4px;
      background: #e2e8f0;
      color: #475569;
      margin-bottom: 8px;
    }
    .citation-box {
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px dashed var(--border);
      font-size: 12px;
      color: var(--citation-text);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .citation-pill {
      background: var(--citation-bg);
      border: 1px solid var(--citation-border);
      border-radius: 6px;
      padding: 4px 8px;
      font-family: inherit;
      display: inline-block;
    }
    .clarification-callout {
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #92400e;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 13.5px;
      margin-top: 8px;
    }
    .suggested-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }
    .pill {
      background: white;
      border: 1px solid var(--border);
      padding: 5px 12px;
      border-radius: 16px;
      font-size: 12.5px;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s;
    }
    .pill:hover {
      background: #eff6ff;
      border-color: #93c5fd;
      color: #1d4ed8;
    }
    .input-bar {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 8px 12px;
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);
    }
    .input-bar textarea {
      flex: 1;
      border: none;
      outline: none;
      resize: none;
      font-family: inherit;
      font-size: 14.5px;
      max-height: 100px;
      min-height: 24px;
      padding: 4px 2px;
    }
    .btn-send {
      background: var(--primary-accent);
      color: white;
      border: none;
      padding: 8px 18px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      transition: background 0.15s;
    }
    .btn-send:hover {
      background: #1d4ed8;
    }
    .btn-send:disabled {
      background: #94a3b8;
      cursor: not-allowed;
    }
    .typing-indicator {
      display: none;
      font-size: 13px;
      color: var(--text-muted);
      font-style: italic;
      margin-left: 8px;
      margin-bottom: 6px;
    }
    .error-banner {
      display: none;
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #b91c1c;
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 13px;
      margin-bottom: 8px;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-logo">N</div>
      <div>
        <div class="brand-title">Northstar Technologies</div>
        <div class="brand-subtitle">Document-Aware Policy Support Assistant</div>
      </div>
    </div>
    <div class="header-actions">
      <span class="session-badge" id="session-badge">Session: Initializing...</span>
      <button class="btn-header" onclick="startNewSession()">New Session</button>
      <button class="btn-header" onclick="clearTranscript()">Clear</button>
    </div>
  </header>

  <main>
    <div class="error-banner" id="error-banner"></div>
    <div id="chat-transcript">
      <div class="message-row assistant">
        <div class="bubble">
          <div class="topic-tag">Support Concierge</div>
          Hello! I am your Northstar Technologies policy assistant. I can answer questions regarding Leave & Attendance, Expense Reimbursements, and IT/Workplace Support with exact document citations. What would you like to know?
        </div>
      </div>
    </div>

    <div class="typing-indicator" id="typing-indicator">Searching knowledge base and formulating response...</div>

    <div class="suggested-pills">
      <span class="pill" onclick="sendPrompt('How many annual leave days are available?')">Annual Leave Days</span>
      <span class="pill" onclick="sendPrompt('What is the Tier-1 hotel reimbursement limit?')">Hotel Spending Caps</span>
      <span class="pill" onclick="sendPrompt('What is the P1 response time?')">P1 Support SLA</span>
      <span class="pill" onclick="sendPrompt('Who approves expenses above 1 lakh?')">Expense Approvals</span>
      <span class="pill" onclick="sendPrompt('Can I work from home?')">Remote Work (WFH)</span>
    </div>

    <div class="input-bar">
      <textarea id="user-input" rows="1" placeholder="Ask a question about Northstar internal policies..." onkeydown="handleKey(event)"></textarea>
      <button class="btn-send" id="btn-send" onclick="handleSend()">Send</button>
    </div>
  </main>

  <script>
    let activeSessionId = null;

    async function initSession() {
      try {
        const res = await fetch('/api/session', { method: 'POST' });
        const data = await res.json();
        activeSessionId = data.session_id;
        document.getElementById('session-badge').textContent = 'Session: ' + activeSessionId.slice(0, 16);
      } catch (err) {
        showError('Failed to initialize session. Is the server running?');
      }
    }

    async function startNewSession() {
      await initSession();
      clearTranscript();
      const transcript = document.getElementById('chat-transcript');
      transcript.innerHTML = `
        <div class="message-row assistant">
          <div class="bubble">
            <div class="topic-tag">Support Concierge</div>
            Started a fresh session (${activeSessionId.slice(0, 16)}). How can I assist you with Northstar policies?
          </div>
        </div>
      `;
    }

    function clearTranscript() {
      document.getElementById('chat-transcript').innerHTML = '';
      hideError();
    }

    function showError(msg) {
      const banner = document.getElementById('error-banner');
      banner.textContent = msg;
      banner.style.display = 'block';
    }

    function hideError() {
      document.getElementById('error-banner').style.display = 'none';
    }

    function handleKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    }

    function sendPrompt(text) {
      document.getElementById('user-input').value = text;
      handleSend();
    }

    async function handleSend() {
      const input = document.getElementById('user-input');
      const text = input.value.trim();
      if (!text) return;
      if (!activeSessionId) await initSession();

      hideError();
      input.value = '';
      appendMessage('user', text);

      const btn = document.getElementById('btn-send');
      const indicator = document.getElementById('typing-indicator');
      btn.disabled = true;
      indicator.style.display = 'block';

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: activeSessionId, message: text })
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || 'Server returned error ' + res.status);
        }

        const data = await res.json();
        appendMessage('assistant', data.answer, data.topic, data.citations, data.clarification_question);
      } catch (err) {
        showError(err.message || 'Error communicating with assistant.');
      } finally {
        btn.disabled = false;
        indicator.style.display = 'none';
      }
    }

    function appendMessage(role, text, topic, citations, clarification) {
      const transcript = document.getElementById('chat-transcript');
      const row = document.createElement('div');
      row.className = 'message-row ' + role;

      const bubble = document.createElement('div');
      bubble.className = 'bubble';

      if (role === 'assistant') {
        if (topic) {
          const tag = document.createElement('div');
          tag.className = 'topic-tag';
          tag.textContent = topic.replace(/_/g, ' ');
          bubble.appendChild(tag);
        }

        const textDiv = document.createElement('div');
        textDiv.textContent = text;
        bubble.appendChild(textDiv);

        if (clarification) {
          const callout = document.createElement('div');
          callout.className = 'clarification-callout';
          callout.textContent = clarification;
          bubble.appendChild(callout);
        }

        if (citations && citations.length > 0) {
          const citeBox = document.createElement('div');
          citeBox.className = 'citation-box';
          citations.forEach(c => {
            const pill = document.createElement('div');
            pill.className = 'citation-pill';
            pill.textContent = c;
            citeBox.appendChild(pill);
          });
          bubble.appendChild(citeBox);
        }
      } else {
        bubble.textContent = text;
      }

      row.appendChild(bubble);
      transcript.appendChild(row);
      transcript.scrollTop = transcript.scrollHeight;
    }

    window.addEventListener('DOMContentLoaded', initSession);
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    """Serve the single-page chat application."""
    return HTMLResponse(content=HTML_PAGE)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("q2_document_assistant.src.web_chat:app", host="127.0.0.1", port=8002, reload=True)

