"""Application configuration for the Smart Weather & Outfit Planner."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - only used when dependency is absent
    load_dotenv = None


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is missing or invalid."""


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings loaded from environment variables."""

    openweathermap_api_key: str
    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    weather_units: str = "metric"
    request_timeout_seconds: int = 10
    history_file: Path = Path("recommendation_history.txt")
    log_file: Path = Path("app.log")


def load_config() -> AppConfig:
    """Load and validate required configuration from environment variables."""

    if load_dotenv is not None:
        load_dotenv()

    openweathermap_api_key = _required_env("OPENWEATHERMAP_API_KEY")
    openai_api_key = _required_env("OPENAI_API_KEY")

    return AppConfig(
        openweathermap_api_key=openweathermap_api_key,
        openai_api_key=openai_api_key,
        openai_model=os.getenv("OPENAI_MODEL", AppConfig.openai_model).strip(),
        weather_units=os.getenv("WEATHER_UNITS", AppConfig.weather_units).strip(),
        request_timeout_seconds=_positive_int_env(
            "REQUEST_TIMEOUT_SECONDS",
            AppConfig.request_timeout_seconds,
        ),
        history_file=Path(os.getenv("RECOMMENDATION_HISTORY_FILE", str(AppConfig.history_file))),
        log_file=Path(os.getenv("APP_LOG_FILE", str(AppConfig.log_file))),
    )


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


def _positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a positive integer") from exc

    if value <= 0:
        raise ConfigurationError(f"{name} must be a positive integer")
    return value
