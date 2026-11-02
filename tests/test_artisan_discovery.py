import unittest
from unittest.mock import Mock, patch

from backend.services.artisan_discovery import (
    ARTISAN_TRADES,
    MAX_PAGES,
    MAX_SPLIT_DEPTH,
    Rect,
    build_text_search_body,
    discover_rect,
    discover_trades,
    grid,
    make_places_transport,
)


def _page(ids, token=None):
    return {"places": [{"id": i} for i in ids], **({"nextPageToken": token} if token else {})}


class GridTests(unittest.TestCase):
    def test_grid_covers_the_whole_zone(self):
        cells = grid(14.40, -61.20, 14.50, -61.10, cell_km=2.0)
        self.assertGreater(len(cells), 1)
        self.assertAlmostEqual(min(c.south for c in cells), 14.40)
        self.assertAlmostEqual(max(c.north for c in cells), 14.50)
        self.assertAlmostEqual(min(c.west for c in cells), -61.20)
        self.assertAlmostEqual(max(c.east for c in cells), -61.10)

    def test_invalid_zone_is_rejected(self):
        with self.assertRaises(ValueError):
            grid(14.5, -61.2, 14.4, -61.1)
        with self.assertRaises(ValueError):
            grid(14.4, -61.2, 14.5, -61.1, cell_km=0)

    def test_split_produces_four_quarters_covering_parent(self):
        parent = Rect(0.0, 0.0, 2.0, 4.0)
        quarters = parent.split()
        self.assertEqual(len(quarters), 4)
        self.assertEqual(min(q.south for q in quarters), 0.0)
        self.assertEqual(max(q.north for q in quarters), 2.0)
        self.assertEqual(min(q.west for q in quarters), 0.0)
        self.assertEqual(max(q.east for q in quarters), 4.0)


class BodyTests(unittest.TestCase):
    def test_included_type_only_when_given_and_never_strict(self):
        rect = Rect(0, 0, 1, 1)
        body = build_text_search_body("plombier", rect, included_type="plumber")
        self.assertEqual(body["includedType"], "plumber")
        self.assertNotIn("strictTypeFiltering", body)
        self.assertNotIn("includedType", build_text_search_body("plombier", rect))

    def test_page_token_only_on_next_pages(self):
        rect = Rect(0, 0, 1, 1)
        self.assertNotIn("pageToken", build_text_search_body("plombier", rect))
        self.assertEqual(build_text_search_body("plombier", rect, page_token="abc")["pageToken"], "abc")


class PaginationTests(unittest.TestCase):
    def test_pages_are_followed_until_token_disappears(self):
        pages = [_page(["a", "b"], "t1"), _page(["c"], "t2"), _page(["d"])]
        calls = []

        def transport(body):
            calls.append(body.get("pageToken"))
            return pages[len(calls) - 1]

        places, incomplete = discover_rect(transport, "plombier", Rect(0, 0, 1, 1))
        self.assertEqual([p["id"] for p in places], ["a", "b", "c", "d"])
        self.assertEqual(incomplete, 0)
        self.assertEqual(calls, [None, "t1", "t2"])

    def test_saturated_cell_is_split_and_quarters_are_used(self):
        # Seule la cellule d'origine renvoie toujours un jeton (saturation) ; ses
        # quatre quarts se terminent. Les résultats de la cellule saturée sont
        # remplacés par ceux des quarts (sinon on compterait deux fois).
        big = Rect(0, 0, 2, 2)

        def transport(body):
            rect = body["locationRestriction"]["rectangle"]
            corners = (rect["low"]["latitude"], rect["low"]["longitude"],
                       rect["high"]["latitude"], rect["high"]["longitude"])
            if corners == (0, 0, 2, 2):  # cellule d'origine : toujours saturée
                return _page(["x"], "more")
            if corners == (0, 0, 1, 1):  # quart sud-ouest
                return _page(["shared", "q1"])
            return _page(["shared"])

        places, incomplete = discover_rect(transport, "plombier", big)
        ids = [p["id"] for p in places]
        self.assertEqual(incomplete, 0)
        self.assertNotIn("x", ids)
        self.assertIn("q1", ids)
        self.assertEqual(ids.count("shared"), 4)  # une fois par quart (brut, avant dédoublonnage)

    def test_recursion_stops_at_max_depth_and_reports_incomplete(self):
        calls = {"n": 0}

        def always_saturated(body):
            calls["n"] += 1
            return _page(["p"], "forever")

        _, incomplete = discover_rect(always_saturated, "plombier", Rect(0, 0, 1, 1))
        self.assertEqual(incomplete, 4 ** MAX_SPLIT_DEPTH)
        # Chaque nœud (1 + 4 + 16 + … jusqu'à la profondeur max) consomme MAX_PAGES appels.
        nodes = sum(4 ** d for d in range(MAX_SPLIT_DEPTH + 1))
        self.assertEqual(calls["n"], nodes * MAX_PAGES)


