import unittest

import requests

from weather_api import WeatherApiClient, WeatherApiError, WeatherData


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.last_request = None

    def get(self, url, params, timeout):
        self.last_request = {"url": url, "params": params, "timeout": timeout}
        if self.exception:
            raise self.exception
        return self.response


class WeatherApiClientTests(unittest.TestCase):
    def test_get_current_weather_sends_request_and_parses_response(self):
        payload = {
            "name": "Zurich",
            "sys": {"country": "CH"},
            "main": {"temp": 12.4, "feels_like": 11.8, "humidity": 81},
            "wind": {"speed": 3.2},
            "weather": [{"main": "Rain", "description": "light rain"}],
            "rain": {"1h": 0.6},
        }
        session = FakeSession(FakeResponse(payload=payload))
        client = WeatherApiClient("weather-key", session=session, timeout_seconds=7)

        weather = client.get_current_weather(" Zurich ")

        self.assertEqual(
            session.last_request["params"],
            {"q": "Zurich", "appid": "weather-key", "units": "metric"},
        )
        self.assertEqual(session.last_request["timeout"], 7)
        self.assertEqual(
            weather,
            WeatherData(
                city="Zurich",
                country="CH",
                temperature_c=12.4,
                feels_like_c=11.8,
                humidity_percent=81,
                wind_speed_mps=3.2,
                description="light rain",
                condition="Rain",
                rain_mm=0.6,
            ),
        )

    def test_get_current_weather_raises_api_message_for_non_success_status(self):
        session = FakeSession(FakeResponse(status_code=404, payload={"message": "city not found"}))
        client = WeatherApiClient("weather-key", session=session)

        with self.assertRaises(WeatherApiError) as context:
            client.get_current_weather("Atlantis")

        self.assertIn("city not found", str(context.exception))

    def test_get_current_weather_wraps_network_errors(self):
        session = FakeSession(exception=requests.Timeout("slow"))
        client = WeatherApiClient("weather-key", session=session)

        with self.assertRaises(WeatherApiError) as context:
            client.get_current_weather("Paris")

        self.assertIn("Failed to connect", str(context.exception))

    def test_parse_weather_response_rejects_missing_fields(self):
        with self.assertRaises(WeatherApiError):
            WeatherApiClient.parse_weather_response({"name": "Broken"})


if __name__ == "__main__":
    unittest.main()
