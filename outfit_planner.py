"""Business workflow for weather-based outfit planning."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from ai_client import AIClientError
from weather_api import WeatherApiError, WeatherData


class WeatherProvider(Protocol):
    def get_current_weather(self, city: str) -> WeatherData:
        """Return current weather for the given city."""


class OutfitRecommendationProvider(Protocol):
    def generate_recommendation(self, weather: WeatherData) -> str:
        """Return an outfit recommendation for the given weather."""


class OutfitPlannerError(RuntimeError):
    """Raised when the outfit planning workflow fails."""


@dataclass(frozen=True)
class OutfitSuggestion:
    city: str
    weather: WeatherData
    recommendation: str

    def format_for_display(self) -> str:
        return (
            f"Weather summary:\n{self.weather.summary()}\n\n"
            f"Outfit recommendation:\n{self.recommendation}"
        )


class OutfitPlanner:
    """Coordinates weather retrieval and AI outfit generation."""

    def __init__(
        self,
        weather_provider: WeatherProvider,
        recommendation_provider: OutfitRecommendationProvider,
    ) -> None:
        self.weather_provider = weather_provider
        self.recommendation_provider = recommendation_provider

    def suggest_for_city(self, city: str) -> OutfitSuggestion:
        """Return an outfit suggestion for a city name."""

        city = city.strip()
        if not city:
            raise OutfitPlannerError("City name cannot be empty")

        try:
            weather = self.weather_provider.get_current_weather(city)
            recommendation = self.recommendation_provider.generate_recommendation(weather)
        except (WeatherApiError, AIClientError) as exc:
            raise OutfitPlannerError(str(exc)) from exc

        return OutfitSuggestion(city=city, weather=weather, recommendation=recommendation)


def save_suggestion_history(suggestion: OutfitSuggestion, history_file: Path) -> None:
    """Append a successful recommendation to a local history file."""

    history_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    entry = (
        f"[{timestamp}] {suggestion.city}\n"
        f"{suggestion.weather.summary()}\n"
        f"{suggestion.recommendation}\n\n"
    )
    with history_file.open("a", encoding="utf-8") as file:
        file.write(entry)
