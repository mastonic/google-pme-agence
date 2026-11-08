"""Configuration commune : la base de test locale reçoit les mêmes migrations que la production."""
import importlib.util
import os

os.environ.setdefault("ADMIN_API_TOKEN", "test-token")
os.environ.setdefault("EMAIL_OUTBOX_LOOP", "false")


def pytest_sessionstart(session):
    # Certains contrôles légers (ex. tests/test_seo_domains.py en CI « validate ») tournent sans
    # les dépendances du backend : on n'applique les migrations que si FastAPI est installé.
    if importlib.util.find_spec("fastapi") is None:
        return
    from backend.main import run_migrations
    run_migrations()
