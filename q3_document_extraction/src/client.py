"""Client initialization and credential management for Question 3."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Search locations for .env
for env_path in [
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parent.parent.parent / "q1_excel_agent" / ".env",
    Path(__file__).resolve().parent.parent.parent / ".env",
]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
load_dotenv()

DEFAULT_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", os.getenv("GEMINI_MODEL", "gemini-flash-latest"))


def get_api_key(api_key: Optional[str] = None) -> str:
    """Safely retrieve Gemini API key without exposing secrets."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key or not key.strip():
        raise ValueError("GEMINI_API_KEY is not configured.")
    return key.strip()


def get_gemini_client(api_key: Optional[str] = None):
    """Create authenticated Google GenAI client."""
    from google import genai
    resolved_key = get_api_key(api_key)
    return genai.Client(api_key=resolved_key)

