"""Vérifie la connexion à la base et affiche le dialecte et le nombre de lignes par table.

Usage (depuis la racine du projet) :
    python -m backend.admin_db_check
"""
from sqlalchemy import func, inspect, select, text

from backend.models.database import Base, engine


def describe_database() -> list[str]:
    url = engine.url.render_as_string(hide_password=True)
    lines = [
        f"Dialecte : {engine.dialect.name} (driver : {engine.driver})",
        f"URL      : {url}",
    ]
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        lines.append("Connexion : OK")

        existing = set(inspect(conn).get_table_names())
        for table in Base.metadata.sorted_tables:
            if table.name not in existing:
                lines.append(f"{table.name:<28} absente (lancez le serveur une fois pour créer le schéma)")
                continue
            count = conn.execute(select(func.count()).select_from(table)).scalar_one()
            lines.append(f"{table.name:<28} {count} ligne(s)")
    return lines


if __name__ == "__main__":
    try:
        for line in describe_database():
            print(line)
    except Exception as exc:
        # Le message brut peut contenir des détails de connexion : on n'affiche que le type.
        print(f"Connexion : ECHEC ({type(exc).__name__})")
        raise SystemExit(1)
