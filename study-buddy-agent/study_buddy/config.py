"""Configuration helpers for the Study Buddy app."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Union

from dotenv import load_dotenv

# Load .env before any agent/model code reads environment variables.
load_dotenv()

if TYPE_CHECKING:
    from google.adk.models.base_llm import BaseLlm


DEFAULT_MODEL = os.getenv("STUDY_BUDDY_MODEL", "gemini-2.5-flash")
OPENROUTER_API_BASE = os.getenv(
    "OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"
)
APP_NAME = "study-buddy"
USER_ID = "student-user"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STUDY_PLAN_PATH = PROJECT_ROOT / "study_plan.md"
STUDY_MATERIALS_DIR = PROJECT_ROOT / "study_materials"


def is_vertex_mode() -> bool:
    """Return True when ADK should use Vertex AI / enterprise Gemini endpoints."""
    return os.getenv("GOOGLE_GENAI_USE_ENTERPRISE", "").lower() in {
        "1",
        "true",
        "yes",
    } or os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in {
        "1",
        "true",
        "yes",
    }


def is_openrouter_mode() -> bool:
    """Return True when requests should go through OpenRouter via LiteLLM."""
    provider = os.getenv("STUDY_BUDDY_LLM_PROVIDER", "").lower()
    if provider == "openrouter":
        return True
    if provider in {"gemini", "vertex", "google"}:
        return False
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _openrouter_model_name() -> str:
    """Normalize STUDY_BUDDY_MODEL for OpenRouter's provider/model format."""
    model = DEFAULT_MODEL
    if model.startswith("openrouter/"):
        return model
    if "/" in model:
        return f"openrouter/{model}"
    return f"openrouter/google/{model}"


def get_model() -> Union[str, "BaseLlm"]:
    """Return the ADK model handle for the configured LLM provider."""
    if is_openrouter_mode():
        from google.adk.models.lite_llm import LiteLlm

        return LiteLlm(
            model=_openrouter_model_name(),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            api_base=OPENROUTER_API_BASE,
        )
    return DEFAULT_MODEL


def describe_llm_backend() -> str:
    """Return a short label for the active LLM backend."""
    if is_openrouter_mode():
        return f"OpenRouter ({_openrouter_model_name()})"
    if is_vertex_mode():
        return f"Vertex AI ({DEFAULT_MODEL})"
    return f"Gemini ({DEFAULT_MODEL})"


def validate_environment() -> None:
    """Raise a clear error if required LLM credentials are missing."""
    if is_openrouter_mode():
        if not os.getenv("OPENROUTER_API_KEY"):
            raise RuntimeError(
                "OpenRouter mode is enabled, but OPENROUTER_API_KEY is missing in .env."
            )
        return

    if is_vertex_mode():
        missing = [
            name
            for name in ("GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION")
            if not os.getenv(name)
        ]
        if missing:
            raise RuntimeError(
                "Vertex AI mode is enabled, but these variables are missing in .env: "
                + ", ".join(missing)
            )
        return

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Copy .env.example to .env and set your API key first."
        )


def ensure_project_directories() -> None:
    """Create folders used by the MCP filesystem server."""
    STUDY_MATERIALS_DIR.mkdir(exist_ok=True)
