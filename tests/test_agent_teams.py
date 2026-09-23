import unittest
from types import SimpleNamespace

from backend.services.agent_teams import (
    BUILTIN_MANIFESTS,
    github_raw_url,
    validate_manifest,
)
from backend.services.plans import PLAN_CATALOG, apply_plan_features


class AgentTeamsTests(unittest.TestCase):
    def test_builtin_agent_teams_are_valid(self):
        slugs = []
        for manifest in BUILTIN_MANIFESTS:
            validated = validate_manifest(dict(manifest))
            slugs.append(validated["slug"])
            self.assertTrue(validated["agents"])
            self.assertTrue(all(agent["prompt"] for agent in validated["agents"]))
        self.assertEqual(set(slugs), {"domain-watch", "seo-local", "social-media"})

    def test_manifest_rejects_unknown_tool(self):
        manifest = {
            "schema_version": 1,
            "slug": "unsafe-team",
            "name": "Unsafe",
            "agents": [{
                "id": "runner",
                "prompt": "test",
                "tools": ["shell_exec"],
            }],
        }
        with self.assertRaisesRegex(ValueError, "Outils non autorisés"):
            validate_manifest(manifest)

    def test_github_import_builds_raw_manifest_url(self):
        url = github_raw_url(
            "https://github.com/acme/local-pulse-agents",
            "teams/social/team.yaml",
            "main",
        )
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/acme/local-pulse-agents/main/teams/social/team.yaml",
        )

    def test_github_import_rejects_non_github_hosts(self):
        with self.assertRaisesRegex(ValueError, "GitHub"):
            github_raw_url("https://evil.example/repo")

    def test_plan_catalog_agent_team_entitlements(self):
        self.assertEqual(PLAN_CATALOG["starter"]["agent_teams"], ["domain-watch"])
        self.assertEqual(PLAN_CATALOG["pro"]["agent_teams"], ["domain-watch", "seo-local"])
        self.assertEqual(
            PLAN_CATALOG["elite"]["agent_teams"],
            ["domain-watch", "seo-local", "social-media"],
        )

    def test_apply_plan_features_sets_entitlements(self):
        business = SimpleNamespace(
            plan_tier="free",
            mrr_value=0.0,
            features_booking_active=False,
            features_menu_active=False,
            features_click_collect_active=False,
            features_chatbot_active=False,
            features_seo_blog_active=False,
            features_gmb_reviews_sync=False,
            features_multilang_active=False,
        )
        apply_plan_features(business, "elite")
        self.assertEqual(business.plan_tier, "elite")
        self.assertEqual(business.mrr_value, 299.0)
        self.assertTrue(business.features_chatbot_active)
        self.assertTrue(business.features_seo_blog_active)
        self.assertTrue(business.features_multilang_active)


if __name__ == "__main__":
    unittest.main()
