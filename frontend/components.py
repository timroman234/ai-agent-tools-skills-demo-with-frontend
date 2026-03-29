"""Reusable UI rendering components for IBM Carbon Streamlit frontends."""

import json
from html import escape
from typing import Any


def _normalize_args(raw: Any) -> dict[str, Any]:
    """Coerce tool args to a dict regardless of how they arrive."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return {"input": raw}
    if raw is None:
        return {}
    return {"value": str(raw)}


def dedup_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate tool entries, keeping the one with the richest args per name."""
    best: dict[str, dict[str, Any]] = {}
    for tool in tools:
        name = tool.get("tool_name") or tool.get("name", "unknown")
        args = _normalize_args(tool.get("args"))
        existing = best.get(name)
        if existing is None or len(args) > len(_normalize_args(existing.get("args"))):
            best[name] = tool
    return list(best.values())


def render_tool_card(tool: dict[str, Any]) -> str:
    """Return an HTML tool card showing tool name and arguments."""
    tool_name = escape(str(tool.get("tool_name") or tool.get("name", "unknown")))
    args = _normalize_args(tool.get("args"))

    args_html = ""
    for key, value in args.items():
        display_value = str(value)
        if len(display_value) > 80:
            display_value = display_value[:77] + "..."
        args_html += (
            f'<div class="tool-args">'
            f'<span class="arg-key">{escape(key)}:</span> '
            f"{escape(display_value)}"
            f"</div>"
        )

    return (
        f'<div class="tool-card">'
        f'<div class="tool-name">{tool_name}</div>'
        f"{args_html}"
        f"</div>"
    )


def render_health_indicator(
    health: dict[str, Any] | None,
    labels: list[str] | None = None,
) -> str:
    """Return HTML for health status dots in the sidebar.

    Args:
        health: Health check response dict from the API, or None if offline.
        labels: List of service labels to display (e.g., ["Database", "Cache"]).
                Each label is looked up as a key in the health dict.
                If None, displays all keys from the health dict.
    """
    if health is None:
        return (
            '<div class="health-indicator">'
            '<span class="dot-err">\u25cf</span> API offline'
            "</div>"
        )

    if labels is None:
        labels = [k for k in health.keys() if k != "status"]

    if not labels:
        # No specific checks; just show API is reachable
        return (
            '<div class="health-indicator">'
            '<span class="dot-ok">\u25cf</span> API online'
            "</div>"
        )

    parts: list[str] = []
    for label in labels:
        value = health.get(label.lower().replace(" ", "_"), False)
        is_ok = value is True or value == "connected" or value == "ok"
        dot_class = "dot-ok" if is_ok else "dot-err"
        parts.append(f'<span class="{dot_class}">\u25cf</span> {escape(label)}')

    return (
        '<div class="health-indicator">'
        + " &nbsp; ".join(parts)
        + "</div>"
    )


def render_skill_card(skill: dict[str, Any]) -> str:
    """Return an HTML skill card showing skill name and description.

    Skills define HOW the agent thinks (its persona and reasoning strategy),
    while Tools define WHAT the agent can do.
    """
    name = escape(str(skill.get("name", "Unknown Skill")))
    description = escape(str(skill.get("description", "")))

    return (
        f'<div class="skill-card">'
        f'<div class="skill-name">{name}</div>'
        f'<div class="skill-desc">{description}</div>'
        f"</div>"
    )


def render_empty_state(
    title: str = "Ask a question to get started",
    description: str = "Type your question below and press Submit.",
    examples: list[str] | None = None,
) -> str:
    """Return HTML for the empty state placeholder shown before any query.

    Args:
        title: Heading text for the empty state.
        description: Subheading description text.
        examples: Optional list of example queries to display.
    """
    example_html = ""
    if examples:
        example_html = "\n".join(
            f'<div class="example-query">{escape(q)}</div>' for q in examples
        )

    return (
        '<div class="empty-state">'
        f'<div class="empty-title">{escape(title)}</div>'
        f'<div class="empty-desc">{escape(description)}</div>'
        f"{example_html}"
        "</div>"
    )
