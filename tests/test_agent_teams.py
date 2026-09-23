from types import SimpleNamespace

import pytest

from backend.services.agent_teams import (
    BUILTIN_MANIFESTS,
    github_raw_url,
    validate_manifest,
)
from backend.services.plans import PLAN_CATALOG, apply_plan_features


def test_builtin_agent_teams_are_valid():
    slugs = []
    for manifest in BUILTIN_MANIFESTS:
        validated = validate_manifest(dict(manifest))
        slugs.append(validated["slug"])
        assert validated["agents"]
        assert all(agent["prompt"] for agent in validated["agents"])
    assert set(slugs) == {"domain-watch", "seo-local", "social-media"}


def test_manifest_rejects_unknown_tool():
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
    with pytest.raises(ValueError, match="Outils non autorisés"):
        validate_manifest(manifest)


def test_github_import_builds_raw_manifest_url():
    url = github_raw_url(
        "https://github.com/acme/local-pulse-agents",
        "teams/social/team.yaml",
        "main",
    )
    assert url == (
        "https://raw.githubusercontent.com/acme/local-pulse-agents/"
        "main/teams/social/team.yaml"
    )


def test_github_import_rejects_non_github_hosts():
    with pytest.raises(ValueError, match="GitHub"):
        github_raw_url("https://evil.example/repo")


def test_plan_catalog_agent_team_entitlements():
    assert PLAN_CATALOG["starter"]["agent_teams"] == ["domain-watch"]
    assert PLAN_CATALOG["pro"]["agent_teams"] == ["domain-watch", "seo-local"]
    assert PLAN_CATALOG["elite"]["agent_teams"] == ["domain-watch", "seo-local", "social-media"]


def test_apply_plan_features_sets_entitlements():
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
    assert business.plan_tier == "elite"
    assert business.mrr_value == 299.0
    assert business.features_chatbot_active is True
    assert business.features_seo_blog_active is True
    assert business.features_multilang_active is True
