"""Helpers for connecting Google ADK agents to the local MCP filesystem server."""

from __future__ import annotations

import os
import sys

from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

from .config import PROJECT_ROOT

try:
    from mcp import StdioServerParameters
except ImportError as exc:  # pragma: no cover - helpful runtime guidance
    raise RuntimeError(
        "The Python package 'mcp' is required for the local filesystem MCP server. "
        "Install it with: pip install mcp"
    ) from exc


def build_filesystem_mcp_toolset(tool_filter: list[str]) -> McpToolset:
    """Create an ADK McpToolset that launches the local filesystem server.

    How it works:
    1. ADK starts `python -m study_buddy.mcp_server` as a child process.
    2. ADK and the MCP server communicate over stdin/stdout using the MCP protocol.
    3. Only the tool names in `tool_filter` are exposed to the target agent.
    """
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["-m", "study_buddy.mcp_server"],
                env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
            ),
            timeout=20,
        ),
        tool_filter=tool_filter,
    )
