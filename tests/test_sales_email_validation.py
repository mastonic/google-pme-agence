import unittest

from unittest.mock import patch

from backend.agents.manager import (
    LocalPulseManager, SALES_EMAIL_SIGNATURE, display_business_name, is_sales_email_valid,
)


DEMO_URL = "https://demo-pulse.vercel.app"

GOOD_BODY = (
    "Bonjour Marie,\n\n"
    "Votre boulangerie apparaît bien dans les recherches locales, et ce sont souvent les personnes qui cherchent "
    "déjà un commerce près de chez elles qui franchissent la porte. J'ai donc préparé une démo de site personnalisée "
    "pour votre établissement, avec vos horaires et vos produits mis en avant de façon claire.\n\n"
    "Pulse Locale PME s'occupe de la mise en ligne et du suivi, vous gardez votre activité.\n\n"
    "Jetez un œil à la démo ci-dessous. Si elle vous plaît, répondez à ce mail et je vous explique la suite "
    "en 10 minutes."
)
GOOD_EMAIL = f"{GOOD_BODY}\n\n{DEMO_URL}\n\n{SALES_EMAIL_SIGNATURE}"


class _Recorder:
    def __init__(self):
        self.logs = []

    def __call__(self, agent, message, msg_type="chat"):
        self.logs.append(message)


