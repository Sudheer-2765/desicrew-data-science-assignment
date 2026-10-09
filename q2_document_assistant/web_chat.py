"""
Top-level entry point for Northstar Technologies Document Support Assistant Web App.
Launch with:
    python -m q2_document_assistant.web_chat
"""

import sys
import uvicorn

from q2_document_assistant.src.web_chat import app

if __name__ == "__main__":
    port = 8002
    host = "127.0.0.1"
    print("=" * 70)
    print("Northstar Technologies — Document Support Assistant Web Server")
    print(f"URL: http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    uvicorn.run(app, host=host, port=port)

