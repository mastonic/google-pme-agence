import unittest

from backend.models.database import (
    engine_options,
    is_production_env,
    normalize_database_url,
    resolve_database_url,
)

SQLITE_DEFAULT = "/app/local_pulse.db"


class NormalizeDatabaseUrlTests(unittest.TestCase):
    def test_postgres_scheme_is_rewritten(self):
        self.assertEqual(
            normalize_database_url("postgres://user:pwd@host:5432/db"),
            "postgresql://user:pwd@host:5432/db",
        )

    def test_postgresql_scheme_is_kept(self):
        url = "postgresql+psycopg2://user:pwd@host/db"
        self.assertEqual(normalize_database_url(url), url)

    def test_surrounding_whitespace_is_stripped(self):
        self.assertEqual(normalize_database_url("  postgres://h/db \n"), "postgresql://h/db")


class ProductionDetectionTests(unittest.TestCase):
    def test_app_env_production(self):
        self.assertTrue(is_production_env({"APP_ENV": "production"}))
        self.assertTrue(is_production_env({"APP_ENV": "Production"}))

    def test_cloud_run_marker(self):
        self.assertTrue(is_production_env({"K_SERVICE": "localpulse-api"}))

    def test_local_dev(self):
        self.assertFalse(is_production_env({}))
        self.assertFalse(is_production_env({"APP_ENV": "development"}))


class ResolveDatabaseUrlTests(unittest.TestCase):
    def test_local_dev_defaults_to_sqlite_file(self):
        self.assertEqual(resolve_database_url({}, SQLITE_DEFAULT), f"sqlite:///{SQLITE_DEFAULT}")

    def test_explicit_url_is_used_locally(self):
        env = {"DATABASE_URL": "postgres://u:p@h/db"}
        self.assertEqual(resolve_database_url(env, SQLITE_DEFAULT), "postgresql://u:p@h/db")

    def test_blank_url_counts_as_missing(self):
        self.assertEqual(
            resolve_database_url({"DATABASE_URL": "   "}, SQLITE_DEFAULT),
            f"sqlite:///{SQLITE_DEFAULT}",
        )

    def test_production_without_url_fails_fast(self):
        with self.assertRaisesRegex(RuntimeError, "DATABASE_URL est obligatoire"):
            resolve_database_url({"APP_ENV": "production"}, SQLITE_DEFAULT)

    def test_cloud_run_without_url_fails_fast(self):
        with self.assertRaisesRegex(RuntimeError, "DATABASE_URL est obligatoire"):
            resolve_database_url({"K_SERVICE": "localpulse-api"}, SQLITE_DEFAULT)

    def test_production_rejects_sqlite_url(self):
        with self.assertRaisesRegex(RuntimeError, "SQLite n'est pas persistant"):
            resolve_database_url(
                {"APP_ENV": "production", "DATABASE_URL": "sqlite:////data/x.db"},
                SQLITE_DEFAULT,
            )

    def test_production_accepts_postgres_url(self):
        env = {"K_SERVICE": "svc", "DATABASE_URL": "postgres://u:p@/db?host=/cloudsql/x"}
        self.assertEqual(
            resolve_database_url(env, SQLITE_DEFAULT),
            "postgresql://u:p@/db?host=/cloudsql/x",
        )


class EngineOptionsTests(unittest.TestCase):
    def test_sqlite_gets_thread_flag_only(self):
        self.assertEqual(
            engine_options("sqlite:////tmp/x.db"),
            {"connect_args": {"check_same_thread": False}},
        )

    def test_postgres_gets_pre_ping_without_connect_args(self):
        options = engine_options("postgresql+psycopg2://u:p@h/db")
        self.assertEqual(options, {"pool_pre_ping": True})
        self.assertNotIn("connect_args", options)


if __name__ == "__main__":
    unittest.main()
