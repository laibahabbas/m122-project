import unittest

from ai_client import AIClientError, GeminiOutfitClient
from weather_api import WeatherData


class FakeGeminiResponse:
    def __init__(self, content):
        self.text = content


class FakeModels:
    def __init__(self, content="Wear a coat.", exception=None, exceptions=None):
        self.content = content
        self.exception = exception
        self.exceptions = list(exceptions or [])
        self.last_kwargs = None
        self.calls = []

    def generate_content(self, **kwargs):
        self.last_kwargs = kwargs
        self.calls.append(kwargs)
        if self.exceptions:
            exception = self.exceptions.pop(0)
            if exception:
                raise exception
        if self.exception:
            raise self.exception
        return FakeGeminiResponse(self.content)


class FakeGeminiClient:
    def __init__(self, models):
        self.models = models


class GeminiOutfitClientTests(unittest.TestCase):
    def setUp(self):
        self.weather = WeatherData(
            city="Zurich",
            country="CH",
            temperature_c=8.0,
            feels_like_c=5.5,
            humidity_percent=70,
            wind_speed_mps=4.0,
            description="overcast clouds",
            condition="Clouds",
        )

    def test_build_prompt_contains_weather_details(self):
        prompt = GeminiOutfitClient.build_prompt(self.weather)

        self.assertIn("Zurich, CH", prompt)
        self.assertIn("8C", prompt)
        self.assertIn("shoes", prompt)

    def test_generate_recommendation_calls_gemini_content_generation(self):
        models = FakeModels("Wear a warm jacket and waterproof shoes.")
        client = GeminiOutfitClient(
            "gemini-key",
            model="test-model",
            client=FakeGeminiClient(models),
            generation_config_factory=lambda instruction: {"system_instruction": instruction, "temperature": 0.7},
        )

        recommendation = client.generate_recommendation(self.weather)

        self.assertEqual(recommendation, "Wear a warm jacket and waterproof shoes.")
        self.assertEqual(models.last_kwargs["model"], "test-model")
        self.assertIn("Zurich", models.last_kwargs["contents"])
        self.assertEqual(
            models.last_kwargs["config"]["system_instruction"],
            GeminiOutfitClient.SYSTEM_INSTRUCTION,
        )

    def test_generate_recommendation_tries_fallback_model_after_error(self):
        models = FakeModels(
            "Wear a rain jacket.",
            exceptions=[RuntimeError("high demand"), None],
        )
        client = GeminiOutfitClient(
            "gemini-key",
            model="primary-model",
            fallback_models=("fallback-model",),
            client=FakeGeminiClient(models),
            generation_config_factory=lambda instruction: {"system_instruction": instruction},
        )

        recommendation = client.generate_recommendation(self.weather)

        self.assertEqual(recommendation, "Wear a rain jacket.")
        self.assertEqual([call["model"] for call in models.calls], ["primary-model", "fallback-model"])

    def test_generate_recommendation_wraps_client_errors(self):
        models = FakeModels(exception=RuntimeError("api down"))
        client = GeminiOutfitClient(
            "gemini-key",
            client=FakeGeminiClient(models),
            generation_config_factory=lambda instruction: {"system_instruction": instruction},
        )

        with self.assertRaises(AIClientError):
            client.generate_recommendation(self.weather)

    def test_generate_recommendation_rejects_empty_text(self):
        models = FakeModels("   ")
        client = GeminiOutfitClient(
            "gemini-key",
            client=FakeGeminiClient(models),
            generation_config_factory=lambda instruction: {"system_instruction": instruction},
        )

        with self.assertRaises(AIClientError):
            client.generate_recommendation(self.weather)


if __name__ == "__main__":
    unittest.main()
