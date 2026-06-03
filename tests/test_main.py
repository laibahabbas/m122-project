import unittest
from unittest.mock import patch

import main
from config import ConfigurationError


class MainTests(unittest.TestCase):
    def test_main_returns_error_when_configuration_is_invalid(self):
        with patch("main.load_config", side_effect=ConfigurationError("missing key")):
            with patch("sys.stderr") as stderr:
                exit_code = main.main()

        self.assertEqual(exit_code, 1)
        stderr.write.assert_called()


if __name__ == "__main__":
    unittest.main()
