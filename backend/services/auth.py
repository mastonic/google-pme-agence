"""Authentification du cockpit par jeton administrateur.

Toutes les routes de l'API exigent `ADMIN_API_TOKEN`, envoyé soit en
`Authorization: Bearer <token>`, soit en `X-Admin-Token: <token>`.
Seules les routes listées dans PUBLIC_ROUTES restent ouvertes (prospects,
clients avec leur lien tokenisé, Stripe, santé). Une route absente de cette
liste est donc protégée par défaut.

Si la variable est absente, les routes protégées répondent 503 (fail closed).
"""
import logging
import os
import secrets

from fastapi import HTTPException, Request

logger = logging.getLogger("localpulse.auth")

ADMIN_TOKEN_ENV = "ADMIN_API_TOKEN"

# Gabarits de routes FastAPI accessibles sans jeton.
PUBLIC_ROUTES = frozenset({
    "/",
    "/status",
    "/pricing-page",
    "/preview/{business_id}",
    "/sites/{business_id}/config",
    "/demo/{business_id}",
    "/buy/{business_id}/{plan}",
    "/photo",
    "/client/onboarding/{token}",
    "/webhook/stripe",
    # Espace client PulsePro : protégé par sa propre session (en-tête X-Client-Session).
    "/client/auth/request",
    "/client/auth/exchange",
    "/client/auth/logout",
    "/client/space",
    "/client/space/info",
    "/client/space/media",
    "/client/space/media/{media_id}",
    "/client/media/{media_id}",
    "/client/space/checkout",
    "/client/space/portal",
    "/client/space/requests",
    "/client/track/{business_id}",
})


def _extract_token(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() == "bearer" and value.strip():
        return value.strip()
    return request.headers.get("x-admin-token", "").strip()


def require_admin(request: Request) -> None:
    """Dépendance globale de l'application : rejette les requêtes sans jeton valide."""
    route = request.scope.get("route")
    if route is not None and route.path in PUBLIC_ROUTES:
        return

    expected = os.getenv(ADMIN_TOKEN_ENV, "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Accès administrateur non configuré (ADMIN_API_TOKEN absent).",
        )

    provided = _extract_token(request)
    if not provided or not secrets.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(
            status_code=401,
            detail="Jeton administrateur invalide ou manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def warn_if_admin_token_missing() -> None:
    if not os.getenv(ADMIN_TOKEN_ENV, "").strip():
        logger.warning(
            "ADMIN_API_TOKEN absent : les routes protégées (cockpit, scans, déploiements, IA) "
            "répondent 503 tant que la variable n'est pas configurée."
        )
