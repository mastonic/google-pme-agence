import unittest

from backend.services.site_design_system import (
    build_design_prompt_directive,
    detect_archetype,
    resolve_site_design,
)


class SiteDesignSystemTests(unittest.TestCase):
    def test_fine_categories_are_split(self):
        self.assertEqual(detect_archetype(["bakery"], "Maison Dupont"), "bakery")
        self.assertEqual(detect_archetype(["cafe"], "Café Soleil"), "cafe")
        self.assertEqual(detect_archetype(["bar"], "Le Lounge"), "bar")
        self.assertEqual(detect_archetype(["dentist"], "Cabinet X"), "dentist")
        self.assertEqual(detect_archetype(["spa"], "Zen"), "spa")
        self.assertEqual(detect_archetype(["hair_care"], "Studio Hair"), "hair")

    def test_name_can_refine_broad_google_type(self):
        self.assertEqual(detect_archetype(["beauty_salon"], "Barber King"), "hair")
        self.assertEqual(detect_archetype(["store"], "Fleurs des Îles"), "florist")
        self.assertEqual(detect_archetype(["store"], "Immo Caraïbes"), "real_estate")

    def test_business_variant_is_deterministic(self):
        one = resolve_site_design(["restaurant"], "Chez Léa", "same-id")
        two = resolve_site_design(["restaurant"], "Chez Léa", "same-id")
        self.assertEqual(one["layout_variant"], two["layout_variant"])
        self.assertEqual(one["hero_variant"], two["hero_variant"])
        self.assertEqual(one["motion_variant"], two["motion_variant"])

    def test_prompt_explicitly_rejects_generic_hero(self):
        d = resolve_site_design(["restaurant"], "Chez Léa", "x")
        directive = build_design_prompt_directive(d)
        self.assertIn("Do NOT default to a full-screen", directive)
        self.assertIn("Human/emotional angle", directive)
        self.assertIn("Signature components", directive)


if __name__ == "__main__":
    unittest.main()
