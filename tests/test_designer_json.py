import json
import unittest

from backend.agents.manager import LocalPulseManager


class DesignerJsonTests(unittest.TestCase):
    def manager(self):
        m = LocalPulseManager.__new__(LocalPulseManager)
        return m

    def test_parse_design_json_accepts_valid_object_with_noise(self):
        raw = """Voici le brief :
        {
          "template": "editorial-food",
          "sector": "restaurant",
          "colors": {"primary": "#111111"},
          "fonts": {"heading": "Playfair Display", "body": "Inter"},
          "mood": "chaleureux, premium",
          "sections_order": ["hero", "menu", "contact"]
        }
        fin"""
        parsed = self.manager()._parse_design_json(raw)
        self.assertEqual(parsed["template"], "editorial-food")
        self.assertEqual(parsed["sections_order"][1], "menu")

    def test_parse_design_json_rejects_missing_required_key(self):
        raw = json.dumps({
            "template": "x",
            "colors": {},
            "fonts": {},
            "mood": "x",
        })
        with self.assertRaises(Exception):
            self.manager()._parse_design_json(raw)

    def test_parse_design_json_removes_trailing_commas(self):
        raw = """{
          "template":"x",
          "colors":{"primary":"#000",},
          "fonts":{"heading":"Inter","body":"Inter",},
          "mood":"clean",
          "sections_order":["hero","contact",],
        }"""
        parsed = self.manager()._parse_design_json(raw)
        self.assertEqual(parsed["template"], "x")


if __name__ == "__main__":
    unittest.main()
