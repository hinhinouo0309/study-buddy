"""Offline demo: PDF -> extracted text -> study notes -> study_plan.md.

This script does NOT call an LLM. Use it when API access is blocked,
quota is exhausted, or you only want to verify the PDF pipeline.
"""

from __future__ import annotations

import re

from study_buddy.config import STUDY_PLAN_PATH
from study_buddy.config import ensure_project_directories
from study_buddy.mcp_server import extract_pdf_text
from study_buddy.mcp_server import list_pdf_files
from study_buddy.mcp_server import read_study_plan
from study_buddy.mcp_server import write_study_plan
from study_buddy.skills import merge_study_plan_with_notes


def _pick_sentences(text: str, limit: int = 8) -> list[str]:
    """Pick short, readable lines from extracted PDF text."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    picked: list[str] = []
    for line in lines:
        if len(line) < 12:
            continue
        if line.startswith("Source PDF:"):
            continue
        if re.fullmatch(r"[\d\W]+", line):
            continue
        if line not in picked:
            picked.append(line)
        if len(picked) >= limit:
            break
    return picked


def build_revision_notes_from_text(pdf_name: str, extracted_text: str) -> str:
    """Build a simple markdown revision brief without an LLM."""
    key_lines = _pick_sentences(extracted_text, limit=10)
    concepts = key_lines[:5]
    revision_points = key_lines[:8]

    questions = [
        f"What is the main idea behind: {concepts[0]}?"
        if concepts
        else "What are the main topics in this lecture?",
        "List three key terms from the notes and explain each in your own words.",
        "Which topic in the lecture would be hardest to explain without notes?",
        "Write one short-answer question and one applied question from this material.",
    ]

    lines = [
        f"Source: `{pdf_name}`",
        "",
        "### Revision points",
    ]
    for index, point in enumerate(revision_points, start=1):
        lines.append(f"{index}. {point}")

    lines.extend(["", "### Key concepts"])
    for index, concept in enumerate(concepts, start=1):
        lines.append(f"{index}. {concept}")

    lines.extend(["", "### Study questions"])
    for index, question in enumerate(questions, start=1):
        lines.append(f"{index}. {question}")

    return "\n".join(lines)


def run_demo(pdf_filename: str = "week_10_note.pdf") -> None:
    """Run the full local PDF research pipeline without Gemini."""
    ensure_project_directories()

    print("Step 1: Detect PDF files through MCP...")
    print(list_pdf_files("."))
    print()

    print(f"Step 2: Extract text from {pdf_filename} with pypdf...")
    extracted = extract_pdf_text(pdf_filename)
    preview = extracted[:500] + ("..." if len(extracted) > 500 else "")
    print(preview)
    print()

    print("Step 3: Build revision notes from extracted text...")
    notes = build_revision_notes_from_text(pdf_filename, extracted)
    print(notes)
    print()

    print("Step 4: Merge notes into study_plan.md...")
    current_plan = read_study_plan()
    updated_plan = merge_study_plan_with_notes(
        current_plan=current_plan,
        source_name=pdf_filename,
        revision_notes=notes,
    )
    write_study_plan(updated_plan)

    print(f"Done. Updated file: {STUDY_PLAN_PATH}")


if __name__ == "__main__":
    run_demo()
