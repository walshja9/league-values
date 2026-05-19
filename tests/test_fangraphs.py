import json
import unittest
from unittest.mock import patch, MagicMock

from scraper.fangraphs import fetch_projections, fetch_all, PROJECTION_URL


class TestFetchProjections(unittest.TestCase):
    def _mock_response(self, data):
        mock = MagicMock()
        mock.read.return_value = json.dumps(data).encode("utf-8")
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        return mock

    @patch("scraper.fangraphs.urlopen")
    def test_fetch_returns_list_of_dicts(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response([
            {"PlayerName": "Test Player", "Team": "NYY", "HR": 30, "playerids": "12345"},
        ])
        result = fetch_projections("steamer", "bat")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["PlayerName"], "Test Player")

    @patch("scraper.fangraphs.urlopen")
    def test_fetch_builds_correct_url(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response([])
        fetch_projections("zips", "pit")
        called_url = mock_urlopen.call_args[0][0].full_url
        self.assertIn("type=zips", called_url)
        self.assertIn("stats=pit", called_url)

    @patch("scraper.fangraphs.urlopen")
    def test_fetch_all_returns_four_keys(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response([])
        result = fetch_all(delay=0)
        self.assertEqual(set(result.keys()), {
            "steamer_hitters", "steamer_pitchers",
            "zips_hitters", "zips_pitchers",
        })

    def test_projection_url_format(self):
        self.assertIn("fangraphs.com/api/projections", PROJECTION_URL)


if __name__ == "__main__":
    unittest.main()
