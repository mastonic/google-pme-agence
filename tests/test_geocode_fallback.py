import unittest
from unittest.mock import patch, Mock

from backend.services.google_maps import GoogleMapsService


class GeocodeFallbackTests(unittest.TestCase):
    @patch("backend.services.google_maps.requests.get")
    def test_falls_back_to_nominatim_when_google_fails(self, mock_get):
        google = Mock()
        google.status_code = 200
        google.json.return_value = {"status": "REQUEST_DENIED", "error_message": "Geocoding API not enabled"}

        osm = Mock()
        osm.status_code = 200
        osm.json.return_value = [{
            "lat": "48.7765",
            "lon": "2.0020",
            "display_name": "Trappes, Yvelines, France",
        }]
        mock_get.side_effect = [google, osm]

        svc = GoogleMapsService()
        svc.api_key = "fake-key"
        result = svc.geocode("Trappes")

        self.assertEqual(result["source"], "nominatim")
        self.assertAlmostEqual(result["lat"], 48.7765, places=4)
        self.assertAlmostEqual(result["lng"], 2.0020, places=4)

    @patch("backend.services.google_maps.requests.get")
    def test_returns_error_when_no_provider_finds_location(self, mock_get):
        google = Mock()
        google.status_code = 200
        google.json.return_value = {"status": "ZERO_RESULTS"}

        osm = Mock()
        osm.status_code = 200
        osm.json.return_value = []
        mock_get.side_effect = [google, osm]

        svc = GoogleMapsService()
        svc.api_key = "fake-key"
        result = svc.geocode("zzzz-no-such-place")

        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
