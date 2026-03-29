"""IBM Carbon-styled Streamlit frontend with multi-turn chat and SSE streaming.

This app demonstrates the difference between AI Agent Skills and Tools:
- Skills define HOW the agent thinks (persona, reasoning strategy)
- Tools define WHAT the agent can do (actual capabilities)

Run with:
    cd frontend
    streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from api_client import check_health, stream_chat
from components import (
    dedup_tools,
    render_health_indicator,
    render_skill_card,
    render_tool_card,
)
from config import config
from styles import get_carbon_css

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title=config.app_title,
    page_icon=config.page_icon,
    layout="centered",
    initial_sidebar_state="auto",
)

st.markdown(get_carbon_css(), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cached health check (defined at module level to avoid redefinition)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=30)
def _cached_health(base_url: str) -> dict | None:
    return check_health(base_url)


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

_DEFAULTS: dict = {
    "session_id": None,
    "messages": [],  # List of {"role": "user"|"assistant", "content": str}
    "active_skill": None,  # {"name": str, "description": str}
    "last_tools": [],
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# Sidebar with separate sections for Skill and Tools
# ---------------------------------------------------------------------------

with st.sidebar:
    # Active Skill section
    st.markdown("## Active Skill")

    if st.session_state.active_skill:
        st.markdown(
            render_skill_card(st.session_state.active_skill),
            unsafe_allow_html=True,
        )
    else:
        st.caption("The active skill will appear here after your first query.")

    st.markdown("---")

    # Tools Used section
    st.markdown("## Tools Used")

    if st.session_state.last_tools:
        for tool in dedup_tools(st.session_state.last_tools):
            st.markdown(render_tool_card(tool), unsafe_allow_html=True)
    else:
        st.caption("Tools invoked during the last query will appear here.")

    st.markdown("---")

    # New Chat button
    if st.button("New Chat"):
        for key, default in _DEFAULTS.items():
            st.session_state[key] = default
        st.rerun()

    st.markdown("---")

    # Health indicator
    health = _cached_health(config.api_base_url)
    st.markdown(
        render_health_indicator(health, config.health_labels),
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main area - header
# ---------------------------------------------------------------------------

# Optional logo support
_logo = Path(__file__).parent / "logo.png"
if _logo.exists():
    _col1, _col2, _col3 = st.columns([1, 0.5, 1])
    with _col2:
        st.image(str(_logo), width=120)

st.title(config.app_title)
st.markdown(f'<p class="subtitle">{config.app_subtitle}</p>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chat input (right below title/subtitle)
# ---------------------------------------------------------------------------

with st.form("chat_form", clear_on_submit=True):
    prompt = st.text_input(
        "Query",
        placeholder=config.input_placeholder,
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Go")

# ---------------------------------------------------------------------------
# Example queries (shown only before first message)
# ---------------------------------------------------------------------------

if not st.session_state.messages:
    st.markdown(
        "<div style='margin-top: 0.5rem; color: #6f6f6f; font-size: 0.85rem;'>Try asking:</div>",
        unsafe_allow_html=True,
    )
    for example in config.example_queries:
        st.markdown(
            f"<div style='font-size: 0.8rem; color: #525252; background: #f4f4f4; "
            f"padding: 0.4rem 0.75rem; margin: 0.25rem 0; border-left: 2px solid #0f62fe;'>{example}</div>",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Chat history display
# ---------------------------------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Handle submission
# ---------------------------------------------------------------------------

if submitted and prompt.strip():
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt.strip()})

    # Stream assistant response
    text_generator, result = stream_chat(
        base_url=config.api_base_url,
        message=prompt.strip(),
        session_id=st.session_state.session_id,
        timeout=config.request_timeout,
    )

    # Consume the stream and collect full text
    full_response = ""
    with st.chat_message("assistant"):
        full_response = st.write_stream(text_generator)

        if result.error:
            st.error(result.error)
            full_response = f"Error: {result.error}"

    # Update session state
    st.session_state.session_id = result.session_id or st.session_state.session_id
    st.session_state.messages.append({"role": "assistant", "content": full_response or result.full_text})
    st.session_state.last_tools = result.tools

    # Update active skill if provided
    if result.skill:
        st.session_state.active_skill = result.skill

    # Rerun to update sidebar and show messages properly
    st.rerun()
