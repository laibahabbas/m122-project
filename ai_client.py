"""Gemini API integration for outfit recommendations."""

from __future__ import annotations

from typing import Any

from weather_api import WeatherData


class AIClientError(RuntimeError):
    """Raised when an outfit recommendation cannot be generated."""


class GeminiOutfitClient:
    """Client responsible for generating outfit recommendations with Gemini."""

    SYSTEM_INSTRUCTION = (
        "You are a practical outfit planner. Give concise clothing advice that fits "
        "the weather, mentions layers or waterproof items when useful, and stays "
        "within 4-6 sentences."
    )

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gemini-3.5-flash",
        client: Any | None = None,
        generation_config_factory: Any | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        self.model = model
        self.client = client or self._build_default_client(api_key)
        self.generation_config_factory = generation_config_factory or self._build_generation_config

    def generate_recommendation(self, weather: WeatherData) -> str:
        """Build a prompt from weather data and return the AI recommendation."""

        prompt = self.build_prompt(weather)
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self.generation_config_factory(self.SYSTEM_INSTRUCTION),
            )
        except Exception as exc:  # pragma: no cover - concrete SDK exceptions vary by version
            raise AIClientError("Failed to get outfit recommendation from Gemini") from exc

        recommendation = getattr(response, "text", None)

        if not recommendation or not recommendation.strip():
            raise AIClientError("Gemini returned an empty recommendation")
        return recommendation.strip()

    @staticmethod
    def build_prompt(weather: WeatherData) -> str:
        """Create the user prompt sent to Gemini."""

        return (
            "Recommend an outfit for today's weather.\n"
            f"Weather: {weather.summary()}.\n"
            "Include shoes, outerwear, and one practical accessory if relevant."
        )

    @staticmethod
    def _build_default_client(api_key: str) -> Any:
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - exercised only without installed dependency
            raise AIClientError("The google-genai package is required. Install dependencies from requirements.txt") from exc
        return genai.Client(api_key=api_key)

    @staticmethod
    def _build_generation_config(system_instruction: str) -> Any:
        try:
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - exercised only without installed dependency
            raise AIClientError("The google-genai package is required. Install dependencies from requirements.txt") from exc

        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        )
