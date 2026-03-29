"""Frontend configuration for the Streamlit app.

All placeholder values are replaced by the /carbon-streamlit skill
when generating a project-specific frontend.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (one level up from frontend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


@dataclass
class FrontendConfig:
    """Configuration for the Streamlit frontend."""

    app_title: str = "City Explorer"
    app_subtitle: str = "AI-powered day trip planning with real weather data"
    page_icon: str = "\U0001F5FA"  # World map emoji
    input_placeholder: str = "Ask about a city to explore..."
    sidebar_title: str = "Agent Activity"
    request_timeout: float = 120.0
    api_base_url: str = field(default_factory=lambda: "")

    # Example queries shown in the empty state
    example_queries: list[str] = field(default_factory=lambda: [
        "Plan a day trip to Paris",
        "What should I do in Tokyo today?",
        "Recommend activities in New York",
    ])

    # Health check service labels (looked up in the /health response)
    health_labels: list[str] = field(default_factory=lambda: ["API"])

    def __post_init__(self) -> None:
        if not self.api_base_url:
            override = os.getenv("API_BASE_URL")
            if override:
                self.api_base_url = override.rstrip("/")
            else:
                port = os.getenv("APP_PORT", "8058")
                self.api_base_url = f"http://localhost:{port}"


config = FrontendConfig()
