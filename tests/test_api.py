from pathlib import Path
import unittest


class ApiRegressionTests(unittest.TestCase):
    def test_update_hourly_forecast_defaults_to_empty_list(self):
        source = Path("custom_components/qweather/api.py").read_text(encoding="utf-8")
        assert 'json_data.get("hourly", []) if json_data else []' in source


if __name__ == "__main__":
    unittest.main()
