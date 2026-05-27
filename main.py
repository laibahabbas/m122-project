"""Console entry point for the Smart Weather & Outfit Planner."""

from __future__ import annotations

import logging
import sys

from ai_client import AIOutfitClient
from config import ConfigurationError, load_config
from outfit_planner import OutfitPlanner, OutfitPlannerError, save_suggestion_history
from weather_api import WeatherApiClient


def main() -> int:
    try:
        config = load_config()
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logging.basicConfig(
        filename=config.log_file,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    city = input("Enter a city name: ").strip()
    if not city:
        logging.error("Empty city name entered")
        print("Error: city name cannot be empty.", file=sys.stderr)
        return 1

    planner = OutfitPlanner(
        WeatherApiClient(
            config.openweathermap_api_key,
            units=config.weather_units,
            timeout_seconds=config.request_timeout_seconds,
        ),
        AIOutfitClient(config.openai_api_key, model=config.openai_model),
    )

    try:
        suggestion = planner.suggest_for_city(city)
        save_suggestion_history(suggestion, config.history_file)
    except OutfitPlannerError as exc:
        logging.exception("Failed to create outfit suggestion")
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print()
    print(suggestion.format_for_display())
    logging.info("Created outfit suggestion for %s", city)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
