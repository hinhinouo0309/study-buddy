"""Local filesystem MCP server for the Study Buddy project.

This server runs as a separate subprocess. Google ADK launches it over STDIO
when an agent needs filesystem tools. The MCP protocol uses stdin/stdout for
JSON-RPC messages, so avoid normal print() logging in this file.
"""

from __future__ import annotations

import base64
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pypdf import PdfReader

from .config import PROJECT_ROOT
from .config import STUDY_MATERIALS_DIR
from .config import STUDY_PLAN_PATH
from .config import ensure_project_directories


mcp = FastMCP(
    "study-buddy-filesystem",
    instructions=(
        "Filesystem MCP server for the Study Buddy project. "
        "It can write study plans, read the saved plan, and discover PDF files "
        "under the study_materials folder."
    ),
)


def _safe_path_from_root(relative_path: str) -> Path:
    """Resolve a path inside the project and reject path traversal."""
    candidate = (PROJECT_ROOT / relative_path).resolve()
    if PROJECT_ROOT.resolve() not in [candidate, *candidate.parents]:
        raise ValueError("Path must stay inside the Study Buddy project folder.")
    return candidate


def _safe_path_from_materials(relative_path: str) -> Path:
    """Resolve a path inside the study materials folder only."""
    candidate = (STUDY_MATERIALS_DIR / relative_path).resolve()
    if STUDY_MATERIALS_DIR.resolve() not in [candidate, *candidate.parents]:
        raise ValueError("Path must stay inside the study_materials folder.")
    return candidate


@mcp.tool()
def write_study_plan(markdown: str) -> str:
    """Write the latest study plan into study_plan.md in the project root."""
    ensure_project_directories()
    STUDY_PLAN_PATH.write_text(markdown, encoding="utf-8")
    return f"Study plan saved to {STUDY_PLAN_PATH}"


@mcp.tool()
def read_study_plan() -> str:
    """Read the saved study_plan.md content for reminder generation."""
    ensure_project_directories()
    if not STUDY_PLAN_PATH.exists():
        return "study_plan.md does not exist yet."
    return STUDY_PLAN_PATH.read_text(encoding="utf-8")


@mcp.tool()
def list_pdf_files(relative_folder: str = ".") -> str:
    """List PDF files inside the study_materials folder or a subfolder."""
    ensure_project_directories()
    target_dir = _safe_path_from_materials(relative_folder)
    if not target_dir.exists():
        return f"Folder not found: {target_dir}"
    if not target_dir.is_dir():
        return f"Not a folder: {target_dir}"

    pdfs = sorted(target_dir.rglob("*.pdf"))
    if not pdfs:
        return "No PDF files found."

    lines = ["PDF files found:"]
    materials_root = STUDY_MATERIALS_DIR.resolve()
    for pdf in pdfs:
        relative = pdf.resolve().relative_to(materials_root)
        size_kb = round(pdf.stat().st_size / 1024, 1)
        lines.append(f"- {relative.as_posix()} ({size_kb} KB)")
    return "\n".join(lines)


@mcp.tool()
def get_pdf_file_info(relative_path: str) -> str:
    """Return metadata for one PDF file inside study_materials."""
    ensure_project_directories()
    pdf_path = _safe_path_from_materials(relative_path)
    if not pdf_path.exists():
        return f"PDF file not found: {pdf_path}"
    if pdf_path.suffix.lower() != ".pdf":
        return "The requested file is not a PDF."

    stat = pdf_path.stat()
    return (
        f"PDF file: {pdf_path.name}\n"
        f"Absolute path: {pdf_path}\n"
        f"Size bytes: {stat.st_size}\n"
        f"Modified: {stat.st_mtime}"
    )


@mcp.tool()
def get_pdf_file_base64(relative_path: str) -> str:
    """Return a PDF file as base64 text so an agent can retrieve the file payload."""
    ensure_project_directories()
    pdf_path = _safe_path_from_materials(relative_path)
    if not pdf_path.exists():
        return f"PDF file not found: {pdf_path}"
    if pdf_path.suffix.lower() != ".pdf":
        return "The requested file is not a PDF."

    encoded = base64.b64encode(pdf_path.read_bytes()).decode("ascii")
    return (
        f"filename={pdf_path.name}\n"
        f"encoding=base64\n"
        f"content={encoded}"
    )


@mcp.tool()
def extract_pdf_text(relative_path: str, max_chars: int = 12000) -> str:
    """Extract readable text from a PDF inside study_materials using pypdf.

    This avoids sending the full PDF bytes through the LLM. The agent still uses
    the filesystem MCP server to access the file, while the server performs the
    heavy PDF parsing locally and returns only extracted text.
    """
    ensure_project_directories()
    pdf_path = _safe_path_from_materials(relative_path)
    if not pdf_path.exists():
        return f"PDF file not found: {pdf_path}"
    if pdf_path.suffix.lower() != ".pdf":
        return "The requested file is not a PDF."

    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if page_text:
            pages.append(f"[Page {index}]\n{page_text}")

    if not pages:
        return f"PDF {pdf_path.name} was loaded, but no extractable text was found."

    full_text = "\n\n".join(pages)
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars] + "\n\n[Truncated for analysis]"

    return f"Source PDF: {pdf_path.name}\n\n{full_text}"


@mcp.tool()
def read_text_file(relative_path: str) -> str:
    """Read a UTF-8 text file inside the project root."""
    target = _safe_path_from_root(relative_path)
    if not target.exists():
        return f"File not found: {target}"
    return target.read_text(encoding="utf-8")


if __name__ == "__main__":
    ensure_project_directories()
    mcp.run()
