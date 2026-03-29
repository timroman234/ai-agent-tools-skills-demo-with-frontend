"""
Skills — how the agent THINKS.

A Skill is a system prompt that shapes the agent's personality, reasoning
strategy, and output format.  Skills do NOT give the agent new capabilities
(that's what Tools do).  They change how the agent uses its existing tools
and how it communicates with the user.

You can swap skills to completely change the agent's behavior without
touching the tool code at all.  For example, the same get_weather and
get_points_of_interest tools could power a "budget backpacker" agent or a
"luxury concierge" agent — just by changing the skill prompt.
"""

from dataclasses import dataclass


@dataclass
class SkillDefinition:
    """Metadata about a skill for display in the frontend."""
    name: str           # Display name (e.g., "Day Trip Planner")
    description: str    # Shown in sidebar
    prompt: str         # System prompt sent to the LLM


# ---------------------------------------------------------------------------
# Skill Definitions
# ---------------------------------------------------------------------------

DAY_TRIP_PLANNER_SKILL = SkillDefinition(
    name="Day Trip Planner",
    description="Plans personalized day trips based on real-time weather and local points of interest. Creates structured itineraries with Morning, Afternoon, and Evening activities.",
    prompt="""\
You are City Explorer, a friendly and practical day-trip planning assistant.

When a user asks about visiting a city, you MUST:
1. Always call get_weather first to check current conditions.
2. Call get_points_of_interest for both "landmarks" and "restaurants".
3. Factor weather into every recommendation (e.g., suggest indoor activities
   if it is raining, outdoor ones if the weather is nice).
4. Respond with a structured itinerary broken into Morning, Afternoon, and
   Evening sections.

Keep your tone warm, concise, and practical.  Use the real weather data to
make your suggestions feel personal and timely.
"""
)

# Registry of all available skills
SKILLS: dict[str, SkillDefinition] = {
    "day_trip_planner": DAY_TRIP_PLANNER_SKILL,
}

# Default skill to use
DEFAULT_SKILL = "day_trip_planner"
