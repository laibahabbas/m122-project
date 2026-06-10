"""OpenWeatherMap API integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class WeatherApiError(RuntimeError):
    """Raised when weather data cannot be fetched or parsed."""


@dataclass(frozen=True)
class WeatherData:
    """Clean weather data used by the rest of the application."""

    city: str
    country: str
    temperature_c: float
    feels_like_c: float
    humidity_percent: int
    wind_speed_mps: float
    description: str
    condition: str
    rain_mm: float = 0.0
    snow_mm: float = 0.0

    def summary(self) -> str:
        precipitation = []
        if self.rain_mm:
            precipitation.append(f"rain {self.rain_mm:g} mm")
        if self.snow_mm:
            precipitation.append(f"snow {self.snow_mm:g} mm")
        precipitation_text = ", ".join(precipitation) if precipitation else "no rain or snow"

        return (
            f"{self.city}, {self.country}: {self.description}, "
            f"{self.temperature_c:g}C (feels like {self.feels_like_c:g}C), "
            f"humidity {self.humidity_percent}%, wind {self.wind_speed_mps:g} m/s, "
            f"{precipitation_text}"
        )


class WeatherApiClient:
    """Client for the OpenWeatherMap current weather endpoint."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(
        self,
        api_key: str,
        *,
        units: str = "metric",
        timeout_seconds: int = 10,
        session: Any | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.units = units
        self.timeout_seconds = timeout_seconds
        self.session = session

    def get_current_weather(self, city: str) -> WeatherData:
        """Fetch and parse current weather for a city."""

        city = city.strip()
        if not city:
            raise WeatherApiError("City name cannot be empty")

        requests = _requests()
        session = self.session or requests.Session()

        try:
            response = session.get(
                self.BASE_URL,
                params={"q": city, "appid": self.api_key, "units": self.units},
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise WeatherApiError("Failed to connect to OpenWeatherMap") from exc

        if response.status_code != 200:
            raise WeatherApiError(_api_error_message(response))

        try:
            payload = response.json()
        except ValueError as exc:
            raise WeatherApiError("OpenWeatherMap returned invalid JSON") from exc

        return self.parse_weather_response(payload)

    @staticmethod
    def parse_weather_response(payload: Mapping[str, Any]) -> WeatherData:
        """Convert an OpenWeatherMap response into a WeatherData object."""

        try:
            weather = payload["weather"][0]
            main = payload["main"]
            wind = payload.get("wind", {})
            sys = payload.get("sys", {})

            return WeatherData(
                city=str(payload["name"]),
                country=str(sys.get("country", "Unknown")),
                temperature_c=float(main["temp"]),
                feels_like_c=float(main["feels_like"]),
                humidity_percent=int(main["humidity"]),
                wind_speed_mps=float(wind.get("speed", 0.0)),
                description=str(weather["description"]),
                condition=str(weather["main"]),
                rain_mm=_precipitation_amount(payload.get("rain", {})),
                snow_mm=_precipitation_amount(payload.get("snow", {})),
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise WeatherApiError("OpenWeatherMap response is missing required weather data") from exc


def _api_error_message(response: Any) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    message = payload.get("message") if isinstance(payload, dict) else None
    if message:
        return f"OpenWeatherMap error ({response.status_code}): {message}"
    return f"OpenWeatherMap error ({response.status_code})"


def _precipitation_amount(value: Any) -> float:
    if not isinstance(value, Mapping):
        return 0.0
    raw_amount = value.get("1h", value.get("3h", 0.0))
    try:
        return float(raw_amount)
    except (TypeError, ValueError):
        return 0.0


def _requests() -> Any:
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - exercised only without installed dependency
        raise WeatherApiError("The requests package is required. Install dependencies from requirements.txt") from exc
    return requests
