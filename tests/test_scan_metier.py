import unittest

from backend.services.artisan_discovery import ARTISAN_TRADES, trades_for_metier


class TradesForMetierTests(unittest.TestCase):
    def test_empty_gives_nothing(self):
        self.assertEqual(trades_for_metier(""), [])
        self.assertEqual(trades_for_metier(None), [])

    def test_known_trade_keeps_its_queries(self):
        trades = trades_for_metier("Plombier")
        self.assertEqual([t["slug"] for t in trades], ["plomberie"])

    def test_unknown_metier_becomes_its_own_query_not_all_trades(self):
        trades = trades_for_metier("Boulangerie")
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["queries"], ["Boulangerie"])
        self.assertLess(len(trades), len(ARTISAN_TRADES))


if __name__ == "__main__":
    unittest.main()
