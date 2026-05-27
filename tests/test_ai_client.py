import unittest

from ai_client import AIClientError, AIOutfitClient
from weather_api import WeatherData


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, content="Wear a coat.", exception=None):
        self.content = content
        self.exception = exception
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self.exception:
            raise self.exception
        return FakeResponse(self.content)


class FakeChat:
    def __init__(self, completions):
        self.completions = completions


class FakeOpenAIClient:
    def __init__(self, completions):
        self.chat = FakeChat(completions)


class AIOutfitClientTests(unittest.TestCase):
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
        prompt = AIOutfitClient.build_prompt(self.weather)

        self.assertIn("Zurich, CH", prompt)
        self.assertIn("8C", prompt)
        self.assertIn("shoes", prompt)

    def test_generate_recommendation_calls_chat_completion(self):
        completions = FakeCompletions("Wear a warm jacket and waterproof shoes.")
        client = AIOutfitClient("openai-key", model="test-model", client=FakeOpenAIClient(completions))

        recommendation = client.generate_recommendation(self.weather)

        self.assertEqual(recommendation, "Wear a warm jacket and waterproof shoes.")
        self.assertEqual(completions.last_kwargs["model"], "test-model")
        self.assertEqual(completions.last_kwargs["messages"][0]["role"], "system")
        self.assertIn("Zurich", completions.last_kwargs["messages"][1]["content"])

    def test_generate_recommendation_wraps_client_errors(self):
        completions = FakeCompletions(exception=RuntimeError("api down"))
        client = AIOutfitClient("openai-key", client=FakeOpenAIClient(completions))

        with self.assertRaises(AIClientError):
            client.generate_recommendation(self.weather)

    def test_generate_recommendation_rejects_empty_text(self):
        completions = FakeCompletions("   ")
        client = AIOutfitClient("openai-key", client=FakeOpenAIClient(completions))

        with self.assertRaises(AIClientError):
            client.generate_recommendation(self.weather)


if __name__ == "__main__":
    unittest.main()
