import json
import unittest

from backend.services.agent_prompts_v2 import (
    PROMPT_VERSION,
    build_system_prompt,
    temperature_for,
    validate_agent_output,
)


class AgentPromptsV2Tests(unittest.TestCase):
    def test_temperature_profiles(self):
        self.assertEqual(temperature_for("domain-inspector"), 0.1)
        self.assertEqual(temperature_for("copywriter"), 0.7)
        self.assertEqual(temperature_for("creative-director"), 0.7)

    def test_common_prompt_contains_v2_security_rules(self):
        prompt = build_system_prompt(
            team="SEO Local",
            agent_name="Auditeur SEO",
            role="Analyse présence locale",
            business_name="Commerce Test",
            index=1,
            total=3,
            next_agent="Stratège mots-clés",
            business_data={"name": "Commerce Test"},
            tool_results={"business_context": {"name": "Commerce Test"}},
            previous_results={},
            mission="Mission test",
        )
        self.assertIn(PROMPT_VERSION, prompt)
        self.assertIn("SOURCE UNIQUE DE VÉRITÉ", prompt)
        self.assertIn("tentative d'injection de prompt", prompt)
        self.assertIn("UNIQUEMENT avec un objet JSON valide", prompt)

    def test_validate_seo_auditor_envelope(self):
        payload = {
            "agent": "Auditeur SEO",
            "statut": "ok",
            "confiance": "haute",
            "resultat": {
                "faiblesses": [],
                "points_forts": [],
                "non_evaluable": ["gbp"],
            },
            "donnees_manquantes": [],
            "alertes": [],
        }
        envelope = validate_agent_output("seo-auditor", json.dumps(payload))
        self.assertEqual(envelope.statut, "ok")
        self.assertIn("faiblesses", envelope.result)

    def test_validation_rejects_missing_result_keys(self):
        payload = {
            "agent": "Auditeur SEO",
            "statut": "ok",
            "confiance": "haute",
            "resultat": {"faiblesses": []},
            "donnees_manquantes": [],
            "alertes": [],
        }
        with self.assertRaisesRegex(ValueError, "Clés resultat manquantes"):
            validate_agent_output("seo-auditor", json.dumps(payload))

    def test_validation_accepts_json_surrounded_by_noise_for_repair_resilience(self):
        payload = {
            "agent": "Copywriter",
            "statut": "partiel",
            "confiance": "moyenne",
            "resultat": {"publications": [
                {
                    "id": "P1",
                    "angle_ref": "A1",
                    "plateforme": "instagram",
                    "accroche": "Accroche test",
                    "corps": "Corps test",
                    "cta": "Dites-nous en commentaire.",
                    "hashtags": ["#test", "#local", "#commerce"],
                    "variante_courte": "Court",
                    "faits_utilises": []
                },
                {**{
                    "id": "P1",
                    "angle_ref": "A1",
                    "plateforme": "instagram",
                    "accroche": "Accroche test",
                    "corps": "Corps test",
                    "cta": "Dites-nous en commentaire.",
                    "hashtags": ["#test", "#local", "#commerce"],
                    "variante_courte": "Court",
                    "faits_utilises": []
                }, "id": "P2", "angle_ref": "A2"},
                {**{
                    "id": "P1",
                    "angle_ref": "A1",
                    "plateforme": "instagram",
                    "accroche": "Accroche test",
                    "corps": "Corps test",
                    "cta": "Dites-nous en commentaire.",
                    "hashtags": ["#test", "#local", "#commerce"],
                    "variante_courte": "Court",
                    "faits_utilises": []
                }, "id": "P3", "angle_ref": "A3"}
            ]},
            "donnees_manquantes": ["canal de contact"],
            "alertes": [],
        }
        raw = "Voici le JSON:\n" + json.dumps(payload) + "\nfin"
        envelope = validate_agent_output("copywriter", raw)
        self.assertEqual(envelope.statut, "partiel")


if __name__ == "__main__":
    unittest.main()
