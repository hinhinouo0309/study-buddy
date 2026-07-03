"""Tool functions used as clear skills by each Study Buddy agent."""

from __future__ import annotations

import base64
from io import BytesIO
from datetime import datetime, timedelta


def analyze_student_request(request: str) -> str:
    """Coordinator skill: classify the student's request before delegation."""
    lowered = request.lower()

    if any(word in lowered for word in ("deadline", "schedule", "plan", "timetable", "安排", "時間表")):
        route = "planner_agent"
        reason = "The user is asking for study planning or deadline management."
    elif any(word in lowered for word in ("summary", "notes", "revise", "topic", "重點", "溫習")):
        route = "research_agent"
        reason = "The user wants study notes, explanations, or revision focus."
    elif any(word in lowered for word in ("todo", "to-do", "remind", "checklist", "提醒", "清單")):
        route = "reminder_agent"
        reason = "The user needs a to-do list or reminders."
    else:
        route = "research_agent"
        reason = "Default to research support when the intent is broad or unclear."

    return (
        f"Suggested route: {route}\n"
        f"Reason: {reason}\n"
        "The coordinator should still read the full request before deciding."
    )


def build_study_schedule(
    course: str,
    assignment: str,
    deadline: str,
    available_days: int = 5,
    daily_hours: float = 1.5,
) -> str:
    """Planner skill: build a simple schedule scaffold from a deadline."""
    try:
        due_date = datetime.fromisoformat(deadline)
    except ValueError:
        return (
            "Invalid deadline format. Please use ISO date format like 2026-07-15 "
            "or 2026-07-15T18:00:00."
        )

    start_date = datetime.now()
    usable_days = max(1, available_days)
    total_hours = round(usable_days * daily_hours, 1)
    topics_per_day = [
        "Review class notes",
        "Summarize key concepts",
        "Practice past-paper style questions",
        "Fix weak areas",
        "Final revision and self-test",
    ]

    lines = [
        f"Course: {course}",
        f"Assignment / target: {assignment}",
        f"Deadline: {due_date.strftime('%Y-%m-%d %H:%M')}",
        f"Suggested study window: {usable_days} day(s)",
        f"Suggested daily study time: {daily_hours} hour(s)",
        f"Estimated total study time: {total_hours} hour(s)",
        "",
        "Draft schedule:",
    ]

    for index in range(usable_days):
        study_day = start_date + timedelta(days=index)
        task = topics_per_day[index % len(topics_per_day)]
        lines.append(
            f"- Day {index + 1} ({study_day.strftime('%Y-%m-%d')}): "
            f"{task} for {course} ({daily_hours}h)"
        )

    lines.extend(
        [
            "",
            "Adjustment tips:",
            "- Bring forward practice sessions if the assignment is calculation-heavy.",
            "- Reserve the last study block for mock questions and error review.",
            "- If the deadline is very near, merge note review and practice on the same day.",
        ]
    )
    return "\n".join(lines)


def generate_revision_focus(
    subject: str,
    topics: str,
    student_level: str = "secondary school",
) -> str:
    """Research skill: generate a revision brief using the model's own knowledge."""
    topic_items = [item.strip() for item in topics.split(",") if item.strip()]
    if not topic_items:
        topic_items = ["core concepts", "definitions", "worked examples"]

    lines = [
        f"Subject: {subject}",
        f"Student level: {student_level}",
        "Suggested revision focus:",
    ]

    for index, topic in enumerate(topic_items, start=1):
        lines.extend(
            [
                f"{index}. {topic}",
                f"   - What to understand: the core idea behind {topic}.",
                f"   - What to memorize: important terms, formulas, or frameworks for {topic}.",
                f"   - What to practise: one short-answer and one applied question on {topic}.",
            ]
        )

    lines.extend(
        [
            "",
            "Study advice:",
            "- Start from class notes, then test yourself without looking.",
            "- Turn each topic into 3 to 5 flashcard-style questions.",
            "- Spend more time on topics you cannot explain in your own words.",
        ]
    )
    return "\n".join(lines)


def extract_text_from_pdf_base64(pdf_payload: str, max_chars: int = 12000) -> str:
    """Research skill: extract text from a base64-encoded PDF payload.

    The MCP server returns PDF data in a simple text envelope:
    - filename=<name>
    - encoding=base64
    - content=<base64 bytes>

    This skill decodes that payload and uses pypdf to extract text for the
    Research Agent to analyze.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - runtime guidance
        raise RuntimeError(
            "Missing dependency 'pypdf'. Install it with: pip install pypdf"
        ) from exc

    parsed: dict[str, str] = {}
    for line in pdf_payload.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            parsed[key.strip()] = value.strip()

    encoded = parsed.get("content")
    filename = parsed.get("filename", "unknown.pdf")
    if not encoded:
        return "No base64 PDF content was found in the MCP response."

    pdf_bytes = base64.b64decode(encoded)
    reader = PdfReader(BytesIO(pdf_bytes))

    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if page_text:
            pages.append(f"[Page {index}]\n{page_text}")

    if not pages:
        return f"PDF {filename} was loaded, but no extractable text was found."

    full_text = "\n\n".join(pages)
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars] + "\n\n[Truncated for analysis]"

    return f"Source PDF: {filename}\n\n{full_text}"


def merge_study_plan_with_notes(
    current_plan: str,
    source_name: str,
    revision_notes: str,
) -> str:
    """Research skill: merge newly generated revision notes into study_plan.md.

    The Research Agent can call this after it has summarized the extracted PDF
    text. The returned markdown is ready to be written back through MCP.
    """
    section_title = f"## Revision Notes from {source_name}"
    new_section = f"{section_title}\n\n{revision_notes.strip()}\n"

    if not current_plan or "does not exist yet" in current_plan.lower():
        return "# Study Plan\n\n" + new_section

    if section_title in current_plan:
        before, _, after = current_plan.partition(section_title)
        if "\n## " in after:
            _, next_section = after.split("\n## ", 1)
            return before.rstrip() + "\n\n" + new_section + "\n## " + next_section
        return before.rstrip() + "\n\n" + new_section

    return current_plan.rstrip() + "\n\n" + new_section


def create_todo_reminders(
    goal: str,
    tasks: str,
    reminder_style: str = "daily checklist",
) -> str:
    """Reminder skill: turn raw tasks into a to-do list with reminder wording."""
    task_items = [item.strip() for item in tasks.split(",") if item.strip()]
    if not task_items:
        task_items = ["Review notes", "Do one practice set", "Check tomorrow's target"]

    lines = [
        f"Goal: {goal}",
        f"Reminder style: {reminder_style}",
        "To-do list:",
    ]

    for index, task in enumerate(task_items, start=1):
        lines.append(f"{index}. [ ] {task}")

    lines.extend(
        [
            "",
            "Reminder messages:",
            f"- Morning: Focus on today's top task for {goal}.",
            f"- Afternoon: Quick check-in: have you completed at least one task for {goal}?",
            f"- Evening: Review what is done and prepare the next step for {goal}.",
        ]
    )
    return "\n".join(lines)
