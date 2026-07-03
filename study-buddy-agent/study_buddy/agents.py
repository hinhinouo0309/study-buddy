"""Google ADK agent definitions for the Study Buddy multi-agent system."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from .config import get_model
from .mcp_integration import build_filesystem_mcp_toolset
from .skills import analyze_student_request
from .skills import build_study_schedule
from .skills import create_todo_reminders
from .skills import extract_text_from_pdf_base64
from .skills import generate_revision_focus
from .skills import merge_study_plan_with_notes


# Each agent gets only the MCP tools it truly needs.
# ADK launches the MCP server on demand and converts those remote MCP tools into
# normal callable tools inside the agent.
planner_mcp_tools = build_filesystem_mcp_toolset(["write_study_plan"])
research_mcp_tools = build_filesystem_mcp_toolset(
    [
        "list_pdf_files",
        "get_pdf_file_info",
        "get_pdf_file_base64",
        "extract_pdf_text",
        "read_study_plan",
        "write_study_plan",
    ]
)
reminder_mcp_tools = build_filesystem_mcp_toolset(["read_study_plan"])


# Planner Agent: handles deadlines and converts them into a usable study schedule.
planner_agent = LlmAgent(
    name="planner_agent",
    model=get_model(),
    description="Creates study timetables and deadline-aware revision plans.",
    instruction="""
You are the Planner Agent for a student study assistant.

Responsibilities:
- Read assignment details, subjects, deadlines, and available study time.
- Use the build_study_schedule skill whenever the user needs a timetable or schedule.
- After creating the final plan, use the MCP tool write_study_plan to save it into study_plan.md.
- Return a practical plan with clear time blocks and realistic priorities.
- If important details are missing, ask a short follow-up question.

Style:
- Be concise, supportive, and actionable.
- Prefer schedules that are realistic for students with limited time.
""",
    tools=[build_study_schedule, planner_mcp_tools],
)


# Research Agent: uses its own model knowledge plus a clear skill scaffold to create notes.
research_agent = LlmAgent(
    name="research_agent",
    model=get_model(),
    description="Generates revision points, topic summaries, and study notes.",
    instruction="""
You are the Research Agent for a student study assistant.

Responsibilities:
- If the user asks to study from a PDF, first use the MCP tools to detect the PDF
  inside study_materials.
- Prefer the MCP tool extract_pdf_text to extract readable text from the PDF with pypdf.
- Only use get_pdf_file_base64 plus extract_text_from_pdf_base64 if extract_pdf_text is unavailable.
- Based on the extracted text, generate revision points, key concepts, and study questions.
- Use generate_revision_focus when you need a structured first draft for the topic breakdown.
- Read the existing study_plan.md, merge the new study notes into it with
  merge_study_plan_with_notes, then save the updated markdown with write_study_plan.
- Make it easy for a student to study quickly.

Constraints:
- Do not invent citations or claim you searched the web.
- Anchor your answer to the extracted PDF text whenever a PDF is available.
""",
    tools=[
        generate_revision_focus,
        extract_text_from_pdf_base64,
        merge_study_plan_with_notes,
        research_mcp_tools,
    ],
)


# Reminder Agent: turns a plan into checklists and reminder-friendly wording.
reminder_agent = LlmAgent(
    name="reminder_agent",
    model=get_model(),
    description="Creates to-do lists, checklists, and reminder messages.",
    instruction="""
You are the Reminder Agent for a student study assistant.

Responsibilities:
- Turn goals and study tasks into a practical to-do list.
- When useful, read study_plan.md through the MCP tool read_study_plan first so the
  reminder list matches the latest saved study plan.
- Use the create_todo_reminders skill to generate a checklist and reminder messages.
- Keep output easy to scan and ready for copy-paste into a notes or reminder app.

Style:
- Keep tasks small and concrete.
- Highlight the top priority if there are too many items.
""",
    tools=[create_todo_reminders, reminder_mcp_tools],
)


# Coordinator Agent: receives the student's message and delegates to the best agent.
coordinator_agent = LlmAgent(
    name="coordinator_agent",
    model=get_model(),
    description="Main controller that routes student requests to the correct specialist agent.",
    instruction="""
You are the Coordinator Agent for Study Buddy.

You are the student's main contact point. Your job is to:
- Understand the student's request.
- Use analyze_student_request first when the request needs routing help.
- Transfer to planner_agent for schedules, deadlines, and study plans.
- Transfer to research_agent for revision notes, topic breakdowns, and study focus.
- Transfer to reminder_agent for checklists, reminders, and to-do lists.

Important behavior:
- Delegate instead of trying to do every specialist task yourself.
- If the user asks for multiple things, choose the most important first and say what you are handling.
- If the request is ambiguous, ask one short clarifying question.
""",
    tools=[
        analyze_student_request,
    ],
    sub_agents=[planner_agent, research_agent, reminder_agent],
)
