"""Single source of truth for Local Pulse commercial subscriptions."""

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
            "Jusqu’à 4 contenus SEO optimisés par mois",
            "Chatbot IA / assistant WhatsApp pour capter les demandes",
            "Automatisation des demandes et relances d’avis clients",
            "Réservation, catalogue/menu et Click & Collect selon activité",
            "Suivi des conversions et tableau de bord renforcé",
            "Version multilingue si nécessaire",
            "Optimisations mensuelles de conversion",
            "Modifications courantes illimitées",
            "Support prioritaire renforcé",
        ],
        "not_included": [],
        "limits": {
            "pages": -1,
            "modifications_per_month": -1,
            "seo_articles_per_month": 4,
            "custom_domain": True,
        },
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


def public_plan_catalog():
    return [
        {
            "slug": p["slug"],
            "name": p["name"],
            "positioning": p["positioning"],
            "price": p["price"],
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


def apply_plan_features(business, slug: str):
    plan = PLAN_CATALOG.get(slug)
    if not plan:
        return business
    business.plan_tier = slug
    business.mrr_value = float(plan["price"])
    for field, value in plan["feature_flags"].items():
        setattr(business, field, value)
    return business
