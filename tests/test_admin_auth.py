import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.routing import APIRoute, APIWebSocketRoute
from starlette.requests import Request

from backend.services.auth import PUBLIC_ROUTES, require_admin

TOKEN = "test-admin-token-123"


def make_request(route_path, headers=None, path=None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": path or route_path,
        "query_string": b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "route": type("Route", (), {"path": route_path})(),
    }
    return Request(scope)


class AdminAuthTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict(os.environ, {"ADMIN_API_TOKEN": TOKEN})
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_rejected(self, status_code, request):
        with self.assertRaises(HTTPException) as ctx:
            require_admin(request)
        self.assertEqual(ctx.exception.status_code, status_code)

    def test_missing_token_is_rejected(self):
        self.assert_rejected(401, make_request("/businesses/{business_id}"))

    def test_wrong_bearer_token_is_rejected(self):
        request = make_request("/businesses/{business_id}", {"Authorization": "Bearer nope"})
        self.assert_rejected(401, request)

    def test_wrong_x_admin_token_is_rejected(self):
        request = make_request("/scan", {"X-Admin-Token": "nope"})
        self.assert_rejected(401, request)

    def test_right_bearer_token_is_accepted(self):
        request = make_request("/businesses/{business_id}", {"Authorization": f"Bearer {TOKEN}"})
        self.assertIsNone(require_admin(request))

    def test_right_x_admin_token_is_accepted(self):
        request = make_request("/deploy/{business_id}", {"X-Admin-Token": TOKEN})
        self.assertIsNone(require_admin(request))

    def test_fails_closed_when_server_token_is_not_configured(self):
        with patch.dict(os.environ, {"ADMIN_API_TOKEN": ""}):
            request = make_request("/businesses", {"Authorization": f"Bearer {TOKEN}"})
            self.assert_rejected(503, request)

    def test_public_routes_need_no_token(self):
        for route_path in ("/preview/{business_id}", "/client/onboarding/{token}", "/webhook/stripe", "/status"):
            with self.subTest(route=route_path):
                self.assertIsNone(require_admin(make_request(route_path)))

    def test_public_route_stays_public_even_with_server_token_unset(self):
        with patch.dict(os.environ, {"ADMIN_API_TOKEN": ""}):
            self.assertIsNone(require_admin(make_request("/demo/{business_id}")))

    def test_unlisted_route_is_protected_by_default(self):
        self.assert_rejected(401, make_request("/some-new-route"))

    def test_every_app_route_is_protected_unless_listed_as_public(self):
        from backend.main import app

        api_routes = [r for r in app.routes if isinstance(r, APIRoute)]
        ws_routes = [r for r in app.routes if isinstance(r, APIWebSocketRoute)]
        route_paths = {r.path for r in api_routes + ws_routes}
        for public_path in PUBLIC_ROUTES:
            with self.subTest(public_path=public_path):
                self.assertIn(public_path, route_paths)

        for route in ws_routes:
            with self.subTest(websocket=route.path):
                self.assertTrue(any(d.call is require_admin for d in route.dependant.dependencies))

        for route in api_routes:
            guarded = any(d.dependency is require_admin for d in route.dependencies)
            with self.subTest(route=route.path, methods=sorted(route.methods)):
                self.assertTrue(guarded)


if __name__ == "__main__":
    unittest.main()
