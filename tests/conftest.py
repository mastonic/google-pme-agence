"""Configuration commune : la base de test locale reçoit les mêmes migrations que la production."""
import os

os.environ.setdefault("ADMIN_API_TOKEN", "test-token")
os.environ.setdefault("EMAIL_OUTBOX_LOOP", "false")


def pytest_sessionstart(session):
    from backend.main import run_migrations
    run_migrations()
