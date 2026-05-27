"""ChatGPT API integration for outfit recommendations."""

from __future__ import annotations

from typing import Any

from weather_api import WeatherData


class AIClientError(RuntimeError):
    """Raised when an outfit recommendation cannot be generated."""


class AIOutfitClient:
    """Client responsible for generating outfit recommendations with ChatGPT."""

    SYSTEM_MESSAGE = (
        "You are a practical outfit planner. Give concise clothing advice that fits "
        "the weather, mentions layers or waterproof items when useful, and stays "
        "within 4-6 sentences."
    )

    def __init__(self, api_key: str, *, model: str = "gpt-4.1-mini", client: Any | None = None) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        self.model = model
        self.client = client or self._build_default_client(api_key)

    def generate_recommendation(self, weather: WeatherData) -> str:
        """Build a prompt from weather data and return the AI recommendation."""

        prompt = self.build_prompt(weather)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
        except Exception as exc:  # pragma: no cover - concrete SDK exceptions vary by version
            raise AIClientError("Failed to get outfit recommendation from ChatGPT") from exc

        try:
            recommendation = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise AIClientError("ChatGPT response did not contain a recommendation") from exc

        if not recommendation or not recommendation.strip():
            raise AIClientError("ChatGPT returned an empty recommendation")
        return recommendation.strip()

    @staticmethod
    def build_prompt(weather: WeatherData) -> str:
        """Create the user prompt sent to ChatGPT."""

        return (
            "Recommend an outfit for today's weather.\n"
            f"Weather: {weather.summary()}.\n"
            "Include shoes, outerwear, and one practical accessory if relevant."
        )

    @staticmethod
    def _build_default_client(api_key: str) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - exercised only without installed dependency
            raise AIClientError("The openai package is required. Install dependencies from requirements.txt") from exc
        return OpenAI(api_key=api_key)
