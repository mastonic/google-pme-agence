"""
Service d'enrichissement CRM des contacts.

Combine deux sources pour retrouver, à partir d'un commerce scanné sur Google Maps :
  - Pappers (registre des entreprises FR) -> nom/prénom + qualité du gérant, SIREN, téléphone/email légaux.
  - Perplexity (recherche web en ligne) -> email de contact, téléphone, nom du dirigeant en complément.

Le service est tolérant aux pannes : si une clé d'API manque ou qu'un appel échoue,
il renvoie simplement les champs trouvés (éventuellement vides) sans lever d'exception,
pour ne jamais casser la démo.
"""
import os
import re
import json
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()  # garantit la lecture de PAPPERS_API_KEY / PERPLEXITY_API_KEY
except Exception:
    pass


def _clean_city(address: str) -> str:
    """Extrait grossièrement la ville depuis une adresse formatée."""
    if not address:
        return ""
    parts = [p.strip() for p in address.split(",")]
    candidate = parts[-2] if len(parts) >= 2 else parts[-1]
    # Retire les codes postaux et le pays
    candidate = re.sub(r"\d{4,6}", "", candidate)
    candidate = candidate.replace("France", "").strip(" ,")
    return candidate


class PappersService:
    """Registre des entreprises françaises -> dirigeants (nom, prénom, qualité)."""

    BASE_URL = "https://api.pappers.fr/v2"

    def __init__(self):
        self.token = os.getenv("PAPPERS_API_KEY")

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    def find_company(self, name: str, city: str = "") -> dict:
        if not self.enabled:
            return {}
        try:
            query = f"{name} {city}".strip()
            resp = requests.get(
                f"{self.BASE_URL}/recherche",
                params={
                    "api_token": self.token,
                    "q": query,
                    "par_page": 1,
                    "precision": "approximate",
                },
                timeout=15,
            )
            if resp.status_code != 200:
                print(f"Pappers API error {resp.status_code}: {resp.text[:200]}")
                return {}
            results = resp.json().get("resultats", [])
            if not results:
                return {}
            top = results[0]
            data = {"siren": top.get("siren")}

            # Les dirigeants peuvent être directement dans le résultat de recherche...
            dirigeants = top.get("dirigeants") or top.get("representants") or []
            # ... sinon on va chercher la fiche détaillée.
            if not dirigeants and data["siren"]:
                detail = self._company_detail(data["siren"])
                dirigeants = detail.get("representants") or detail.get("dirigeants") or []
                data["phone"] = detail.get("telephone")
                data["email"] = detail.get("email")

            leader = self._pick_leader(dirigeants)
            if leader:
                data["owner_first_name"] = leader.get("prenom") or leader.get("prenom_usuel")
                data["owner_last_name"] = leader.get("nom")
                data["owner_role"] = leader.get("qualite")
            return {k: v for k, v in data.items() if v}
        except Exception as e:
            print(f"Pappers enrichment failed: {e}")
            return {}

    def _company_detail(self, siren: str) -> dict:
        try:
            resp = requests.get(
                f"{self.BASE_URL}/entreprise",
                params={"api_token": self.token, "siren": siren},
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"Pappers detail failed: {e}")
        return {}

    @staticmethod
    def _pick_leader(dirigeants: list) -> dict:
        """Choisit le dirigeant le plus pertinent (Gérant/Président/personne physique)."""
        if not dirigeants:
            return {}
        priority = ("gérant", "gerant", "président", "president", "directeur")
        for d in dirigeants:
            qualite = (d.get("qualite") or "").lower()
            if any(p in qualite for p in priority) and d.get("nom"):
                return d
        # Fallback : première personne physique avec un nom
        for d in dirigeants:
            if d.get("nom"):
                return d
        return {}


class PerplexityService:
    """Recherche web en ligne -> email / téléphone / dirigeant."""

    URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self):
        self.key = os.getenv("PERPLEXITY_API_KEY")
        self.model = os.getenv("PERPLEXITY_MODEL", "sonar")

    @property
    def enabled(self) -> bool:
        return bool(self.key)

    def find_contacts(self, name: str, address: str) -> dict:
        if not self.enabled:
            return {}
        prompt = (
            f"Trouve les informations de contact professionnelles du commerce suivant "
            f"en France : « {name} », adresse : {address}. "
            "Cherche son email de contact, son numéro de téléphone, et le nom et prénom "
            "du gérant ou propriétaire. "
            "Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format : "
            '{"email": "", "phone": "", "owner_first_name": "", "owner_last_name": ""}. '
            "Laisse une chaîne vide pour toute information introuvable. N'invente jamais de données."
        )
        try:
            resp = requests.post(
                self.URL,
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Tu es un assistant de recherche de contacts B2B. Tu ne renvoies que du JSON valide."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                },
                timeout=40,
            )
            if resp.status_code != 200:
                print(f"Perplexity API error {resp.status_code}: {resp.text[:200]}")
                return {}
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = self._extract_json(content)
            # Normalise les clés et retire les valeurs vides
            mapping = {
                "email": "contact_email",
                "phone": "phone",
                "owner_first_name": "owner_first_name",
                "owner_last_name": "owner_last_name",
            }
            out = {}
            for src, dst in mapping.items():
                val = parsed.get(src)
                if isinstance(val, str) and val.strip():
                    out[dst] = val.strip()
            return out
        except Exception as e:
            print(f"Perplexity enrichment failed: {e}")
            return {}

    @staticmethod
    def _extract_json(text: str) -> dict:
        if not text:
            return {}
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return {}
        return {}


def enrich_business(name: str, address: str) -> dict:
    """
    Orchestration : Pappers (officiel) puis Perplexity (web) en complément.
    Pappers est prioritaire pour l'identité du gérant ; Perplexity comble
    les emails/téléphones manquants.
    """
    city = _clean_city(address)
    result = {}
    sources = {}

    pappers = PappersService()
    if pappers.enabled:
        pappers_data = pappers.find_company(name, city)
        if pappers_data:
            sources["pappers"] = sorted(pappers_data.keys())
        # Pappers renvoie parfois email/phone sous d'autres clés
        if pappers_data.get("email"):
            result["contact_email"] = pappers_data.pop("email")
        if pappers_data.get("phone"):
            result["phone"] = pappers_data.pop("phone")
        result.update(pappers_data)

    perplexity = PerplexityService()
    if perplexity.enabled:
        web_data = perplexity.find_contacts(name, address)
        if web_data:
            sources["perplexity"] = sorted(web_data.keys())
        # Ne pas écraser ce que Pappers a déjà fourni (source officielle prioritaire)
        for key, value in web_data.items():
            result.setdefault(key, value)

    result["enrichment_source"] = sources
    result["enrichment_status"] = "enriched" if (sources and any(
        result.get(f) for f in ("owner_last_name", "phone", "contact_email")
    )) else "no_result"
    result["keys_configured"] = {
        "pappers": pappers.enabled,
        "perplexity": perplexity.enabled,
    }
    return result
