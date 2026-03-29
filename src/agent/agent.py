"""
The Agentic Loop — the engine that ties Tools and Skills together.

This module implements the core loop that:
  1. Sends the conversation (with the Skill as system prompt) to the LLM.
  2. Checks if the LLM wants to call any Tools.
  3. If yes — executes the tool(s), feeds results back, and loops.
  4. If no  — returns the final text response to the user.

This is the same pattern used by production agent frameworks.  Understanding
this loop is the single most important thing for building AI agents.
"""

import json
from typing import Callable, Generator
from openai import OpenAI

from agent.tools import TOOLS, TOOL_FUNCTIONS
from agent.skills import SKILLS, DEFAULT_SKILL, SkillDefinition

# Initialize the OpenAI client (reads OPENAI_API_KEY from environment)
client = OpenAI()

MODEL = "gpt-4o"


def run_agent(
    user_message: str,
    conversation_history: list,
    skill_id: str = DEFAULT_SKILL,
    on_tool_call: Callable[[str, dict], None] | None = None,
) -> str:
    """Run one turn of the agentic loop.

    Args:
        user_message: The latest message from the user.
        conversation_history: A mutable list of message dicts that persists
            across turns.  This function appends to it in place.
        skill_id: The skill to use (key from SKILLS dict).
        on_tool_call: Optional callback invoked when a tool is called.
            Receives (function_name, arguments).

    Returns:
        The agent's final text response.
    """
    skill = SKILLS.get(skill_id, SKILLS[DEFAULT_SKILL])

    # Append the new user message to the conversation history
    conversation_history.append({"role": "user", "content": user_message})

    # Build the full messages list: system prompt (Skill) + conversation
    messages = [
        {"role": "system", "content": skill.prompt},
        *conversation_history,
    ]

    # --- Agentic Loop ---
    MAX_ITERATIONS = 10

    for _iteration in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )

        choice = response.choices[0]
        assistant_message = choice.message

        if assistant_message.tool_calls:
            # Append the assistant's message to conversation history
            conversation_history.append(assistant_message.model_dump())
            messages.append(assistant_message.model_dump())

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name

                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                # Invoke callback if provided
                if on_tool_call:
                    on_tool_call(function_name, arguments)

                # Look up and execute the matching Python function
                tool_fn = TOOL_FUNCTIONS.get(function_name)
                if tool_fn is None:
                    result = {"error": f"Unknown tool: {function_name}"}
                else:
                    result = tool_fn(**arguments)

                # Package the result for the API
                tool_result_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
                conversation_history.append(tool_result_message)
                messages.append(tool_result_message)

            continue

        # No tool calls — final text response
        final_text = assistant_message.content or ""
        conversation_history.append({"role": "assistant", "content": final_text})
        return final_text

    return "Sorry, I had trouble completing that request. Please try again."


def run_agent_streaming(
    user_message: str,
    conversation_history: list,
    skill_id: str = DEFAULT_SKILL,
    on_tool_call: Callable[[str, dict], None] | None = None,
) -> Generator[str, None, list[dict]]:
    """Run one turn of the agentic loop with streaming response.

    Args:
        user_message: The latest message from the user.
        conversation_history: A mutable list of message dicts that persists
            across turns.  This function appends to it in place.
        skill_id: The skill to use (key from SKILLS dict).
        on_tool_call: Optional callback invoked when a tool is called.
            Receives (function_name, arguments).

    Yields:
        Text chunks as they arrive from the LLM.

    Returns:
        List of tool calls made during this turn (via generator return value).
    """
    skill = SKILLS.get(skill_id, SKILLS[DEFAULT_SKILL])
    tool_calls_made: list[dict] = []

    # Append the new user message to the conversation history
    conversation_history.append({"role": "user", "content": user_message})

    # Build the full messages list: system prompt (Skill) + conversation
    messages = [
        {"role": "system", "content": skill.prompt},
        *conversation_history,
    ]

    MAX_ITERATIONS = 10
    final_text_chunks: list[str] = []

    for _iteration in range(MAX_ITERATIONS):
        # For tool-calling iterations, we don't stream
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            stream=False,  # Non-streaming for tool iterations
        )

        choice = response.choices[0]
        assistant_message = choice.message

        if assistant_message.tool_calls:
            conversation_history.append(assistant_message.model_dump())
            messages.append(assistant_message.model_dump())

            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name

                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                # Track tool calls
                tool_calls_made.append({
                    "tool_name": function_name,
                    "args": arguments,
                })

                if on_tool_call:
                    on_tool_call(function_name, arguments)

                tool_fn = TOOL_FUNCTIONS.get(function_name)
                if tool_fn is None:
                    result = {"error": f"Unknown tool: {function_name}"}
                else:
                    result = tool_fn(**arguments)

                tool_result_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
                conversation_history.append(tool_result_message)
                messages.append(tool_result_message)

            continue

        # No tool calls — stream the final response
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                final_text_chunks.append(text)
                yield text

        # Save final response to conversation history
        final_text = "".join(final_text_chunks)
        conversation_history.append({"role": "assistant", "content": final_text})
        return tool_calls_made

    yield "Sorry, I had trouble completing that request. Please try again."
    return tool_calls_made


def get_skill_info(skill_id: str = DEFAULT_SKILL) -> SkillDefinition:
    """Get the skill definition for display."""
    return SKILLS.get(skill_id, SKILLS[DEFAULT_SKILL])
