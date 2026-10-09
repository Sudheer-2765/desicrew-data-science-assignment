"""Lightweight Web Chat Interface for Q1 Excel Inventory Agent using FastAPI."""

import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from q1_excel_agent.agent import ExcelInventoryAgent
from q1_excel_agent.data_loader import inspect_dataset

app = FastAPI(title="DesiCrew Q1 Excel Agent Web Chat")
agent = ExcelInventoryAgent()


class ChatRequest(BaseModel):
    message: str


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DesiCrew - Excel Inventory Assistant</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --bg: #f8fafc;
            --chat-bg: #ffffff;
            --border: #e2e8f0;
            --text-dark: #0f172a;
            --text-muted: #64748b;
            --user-bubble: #2563eb;
            --user-text: #ffffff;
            --bot-bubble: #f1f5f9;
            --bot-text: #0f172a;
            --badge-bg: #e0e7ff;
            --badge-text: #3730a3;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text-dark); display: flex; flex-direction: column; height: 100vh; }
        header { background: #fff; border-bottom: 1px solid var(--border); padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }
        header h1 { font-size: 1.15rem; font-weight: 600; color: #1e293b; }
        .stats-badge { background: #ecfdf5; color: #065f46; font-size: 0.8rem; font-weight: 500; padding: 0.35rem 0.75rem; border-radius: 9999px; border: 1px solid #a7f3d0; }
        
        main { flex: 1; max-width: 900px; width: 100%; margin: 0 auto; display: flex; flex-direction: column; overflow: hidden; padding: 1rem; }
        
        #sample-pills { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem; }
        .pill { background: #fff; border: 1px solid var(--border); border-radius: 9999px; padding: 0.35rem 0.85rem; font-size: 0.78rem; cursor: pointer; color: #334155; transition: all 0.15s ease; }
        .pill:hover { background: #eff6ff; border-color: #93c5fd; color: #1d4ed8; }

        #chat-window { flex: 1; background: var(--chat-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .msg { max-width: 80%; display: flex; flex-direction: column; gap: 0.35rem; }
        .msg.user { align-self: flex-end; }
        .msg.bot { align-self: flex-start; }
        
        .bubble { padding: 0.85rem 1.1rem; border-radius: 12px; font-size: 0.92rem; line-height: 1.5; white-space: pre-wrap; }
        .msg.user .bubble { background: var(--user-bubble); color: var(--user-text); border-bottom-right-radius: 2px; }
        .msg.bot .bubble { background: var(--bot-bubble); color: var(--bot-text); border-bottom-left-radius: 2px; }
        
        .tool-bar { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.25rem; }
        .tool-tag { font-size: 0.72rem; padding: 0.2rem 0.5rem; border-radius: 4px; background: var(--badge-bg); color: var(--badge-text); font-weight: 500; font-family: monospace; }
        
        #input-container { margin-top: 0.75rem; display: flex; gap: 0.5rem; }
        #query-input { flex: 1; padding: 0.85rem 1.1rem; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; outline: none; background: #fff; }
        #query-input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(37,99,235,0.15); }
        #send-btn { background: var(--primary); color: #fff; border: none; border-radius: 8px; padding: 0.85rem 1.5rem; font-weight: 500; cursor: pointer; transition: background 0.15s ease; }
        #send-btn:hover { background: var(--primary-hover); }
        #send-btn:disabled { opacity: 0.6; cursor: not-allowed; }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>DesiCrew — Excel Inventory Agent</h1>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">Data Querying (Pandas) &bull; Domain Glossary Search &bull; Plain-English Summaries</p>
        </div>
        <div class="stats-badge" id="stats-badge">Loading dataset stats...</div>
    </header>

    <main>
        <div id="sample-pills">
            <span class="pill" onclick="askPreset('What is the total inventory value?')">Total inventory value?</span>
            <span class="pill" onclick="askPreset('Which product has the highest units sold?')">Top selling product?</span>
            <span class="pill" onclick="askPreset('Which products have stock reconciliation discrepancies?')">Stock discrepancies?</span>
            <span class="pill" onclick="askPreset('What is safety stock?')">What is safety stock?</span>
            <span class="pill" onclick="askPreset('What is EOQ?')">What is EOQ?</span>
            <span class="pill" onclick="askPreset('Which product has the highest inventory value and what is that value?')">Highest inventory value product?</span>
        </div>

        <div id="chat-window">
            <div class="msg bot">
                <div class="bubble">Hello! I am your Excel Inventory Assistant. I can analyze the 46 products in your inventory dataset (running Pandas queries for stock calculations and anomalies) or explain supply chain terminology. What would you like to explore?</div>
            </div>
        </div>

        <div id="input-container">
            <input type="text" id="query-input" placeholder="Ask a question about the inventory dataset or supply chain concepts..." onkeypress="handleKey(event)" />
            <button id="send-btn" onclick="sendMessage()">Send</button>
        </div>
    </main>

    <script>
        // Fetch stats
        fetch('/api/info')
            .then(r => r.json())
            .then(data => {
                document.getElementById('stats-badge').innerText = `${data.row_count} Products | $${data.total_valuation.toLocaleString()} Valuation | ${data.anomalies} Discrepancies`;
            });

        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }

        function askPreset(q) {
            document.getElementById('query-input').value = q;
            sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('query-input');
            const btn = document.getElementById('send-btn');
            const q = input.value.trim();
            if (!q) return;

            input.value = '';
            input.disabled = true;
            btn.disabled = true;

            const chat = document.getElementById('chat-window');

            // User bubble
            const userMsg = document.createElement('div');
            userMsg.className = 'msg user';
            userMsg.innerHTML = `<div class="bubble">${escapeHtml(q)}</div>`;
            chat.appendChild(userMsg);
            chat.scrollTop = chat.scrollHeight;

            // Bot bubble placeholder
            const botMsg = document.createElement('div');
            botMsg.className = 'msg bot';
            botMsg.innerHTML = `<div class="bubble" style="color: #64748b;"><em>Thinking & analyzing...</em></div>`;
            chat.appendChild(botMsg);
            chat.scrollTop = chat.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: q })
                });
                const data = await res.json();

                let toolTags = '';
                if (data.tools_used && data.tools_used.length > 0) {
                    toolTags = '<div class="tool-bar">' + data.tools_used.map(t => `<span class="tool-tag">&#9881; ${escapeHtml(t.tool)}</span>`).join('') + '</div>';
                }

                botMsg.innerHTML = `<div class="bubble">${escapeHtml(data.answer)}</div>${toolTags}`;
            } catch (err) {
                botMsg.innerHTML = `<div class="bubble" style="color: #b91c1c;">An error occurred while connecting to the assistant.</div>`;
            } finally {
                input.disabled = false;
                btn.disabled = false;
                input.focus();
                chat.scrollTop = chat.scrollHeight;
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.innerText = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def get_chat_page():
    """Serve the single-page chat user interface."""
    return HTML_CONTENT


@app.get("/api/info")
def get_dataset_info():
    """Return dataset overview metrics for UI badges."""
    meta = inspect_dataset(agent.df)
    return {
        "row_count": meta["row_count"],
        "column_count": meta["column_count"],
        "total_valuation": meta["summary_statistics"]["total_inventory_valuation_usd"],
        "anomalies": meta["stock_formula_discrepancies_count"],
    }


@app.post("/api/chat")
def handle_chat_query(req: ChatRequest):
    """Process incoming query through the inventory agent."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty query provided.")
    response = agent.ask(req.message)
    return response.to_dict()


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the FastAPI uvicorn server."""
    print(f"Starting Q1 Excel Agent Web Interface at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()

