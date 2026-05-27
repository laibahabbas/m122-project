import os
import unittest
from unittest.mock import patch

from config import ConfigurationError, load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_reads_required_api_keys(self):
        env = {
            "OPENWEATHERMAP_API_KEY": "weather-key",
            "OPENAI_API_KEY": "openai-key",
            "OPENAI_MODEL": "test-model",
            "REQUEST_TIMEOUT_SECONDS": "15",
        }

        with patch.dict(os.environ, env, clear=True):
            config = load_config()

        self.assertEqual(config.openweathermap_api_key, "weather-key")
        self.assertEqual(config.openai_api_key, "openai-key")
        self.assertEqual(config.openai_model, "test-model")
        self.assertEqual(config.request_timeout_seconds, 15)

    def test_load_config_fails_when_required_key_is_missing(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key"}, clear=True):
            with self.assertRaises(ConfigurationError) as context:
                load_config()

        self.assertIn("OPENWEATHERMAP_API_KEY", str(context.exception))

    def test_load_config_rejects_invalid_timeout(self):
        env = {
            "OPENWEATHERMAP_API_KEY": "weather-key",
            "OPENAI_API_KEY": "openai-key",
            "REQUEST_TIMEOUT_SECONDS": "zero",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ConfigurationError):
                load_config()


if __name__ == "__main__":
    unittest.main()
