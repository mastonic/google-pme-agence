"""Authentification du module transport sanitaire (données de santé).

- Mots de passe : PBKDF2-SHA256 (600 000 itérations), sel aléatoire.
- Jetons : signés HMAC-SHA256 (format compact type JWT), durée limitée.
- Rôles : admin (l'agence, voit tous les clients) ; client (un ambulancier,
  ne voit que les dossiers de son entreprise).
- Anti force brute : verrouillage temporaire après plusieurs échecs.

Secret de signature : PMT_AUTH_SECRET (obligatoire en production). Sans lui,
un secret aléatoire est généré au démarrage : les sessions sautent à chaque
redémarrage.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Optional

PBKDF2_ITERATIONS = 600_000
TOKEN_TTL_SECONDS = int(os.environ.get("PMT_TOKEN_TTL_HOURS", "12")) * 3600
MIN_PASSWORD_LENGTH = 10
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60
ROLES = ("admin", "client")

_secret_cache: Optional[bytes] = None


def _secret() -> bytes:
    global _secret_cache
    env = os.environ.get("PMT_AUTH_SECRET", "")
    if env:
        return env.encode()
    if _secret_cache is None:
        print("⚠️  PMT_AUTH_SECRET absent : secret de session temporaire (sessions perdues au redémarrage).")
        _secret_cache = secrets.token_bytes(32)
    return _secret_cache


# ── Mots de passe ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, digest_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, AttributeError):
        return False


def password_problem(password: str) -> Optional[str]:
    if len(password or "") < MIN_PASSWORD_LENGTH:
        return f"Mot de passe trop court ({MIN_PASSWORD_LENGTH} caractères minimum)."
    if password.isdigit() or password.isalpha():
        return "Mélanger lettres et chiffres (ou symboles)."
    return None


# ── Jetons ────────────────────────────────────────────────────────────────────

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_token(user_id: int, token_version: int, ttl: int = TOKEN_TTL_SECONDS, now: Optional[float] = None) -> str:
    now = time.time() if now is None else now
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64(json.dumps({"sub": user_id, "ver": token_version, "iat": int(now), "exp": int(now + ttl)}).encode())
    signature = _b64(hmac.new(_secret(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def read_token(token: str, now: Optional[float] = None) -> Optional[dict]:
    """Retourne le contenu du jeton s'il est authentique et non expiré, sinon None."""
    try:
        header, payload, signature = token.split(".")
        expected = _b64(hmac.new(_secret(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        claims = json.loads(_unb64(payload))
    except (ValueError, json.JSONDecodeError):
        return None
    if claims.get("exp", 0) < (time.time() if now is None else now):
        return None
    return claims


# ── Anti force brute ──────────────────────────────────────────────────────────

class LoginThrottle:
    def __init__(self, max_attempts: int = MAX_FAILED_ATTEMPTS, lockout: int = LOCKOUT_SECONDS):
        self.max_attempts = max_attempts
        self.lockout = lockout
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def locked(self, key: str, now: Optional[float] = None) -> bool:
        now = time.time() if now is None else now
        with self._lock:
            recent = [t for t in self._failures.get(key, []) if now - t < self.lockout]
            self._failures[key] = recent
            return len(recent) >= self.max_attempts

    def fail(self, key: str, now: Optional[float] = None) -> None:
        with self._lock:
            self._failures.setdefault(key, []).append(time.time() if now is None else now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


throttle = LoginThrottle()


@dataclass
class CurrentUser:
    id: int
    email: str
    role: str
    business_id: Optional[str]

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def scope(self, requested: Optional[str]) -> Optional[str]:
        """Client : toujours son entreprise. Admin : le filtre demandé (ou tout)."""
        return requested if self.is_admin else self.business_id

    def can_access(self, business_id: Optional[str]) -> bool:
        return self.is_admin or (business_id is not None and business_id == self.business_id)
