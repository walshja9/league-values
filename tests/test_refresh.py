import json
import os
import tempfile
import unittest
from unittest.mock import patch

from scraper.refresh import refresh


class TestRefresh(unittest.TestCase):
    @patch("scraper.refresh.fetch_all")
    def test_refresh_writes_current_json(self, mock_fetch):
        mock_fetch.return_value = {
            "steamer_hitters": [
                {"playerids": "1", "PlayerName": "Test", "Team": "NYY",
                 "PA": 600, "AB": 540, "H": 162, "HR": 30, "R": 90, "RBI": 85,
                 "SB": 10, "SO": 120, "BB": 55, "AVG": 0.300, "OBP": 0.370,
                 "SLG": 0.500, "OPS": 0.870},
            ],
            "steamer_pitchers": [],
            "zips_hitters": [],
            "zips_pitchers": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "current.json")
            raw_dir = os.path.join(tmpdir, "raw")
            refresh(output_path=output, raw_dir=raw_dir, delay=0)
            self.assertTrue(os.path.exists(output))
            with open(output) as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["name"], "Test")

    @patch("scraper.refresh.fetch_all")
    def test_refresh_saves_raw_files(self, mock_fetch):
        mock_fetch.return_value = {
            "steamer_hitters": [{"playerids": "1", "PlayerName": "A", "Team": "X"}],
            "steamer_pitchers": [],
            "zips_hitters": [],
            "zips_pitchers": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "current.json")
            raw_dir = os.path.join(tmpdir, "raw")
            refresh(output_path=output, raw_dir=raw_dir, delay=0)
            self.assertTrue(os.path.exists(os.path.join(raw_dir, "steamer_hitters.json")))


if __name__ == "__main__":
    unittest.main()
