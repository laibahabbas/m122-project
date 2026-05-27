import tempfile
import unittest
from pathlib import Path

from ai_client import AIClientError
from outfit_planner import OutfitPlanner, OutfitPlannerError, OutfitSuggestion, save_suggestion_history
from weather_api import WeatherApiError, WeatherData


class FakeWeatherProvider:
    def __init__(self, weather=None, exception=None):
        self.weather = weather
        self.exception = exception
        self.city = None

    def get_current_weather(self, city):
        self.city = city
        if self.exception:
            raise self.exception
        return self.weather


class FakeRecommendationProvider:
    def __init__(self, recommendation="Wear layers.", exception=None):
        self.recommendation = recommendation
        self.exception = exception
        self.weather = None

    def generate_recommendation(self, weather):
        self.weather = weather
        if self.exception:
            raise self.exception
        return self.recommendation


class OutfitPlannerTests(unittest.TestCase):
    def setUp(self):
        self.weather = WeatherData(
            city="Basel",
            country="CH",
            temperature_c=18.0,
            feels_like_c=18.0,
            humidity_percent=60,
            wind_speed_mps=2.0,
            description="clear sky",
            condition="Clear",
        )

    def test_suggest_for_city_combines_weather_and_ai_result(self):
        weather_provider = FakeWeatherProvider(self.weather)
        recommendation_provider = FakeRecommendationProvider("Light jacket and sneakers.")
        planner = OutfitPlanner(weather_provider, recommendation_provider)

        suggestion = planner.suggest_for_city(" Basel ")

        self.assertEqual(weather_provider.city, "Basel")
        self.assertIs(recommendation_provider.weather, self.weather)
        self.assertEqual(suggestion.city, "Basel")
        self.assertEqual(suggestion.recommendation, "Light jacket and sneakers.")

    def test_suggest_for_city_rejects_empty_city(self):
        planner = OutfitPlanner(FakeWeatherProvider(self.weather), FakeRecommendationProvider())

        with self.assertRaises(OutfitPlannerError):
            planner.suggest_for_city(" ")

    def test_suggest_for_city_wraps_weather_errors(self):
        planner = OutfitPlanner(
            FakeWeatherProvider(exception=WeatherApiError("weather failed")),
            FakeRecommendationProvider(),
        )

        with self.assertRaises(OutfitPlannerError) as context:
            planner.suggest_for_city("Bern")

        self.assertIn("weather failed", str(context.exception))

    def test_suggest_for_city_wraps_ai_errors(self):
        planner = OutfitPlanner(
            FakeWeatherProvider(self.weather),
            FakeRecommendationProvider(exception=AIClientError("ai failed")),
        )

        with self.assertRaises(OutfitPlannerError) as context:
            planner.suggest_for_city("Bern")

        self.assertIn("ai failed", str(context.exception))

    def test_save_suggestion_history_appends_entry(self):
        suggestion = OutfitSuggestion("Basel", self.weather, "Light jacket.")

        with tempfile.TemporaryDirectory() as directory:
            history_file = Path(directory) / "history.txt"
            save_suggestion_history(suggestion, history_file)

            content = history_file.read_text(encoding="utf-8")

        self.assertIn("Basel", content)
        self.assertIn("Light jacket.", content)
        self.assertIn("clear sky", content)


if __name__ == "__main__":
    unittest.main()
