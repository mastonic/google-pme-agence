"""Catalogue commercial unique de Pulse Locale PME (édité par HoldMasto).

Tous les prix sont HT. Paiement annuel : 10 mois payés pour 12 (2 mois offerts).
"""

ANNUAL_MONTHS_PAID = 10   # paiement annuel = 10 × le prix mensuel (2 mois offerts)
FAIR_USE_MODIFICATIONS = 10  # Élite : « illimité » encadré par un usage raisonnable

PLAN_CATALOG = {
    "starter": {
        "slug": "starter",
        "name": "Starter",
        "positioning": "Présence professionnelle",
        "price": 49,
        "currency": "eur",
        "is_popular": False,
        "summary": "Pour avoir une présence web propre, rassurante et toujours à jour.",
        "features": [
            "Site vitrine professionnel jusqu’à 5 pages",
            "Design mobile-first adapté au secteur",
            "Hébergement, SSL et maintenance technique inclus",
            "Formulaire de contact + téléphone + WhatsApp",
            "Google Maps, horaires et informations pratiques",
            "Mise en ligne et supervision du site",
            "1 petite modification de contenu par mois",
            "Support par email",
        ],
        "not_included": [
            "SEO local mensuel actif",
            "Gestion de la fiche Google",
            "Automatisation des avis",
            "Chatbot IA / WhatsApp",
        ],
        "limits": {
            "pages": 5,
            "modifications_per_month": 1,
            "seo_articles_per_month": 0,
            "custom_domain": False,
        },
        "agent_teams": ["domain-watch"],
        "feature_flags": {
            "features_booking_active": False,
            "features_menu_active": True,
            "features_click_collect_active": False,
            "features_chatbot_active": False,
            "features_seo_blog_active": False,
            "features_gmb_reviews_sync": False,
            "features_multilang_active": False,
        },
    },
    "pro": {
        "slug": "pro",
        "name": "Pro",
        "positioning": "Visibilité & acquisition locale",
        "price": 149,
        "currency": "eur",
        "is_popular": True,
        "summary": "Pour être mieux trouvé sur Google et transformer plus de recherches locales en contacts.",
        "features": [
            "Tout le plan Starter",
            "Nom de domaine personnalisé connecté",
            "SEO local : pages, balises et mots-clés prioritaires",
            "Optimisation et suivi de la fiche Google Business",
            "Mise en avant et synchronisation des avis Google",
            "Module métier : réservation, menu/catalogue ou demande de devis selon activité",
            "Suivi des appels, clics WhatsApp et demandes de contact",
            "Rapport mensuel de visibilité et de performance",
            "3 modifications de contenu par mois",
            "Support prioritaire",
        ],
        "not_included": [
            "Chatbot IA / WhatsApp automatisé",
            "Production SEO continue avancée",
            "Automatisations multicanales",
        ],
        "limits": {
            "pages": 10,
            "modifications_per_month": 3,
            "seo_articles_per_month": 0,
            "custom_domain": True,
        },
        "agent_teams": ["domain-watch", "seo-local"],
        "feature_flags": {
            "features_booking_active": True,
            "features_menu_active": True,
            "features_click_collect_active": True,
            "features_chatbot_active": False,
            "features_seo_blog_active": False,
            "features_gmb_reviews_sync": True,
            "features_multilang_active": False,
        },
    },
    "elite": {
        "slug": "elite",
        "name": "Élite",
        "positioning": "Croissance & automatisation",
        "price": 299,
        "currency": "eur",
        "is_popular": False,
        "summary": "Pour automatiser l’acquisition, le suivi client et la croissance locale.",
        "features": [
            "Tout le plan Pro",
            "SEO avancé et production de contenu régulière",
            "Réceptionniste IA incluse (appels manqués + WhatsApp, 100 appels/mois)",
            "Pack Connecté inclus : Google Agenda, Google Sheets, Zapier / Make",
            "Chatbot IA / assistant WhatsApp pour capter les demandes",
            "Automatisation des demandes et relances d’avis clients",
            "Minimum garanti chaque mois : 4 contenus SEO + 4 publications Google",
            "Réservation, catalogue/menu et Click & Collect selon activité",
            "Suivi des conversions et tableau de bord renforcé",
            "Version multilingue si nécessaire",
            "Optimisations mensuelles de conversion",
            "Jusqu’à 10 demandes de modification par mois (usage raisonnable)",
            "Support prioritaire renforcé",
        ],
        "not_included": [],
        "limits": {
            "pages": -1,
            "modifications_per_month": FAIR_USE_MODIFICATIONS,
            "seo_articles_per_month": 4,
            "google_posts_per_month": 4,
            "custom_domain": True,
        },
        "includes_addons": ["receptionniste_ia", "pack_connecte"],
        "agent_teams": ["domain-watch", "seo-local", "social-media"],
        "feature_flags": {
            "features_booking_active": True,
            "features_menu_active": True,
            "features_click_collect_active": True,
            "features_chatbot_active": True,
            "features_seo_blog_active": True,
            "features_gmb_reviews_sync": True,
            "features_multilang_active": True,
        },
    },
}


