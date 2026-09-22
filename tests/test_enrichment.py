import unittest
from unittest.mock import patch

from backend.services.enrichment import (
    WebsiteContactFinder,
    _safe_website_url,
    _valid_public_email,
)


class _Resp:
    def __init__(self, text, url="https://example.fr/", status=200, content_type="text/html"):
        self.text = text
        self.url = url
        self.status_code = status
        self.headers = {"content-type": content_type}


class EnrichmentTests(unittest.TestCase):
    def test_rejects_private_or_invalid_website_urls(self):
        self.assertEqual(_safe_website_url("http://127.0.0.1/test"), "")
        self.assertEqual(_safe_website_url("ftp://example.fr"), "")
        self.assertEqual(_safe_website_url("example.fr"), "https://example.fr")

    def test_email_validation_filters_placeholders(self):
        self.assertTrue(_valid_public_email("contact@entreprise.fr"))
        self.assertFalse(_valid_public_email("noreply@entreprise.fr"))
        self.assertFalse(_valid_public_email("demo@example.com"))

    @patch("backend.services.enrichment.requests.get")
    def test_finder_prefers_published_mailto_and_discovers_contact_page(self, get):
        get.side_effect = [
            _Resp('<a href="/contact">Nous contacter</a>', "https://example.fr/"),
            _Resp('<a href="mailto:bonjour@example.fr">Email</a>', "https://example.fr/contact"),
            _Resp("", "https://example.fr/nous-contacter", 404),
            _Resp("", "https://example.fr/mentions-legales", 404),
            _Resp("", "https://example.fr/a-propos", 404),
        ]
        result = WebsiteContactFinder().find("https://example.fr")
        self.assertIn("bonjour@example.fr", result["emails"])
        self.assertEqual(
            result["email_sources"]["bonjour@example.fr"]["source"],
            "website_mailto",
        )
        self.assertEqual(
            result["email_sources"]["bonjour@example.fr"]["confidence"],
            95,
        )


if __name__ == "__main__":
    unittest.main()
