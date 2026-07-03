"""Terminal entry point for the Study Buddy multi-agent app."""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv

# Load .env before importing agents so model selection sees OpenRouter settings.
load_dotenv()

from google.adk.runners import InMemoryRunner
from google.genai import types

from study_buddy.agents import coordinator_agent
from study_buddy.config import APP_NAME
from study_buddy.config import USER_ID
from study_buddy.config import describe_llm_backend
from study_buddy.config import ensure_project_directories
from study_buddy.config import validate_environment


def _extract_text_from_event(event) -> str:
    """Extract readable text from a Google ADK event."""
    if not event.content or not event.content.parts:
        return ""

    chunks: list[str] = []
    for part in event.content.parts:
        if getattr(part, "text", None):
            chunks.append(part.text)
    return "".join(chunks).strip()


async def chat() -> None:
    """Run an interactive terminal chat loop against the coordinator agent."""
    ensure_project_directories()
    validate_environment()

    # InMemoryRunner is enough for a local prototype and keeps the example simple.
    runner = InMemoryRunner(agent=coordinator_agent, app_name=APP_NAME)

    # One session keeps the conversation context across multiple turns.
    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state={},
    )

    print("Study Buddy is ready.")
    print(f"LLM backend: {describe_llm_backend()}")
    print("Type your study request, or type 'exit' to quit.\n")

    while True:
        user_text = input("You: ").strip()
        if user_text.lower() in {"exit", "quit"}:
            print("Study Buddy: Goodbye.")
            break
        if not user_text:
            continue

        message = types.Content(role="user", parts=[types.Part(text=user_text)])
        printed_response = False

        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=message,
        ):
            # Ignore echoed user events and only print actual agent text responses.
            if event.author == "user":
                continue

            text = _extract_text_from_event(event)
            if text:
                print(f"\nStudy Buddy ({event.author}):\n{text}\n")
                printed_response = True

        if not printed_response:
            print("\nStudy Buddy: I processed that request, but no text response was returned.\n")


def _print_api_help(exc: Exception) -> None:
    """Show a friendly hint for common Gemini API setup problems."""
    message = str(exc)
    if "User location is not supported" in message:
        print(
            "\nGemini API region error:\n"
            "- Google AI Studio API keys are blocked from some regions such as Hong Kong.\n"
            "- Your project code is fine; this is an API access issue.\n"
            "- Workarounds:\n"
            "  1. Switch to OpenRouter in .env (see .env.example)\n"
            "  2. Switch to Vertex AI in .env (see .env.example)\n"
            "  3. Use a VPN/server in a supported region\n"
            "  4. Run the offline PDF demo: .\\.venv\\Scripts\\python.exe demo_pdf_pipeline.py\n"
        )
    if "RESOURCE_EXHAUSTED" in message or "429" in message:
        print(
            "\nGemini API quota error:\n"
            "- The free tier only allows a few requests per minute.\n"
            "- Workarounds:\n"
            "  1. Wait about a minute and try again\n"
            "  2. Switch to OpenRouter in .env (see .env.example)\n"
            "  3. Upgrade your Google AI Studio plan\n"
        )


if __name__ == "__main__":
    try:
        asyncio.run(chat())
    except RuntimeError as exc:
        print(f"Startup error: {exc}")
    except Exception as exc:
        _print_api_help(exc)
        raise