class SalesEmailValidationTests(unittest.TestCase):
    def manager(self, business=None):
        m = LocalPulseManager.__new__(LocalPulseManager)
        m.business_data = business or {
            "name": "Boulangerie Dupont",
            "deployment_url": DEMO_URL,
            "owner_first_name": "Marie",
            "opportunity_score": 72,
            "plan_catalog": [{"slug": "pro", "name": "Pro", "price": 149, "summary": "Visibilité locale."}],
            "payment_links": {"pro": "https://pay/pro"},
        }
        m._push_log = _Recorder()
        return m

    # ── sanitizer: placeholders, markers, links, signature ──────────────────

    def test_sanitizer_removes_placeholders_markers_and_pipe_lists(self):
        raw = (
            "Bonjour [Prénom],\n"
            "--- EMAIL CONTENT START ---\n"
            "Je suis [Votre Nom] de [Votre Société].\n"
            "[ChIJabc123] | [https://x-rigahludovic-projects.vercel.app] | [Gmail Draft: Ready]\n"
            "Ouvrez [démo](https://x-rigahludovic-projects.vercel.app) ci-dessous.\n"
            "Cordialement,\n"
            "[Votre Titre]\n"
            "[Votre Email]\n"
            "--- EMAIL CONTENT END ---"
        )
        cleaned = self.manager()._sanitize_sales_email(raw)
        self.assertNotIn("[", cleaned)
        self.assertNotIn("]", cleaned)
        self.assertNotIn("EMAIL CONTENT", cleaned)
        self.assertNotIn("|", cleaned)
        self.assertNotIn("Gmail Draft", cleaned)
        self.assertNotIn("Cordialement", cleaned)
        self.assertNotIn("Votre", cleaned)
        self.assertIn("Bonjour,", cleaned)
        self.assertIn("https://x-rigahludovic-projects.vercel.app", cleaned)
        self.assertNotIn("](", cleaned)
        self.assertTrue(cleaned.endswith(SALES_EMAIL_SIGNATURE))

    def test_sanitizer_replaces_any_closing_with_required_signature(self):
        raw = "Bonjour,\n\nTexte.\n\nBien à vous,\nJean Martin\nGérant"
        cleaned = self.manager()._sanitize_sales_email(raw)
        self.assertTrue(cleaned.endswith("Texte.\n\n" + SALES_EMAIL_SIGNATURE))
        self.assertNotIn("Bien à vous", cleaned)

    def test_sanitizer_collapses_blank_lines(self):
        cleaned = self.manager()._sanitize_sales_email("Bonjour,\n\n\n\n\nTexte court.\n\n\n\n")
        self.assertNotIn("\n\n\n", cleaned)

    def test_sanitizer_strips_markdown_emphasis_and_headings(self):
        cleaned = self.manager()._sanitize_sales_email("# Bonjour,\n\nVotre **site** est prêt.")
        self.assertIn("Bonjour,", cleaned)
        self.assertIn("Votre site est prêt.", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("#", cleaned)

    def test_demo_link_replaces_long_preview_url_once(self):
        m = self.manager()
        out = m._with_demo_link(
            "Bonjour,\n\nDécouvrez https://abc-def-rigahludovic-projects.vercel.app dès maintenant.", DEMO_URL)
        self.assertEqual(out.count(DEMO_URL), 1)
        self.assertNotIn("rigahludovic-projects", out)

    # ── validator ─────────────────────────────────────────────────────────

    def test_valid_email_has_no_problems(self):
        self.assertEqual(is_sales_email_valid(GOOD_EMAIL, DEMO_URL, "Marie"), [])

    def test_missing_signature_is_reported(self):
        problems = is_sales_email_valid(GOOD_BODY + f"\n\n{DEMO_URL}", DEMO_URL, "Marie")
        self.assertIn("signature absente ou incorrecte", problems)

    def test_placeholder_is_reported(self):
        text = GOOD_EMAIL.replace("votre établissement", "[Nom de la société]")
        self.assertIn("placeholder restant", is_sales_email_valid(text, DEMO_URL, "Marie"))

    def test_artifact_is_reported(self):
        text = GOOD_EMAIL.replace("Pulse Locale PME s'occupe", "--- EMAIL CONTENT START --- Pulse Locale PME s'occupe")
        self.assertIn("artefact technique ou Markdown", is_sales_email_valid(text, DEMO_URL, "Marie"))

    def test_cordialement_is_reported(self):
        text = GOOD_BODY + f"\n\nCordialement,\n{DEMO_URL}\n\n{SALES_EMAIL_SIGNATURE}"
        self.assertIn("formule 'Cordialement' interdite", is_sales_email_valid(text, DEMO_URL, "Marie"))

    def test_missing_greeting_is_reported(self):
        text = GOOD_EMAIL.replace("Bonjour Marie,", "Madame, Monsieur")
        self.assertIn("salutation absente", is_sales_email_valid(text, DEMO_URL, "Marie"))

    def test_generic_greeting_is_reported_when_first_name_known(self):
        text = GOOD_EMAIL.replace("Bonjour Marie,", "Bonjour,")
        self.assertIn("prénom du gérant absent de la salutation", is_sales_email_valid(text, DEMO_URL, "Marie"))

    def test_length_out_of_range_is_reported(self):
        short = f"Bonjour Marie,\n\nDémo prête : {DEMO_URL}\n\n{SALES_EMAIL_SIGNATURE}"
        self.assertTrue(any(p.startswith("longueur hors plage") for p in is_sales_email_valid(short, DEMO_URL, "Marie")))
        long_text = GOOD_BODY + ("\n\n" + GOOD_BODY) * 4 + f"\n\n{DEMO_URL}\n\n{SALES_EMAIL_SIGNATURE}"
        self.assertTrue(any(p.startswith("longueur hors plage") for p in is_sales_email_valid(long_text, DEMO_URL, "Marie")))

    def test_missing_demo_url_is_reported(self):
        text = GOOD_BODY + f"\n\n{SALES_EMAIL_SIGNATURE}"
        self.assertIn("lien de démo absent", is_sales_email_valid(text, DEMO_URL, "Marie"))

    def test_price_in_body_is_reported(self):
        text = GOOD_EMAIL.replace("je vous explique", "le plan coûte 149€ / mois, je vous explique")
        self.assertIn("prix présent dans le corps", is_sales_email_valid(text, DEMO_URL, "Marie"))

    def test_truncated_body_is_reported(self):
        text = GOOD_EMAIL.replace("en 10 minutes.", "en 10 min et")
        self.assertIn("fin de texte tronquée", is_sales_email_valid(text, DEMO_URL, "Marie"))

    def test_empty_text_is_reported(self):
        self.assertEqual(is_sales_email_valid("", DEMO_URL), ["email vide"])

    # ── generation flow (no LLM call: _call is replaced) ──────────────────

    def _with_responses(self, m, responses):
        pending = list(responses)
        calls = []

        def fake_call(prompt, max_tokens=2048, system="", temperature=0.2):
            calls.append(prompt)
            return pending.pop(0)

        m._call = fake_call
        return calls

    def test_invalid_first_answer_is_regenerated_once(self):
        m = self.manager()
        calls = self._with_responses(m, ["Bonjour,\n\n[Votre Nom] Cordialement", GOOD_BODY])
        result = m._generate_sales_email("prompt un", "prompt deux")
        self.assertEqual(len(calls), 2)
        self.assertEqual(is_sales_email_valid(result, DEMO_URL, "Marie"), [])
        self.assertIn(DEMO_URL, result)

    def test_double_invalid_answer_falls_back_to_safe_template(self):
        m = self.manager()
        calls = self._with_responses(m, ["Bonjour,\n\n[Votre Nom] Cordialement", "Court. [X]"])
        result = m._generate_sales_email("prompt un", "prompt deux")
        self.assertEqual(len(calls), 2)
        self.assertEqual(is_sales_email_valid(result, DEMO_URL, "Marie"), [])
        self.assertIn("Bonjour Marie,", result)
        self.assertIn("Boulangerie Dupont", result)
        self.assertTrue(result.endswith(SALES_EMAIL_SIGNATURE))

    def test_fallback_is_valid_without_demo_url(self):
        m = self.manager()
        fallback = m._fallback_sales_email("", "")
        self.assertEqual(is_sales_email_valid(fallback, "", ""), [])

    def test_provider_error_uses_fallback_without_retry(self):
        m = self.manager()

        def boom(prompt, max_tokens=2048, system="", temperature=0.2):
            raise RuntimeError("quota")

        m._call = boom
        result = m._generate_sales_email("prompt un", "prompt deux")
        self.assertTrue(result.endswith(SALES_EMAIL_SIGNATURE))
        self.assertIn(DEMO_URL, result)

    def test_finalize_adds_checkout_once_after_valid_email(self):
        m = self.manager()
        final = m._finalize_sales_email(GOOD_EMAIL)
        self.assertEqual(final.count(DEMO_URL), 1)
        self.assertIn("https://pay/pro", final)
        self.assertTrue(final.endswith(SALES_EMAIL_SIGNATURE))
        self.assertLess(final.index(DEMO_URL), final.index("https://pay/pro"))

    # ── email de secours avant déploiement (cas réel : hôtel sans lien Vercel) ──

    HOTEL = {
        "name": "ENZO HOTELS TRAPPES By KYRIAD DIRECT",
        "business_id": "ChIJhotel123",
        "rating": 3.9,
        "user_ratings_total": 412,
        "deployment_url": "",
    }

    def hotel_manager(self):
        m = self.manager(dict(self.HOTEL))
        m.sector = "lodging"
        return m

    def test_display_name_tames_all_caps(self):
        self.assertEqual(display_business_name("ENZO HOTELS TRAPPES By KYRIAD DIRECT"),
                         "Enzo Hotels Trappes by Kyriad Direct")
        self.assertEqual(display_business_name("HÔTEL DE LA GARE"), "Hôtel de la Gare")
        self.assertEqual(display_business_name("BOULANGERIE SAINT-JEAN"), "Boulangerie Saint-Jean")
        self.assertEqual(display_business_name("L'ATELIER D'ANNA"), "L'Atelier d'Anna")
        self.assertEqual(display_business_name("Chez Marcel"), "Chez Marcel")  # déjà soigné : inchangé

    def test_demo_link_before_deployment_is_public_demo_page(self):
        with patch.dict("os.environ", {"PUBLIC_BASE_URL": "https://cockpit.example"}):
            self.assertEqual(self.hotel_manager()._demo_link(), "https://cockpit.example/demo/ChIJhotel123")
        m = self.manager()
        self.assertEqual(m._demo_link(), DEMO_URL)  # déployé : lien Vercel

    def test_hotel_fallback_has_link_facts_and_sector_benefit(self):
        m = self.hotel_manager()
        with patch.dict("os.environ", {"PUBLIC_BASE_URL": "https://cockpit.example"}):
            demo = m._demo_link()
            email = m._fallback_sales_email(demo, "")
        self.assertEqual(is_sales_email_valid(email, demo, ""), [])
        self.assertIn("https://cockpit.example/demo/ChIJhotel123", email)
        self.assertIn("Enzo Hotels Trappes by Kyriad Direct", email)
        self.assertNotIn("ENZO HOTELS", email)
        self.assertIn("3,9/5 sur 412 avis", email)
        self.assertIn("réserver directement", email)
        self.assertNotIn("vous apprécient", email)  # 3,9/5 : pas de compliment automatique
        self.assertNotIn("visio", email)          # un seul appel à l'action
        self.assertNotIn("la présenter", email)   # ancienne faute d'accord

    def test_fallback_without_reviews_invents_nothing(self):
        m = self.manager({"name": "GARAGE MARTIN", "business_id": "g1"})
        m.sector = "automotive"
        email = m._fallback_sales_email(m._demo_link(), "")
        self.assertNotIn("/5", email)
        self.assertIn("Garage Martin", email)
        self.assertEqual(is_sales_email_valid(email, m._demo_link(), ""), [])


if __name__ == "__main__":
    unittest.main()
