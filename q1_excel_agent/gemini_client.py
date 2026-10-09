"""Gemini API client configuration and initialization."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Automatically look for .env in q1_excel_agent, workspace root, or cwd
for possible_env in [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]:
    if possible_env.exists():
        load_dotenv(dotenv_path=possible_env)
load_dotenv()

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_api_key(api_key: Optional[str] = None) -> str:
    """
    Retrieve Gemini API key safely from parameter or environment.
    Never exposes secrets in logs or exceptions.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "GEMINI_API_KEY is not set. Please configure the GEMINI_API_KEY "
            "environment variable or provide it to the client."
        )
    return key.strip()


def create_gemini_client(api_key: Optional[str] = None):
    """
    Create and return an authenticated Google GenAI client.
    """
    from google import genai

    resolved_key = get_api_key(api_key)
    return genai.Client(api_key=resolved_key)