def annual_price(slug: str) -> int:
    """Prix HT d'un an payé d'avance (2 mois offerts)."""
    return int(PLAN_CATALOG[slug]["price"] * ANNUAL_MONTHS_PAID)


def public_plan_catalog():
    return [
        {
            "slug": p["slug"],
            "name": p["name"],
            "positioning": p["positioning"],
            "price": p["price"],
            "annual_price": annual_price(p["slug"]),
            "includes_addons": p.get("includes_addons", []),
            "currency": p["currency"],
            "summary": p["summary"],
            "features": p["features"],
            "not_included": p["not_included"],
            "limits": p["limits"],
            "agent_teams": p.get("agent_teams", []),
            "is_popular": p["is_popular"],
        }
        for p in PLAN_CATALOG.values()
    ]


def apply_plan_features(business, slug: str, billing: str = "monthly"):
    plan = PLAN_CATALOG.get(slug)
    if not plan:
        return business
    business.plan_tier = slug
    # MRR : équivalent mensuel réellement encaissé (annuel = 10 mois / 12).
    business.mrr_value = round(annual_price(slug) / 12, 2) if billing == "annual" else float(plan["price"])
    for field, value in plan["feature_flags"].items():
        setattr(business, field, value)
    return business


# ──────────────────────────────────────────────────────────────────────────────
# MODULES COMPLÉMENTAIRES (add-ons)
# ──────────────────────────────────────────────────────────────────────────────
import datetime as _dt

RECEPTIONIST_ADDON = "receptionniste_ia"
CONNECT_ADDON = "pack_connecte"

ADDON_CATALOG = {
    RECEPTIONIST_ADDON: {
        "slug": RECEPTIONIST_ADDON,
        "name": "Réceptionniste IA",
        "summary": "Répond aux appels manqués, qualifie la demande et vous envoie un résumé par WhatsApp ou SMS.",
        "price": 39,          # € HT/mois, incluse dans la formule Élite
        "included_calls": 100,       # appels ou conversations inclus par mois (option payante / Élite)
        "trial_calls": 60,           # plafond de l'essai gratuit de 30 jours
        "extra_call_price": 0.83,    # € HT par appel au-delà du forfait
        "extra_call_price_ttc": 1.0, # soit 1 € TTC
        "currency": "eur",
        "trial_days": 30,
    },
    CONNECT_ADDON: {
        "slug": CONNECT_ADDON,
        "name": "Pack Connecté",
        "summary": "Google Agenda (prise de rendez-vous par l'IA), Google Sheets (registre des appels) et webhook "
                   "Zapier / Make vers n'importe quelle application.",
        "price": 19,          # € HT/mois, inclus dans la formule Élite, offert pendant l'essai de la réceptionniste
        "currency": "eur",
    },
}

ADDON_STATUSES = ("inactive", "trial", "active", "expired")


def start_addon_trial(state, now=None, slug: str = RECEPTIONIST_ADDON):
    """Démarre l'essai gratuit à l'activation. Idempotent : un essai déjà démarré n'est jamais relancé."""
    now = now or _dt.datetime.utcnow()
    if getattr(state, "trial_started_at", None):
        return state
    state.trial_started_at = now
    state.trial_ends_at = now + _dt.timedelta(days=ADDON_CATALOG[slug]["trial_days"])
    return state


def plan_includes_addon(business, slug: str = RECEPTIONIST_ADDON) -> bool:
    """Le module est-il compris dans la formule payée du commerce (ex. Élite) ?"""
    if business is None or getattr(business, "subscription_status", None) != "active":
        return False
    plan = PLAN_CATALOG.get(getattr(business, "plan_tier", None) or "")
    return bool(plan and slug in plan.get("includes_addons", []))


def addon_status(state, now=None, included: bool = False) -> str:
    """active (payé ou inclus dans la formule) | trial (essai en cours) | expired (essai terminé, non payé)
    | inactive (jamais activé)."""
    if included:
        return "active"
    if state is None:
        return "inactive"
    if getattr(state, "paid_active", False):
        return "active"
    ends = getattr(state, "trial_ends_at", None)
    if not ends:
        return "inactive"
    return "trial" if (now or _dt.datetime.utcnow()) < ends else "expired"


def days_left(state, now=None, included: bool = False) -> int:
    """Jours d'essai restants (arrondi au jour supérieur, 0 si terminé, payé ou inclus)."""
    if included:
        return 0
    ends = getattr(state, "trial_ends_at", None) if state is not None else None
    if not ends or getattr(state, "paid_active", False):
        return 0
    seconds = (ends - (now or _dt.datetime.utcnow())).total_seconds()
    return max(0, -(-int(seconds) // 86400))


def addon_ai_enabled(state, now=None, included: bool = False) -> bool:
    return addon_status(state, now, included) in ("trial", "active")
