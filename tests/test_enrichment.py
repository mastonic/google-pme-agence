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


class INPITests(unittest.TestCase):
    RNE = {"siren": "912345678", "formality": {"content": {
        "personnePhysique": {"identite": {
            "entreprise": {"siren": "912345678", "codeApe": "5610C", "dateImmat": "2022-03-01"},
            "entrepreneur": {"descriptionPersonne": {"nom": "BOULE", "prenoms": ["MARIE", "ANNE"]}}},
            "etablissementPrincipal": {"descriptionEtablissement": {"nomCommercial": "FRUITY BOULE"},
                                       "adresse": {"codePostal": "97200"}}}}}}

    def test_parse_rne_individual(self):
        from backend.services.enrichment import INPIService
        out = INPIService.parse_rne(self.RNE)
        self.assertEqual(out["siren"], "912345678")
        self.assertEqual(out["trade_name"], "FRUITY BOULE")
        self.assertEqual((out["owner_first_name"], out["owner_last_name"]), ("Marie", "Boule"))
        self.assertEqual(out["postcode"], "97200")

    @patch("backend.services.enrichment.requests.get")
    def test_public_fallback_requires_name_match(self, get):
        from backend.services.enrichment import INPIService
        class R:
            status_code = 200
            def json(self_inner):
                return {"results": [
                    {"siren": "1", "nom_complet": "AUTRE SOCIETE", "siege": {}},
                    {"siren": "912345678", "nom_complet": "MARIE BOULE", "date_creation": "2022-03-01",
                     "siege": {"liste_enseignes": ["FRUITY BOULE"], "code_postal": "97200"},
                     "dirigeants": [{"type_dirigeant": "personne physique", "nom": "BOULE", "prenoms": "MARIE ANNE"}]}]}
        get.return_value = R()
        with patch.dict("os.environ", {"INPI_USERNAME": "", "INPI_PASSWORD": ""}):
            out = INPIService().find_company("Fruity Boule", "12 rue X, 97200 Fort-de-France")
        self.assertEqual(out["siren"], "912345678")
        self.assertEqual(out["owner_first_name"], "Marie")
        self.assertEqual(out["registry_source"], "recherche_entreprises")
        self.assertEqual(get.call_args.kwargs["params"]["code_postal"], "97200")