class TransportTests(unittest.TestCase):
    @patch("requests.post")
    def test_transport_sends_field_mask_and_key_and_returns_json(self, mock_post):
        mock_post.return_value = Mock(status_code=200, json=Mock(return_value=_page(["a"])))
        transport = make_places_transport("KEY", timeout=5)

        data = transport(build_text_search_body("plombier", Rect(0, 0, 1, 1)))

        self.assertEqual(data["places"][0]["id"], "a")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["X-Goog-Api-Key"], "KEY")
        self.assertIn("nextPageToken", kwargs["headers"]["X-Goog-FieldMask"])
        self.assertNotIn("websiteUri", kwargs["headers"]["X-Goog-FieldMask"])

    @patch("requests.post")
    def test_transport_raises_on_http_error(self, mock_post):
        mock_post.return_value = Mock(status_code=403, json=Mock(return_value={"error": {"message": "API not enabled"}}))
        transport = make_places_transport("KEY")
        with self.assertRaises(RuntimeError) as ctx:
            transport(build_text_search_body("plombier", Rect(0, 0, 1, 1)))
        self.assertIn("API not enabled", str(ctx.exception))


class TradesTests(unittest.TestCase):
    def test_discover_trades_tags_each_place_with_matching_trades(self):
        trades = [
            {"slug": "plomberie", "queries": ["plombier"], "included_type": None},
            {"slug": "electricite", "queries": ["électricien"], "included_type": None},
        ]

        def transport(body):
            if body["textQuery"] == "plombier":
                return _page(["p1", "both"])
            return _page(["e1", "both"])

        result = discover_trades(transport, [Rect(0, 0, 1, 1)], trades)
        self.assertEqual(result["queries"], 2)
        self.assertEqual(result["incomplete_cells"], 0)
        self.assertEqual(result["places"]["both"]["trades"], ["plomberie", "electricite"])
        self.assertEqual(result["places"]["p1"]["trades"], ["plomberie"])
        self.assertEqual(len(result["places"]), 3)

    def test_places_without_id_are_ignored(self):
        def transport(body):
            return {"places": [{"displayName": {"text": "Sans id"}}, {"id": "ok"}]}

        result = discover_trades(transport, [Rect(0, 0, 1, 1)], [{"slug": "t", "queries": ["q"], "included_type": None}])
        self.assertEqual(list(result["places"]), ["ok"])

    def test_catalogue_is_well_formed(self):
        slugs = [t["slug"] for t in ARTISAN_TRADES]
        self.assertEqual(len(slugs), len(set(slugs)), "slugs de métiers dupliqués")
        for trade in ARTISAN_TRADES:
            self.assertTrue(trade["queries"], f"{trade['slug']} sans requête")
            self.assertTrue(all(q.strip() for q in trade["queries"]))
            self.assertTrue(trade["included_type"] is None or trade["included_type"].strip())


if __name__ == "__main__":
    unittest.main()
