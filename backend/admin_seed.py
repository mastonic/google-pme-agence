"""Seed default Plans and DesignPresets on first launch."""
from backend.models.database import SessionLocal, Plan, DesignPreset

DEFAULT_PLANS = [
    {
        "name": "Starter",
        "slug": "starter",
        "price": 49.0,
        "color": "#6366f1",
        "icon": "🥉",
        "badge": None,
        "is_popular": False,
        "sort_order": 0,
        "features": [
            {"text": "Sous-domaine local-pulse.app", "included": True},
            {"text": "Site 1 page optimisé", "included": True},
            {"text": "Fiche Google My Business", "included": True},
            {"text": "Hébergement + SSL inclus", "included": True},
            {"text": "Rapport SEO mensuel", "included": True},
            {"text": "1 modification / mois", "included": True},
            {"text": "Nom de domaine personnalisé", "included": False},
            {"text": "Articles SEO automatiques", "included": False},
            {"text": "Avis Google en direct", "included": False},
        ],
        "limits": {"pages": 1, "articles_per_month": 0, "modifications": 1, "custom_domain": False},
    },
    {
        "name": "Pro",
        "slug": "pro",
        "price": 149.0,
        "color": "#0071E3",
        "icon": "🥈",
        "badge": "Le plus populaire",
        "is_popular": True,
        "sort_order": 1,
        "features": [
            {"text": "Nom de domaine personnalisé", "included": True},
            {"text": "Site multi-pages (jusqu'à 5)", "included": True},
            {"text": "SEO local actif (mots-clés + positions)", "included": True},
            {"text": "2 articles SEO IA / mois", "included": True},
            {"text": "Avis Google synchronisés en direct", "included": True},
            {"text": "Rapport de positions hebdomadaire", "included": True},
            {"text": "3 modifications / mois", "included": True},
            {"text": "Module réservations en ligne", "included": False},
            {"text": "Blog automatisé complet", "included": False},
        ],
        "limits": {"pages": 5, "articles_per_month": 2, "modifications": 3, "custom_domain": True},
    },
    {
        "name": "Elite",
        "slug": "elite",
        "price": 299.0,
        "color": "#d97706",
        "icon": "🥇",
        "badge": None,
        "is_popular": False,
        "sort_order": 2,
        "features": [
            {"text": "Nom de domaine offert + SSL auto", "included": True},
            {"text": "Site complet (pages illimitées)", "included": True},
            {"text": "SEO avancé + stratégie backlinks", "included": True},
            {"text": "4 articles SEO IA / mois", "included": True},
            {"text": "Module réservations en ligne", "included": True},
            {"text": "Catalogue produits / Carte menu", "included": True},
            {"text": "Audit SEO trimestriel + appel stratégie", "included": True},
            {"text": "Support prioritaire 7j/7", "included": True},
            {"text": "Modifications illimitées", "included": True},
        ],
        "limits": {"pages": -1, "articles_per_month": 4, "modifications": -1, "custom_domain": True},
    },
]

DEFAULT_PRESETS = [
    {
        "name": "luxury-dining",
        "label": "Restaurant / Café / Brasserie",
        "sectors": ["restaurant", "food", "cafe", "bar", "bakery"],
        "colors": {"primary": "#1A1208", "secondary": "#C8922A", "accent": "#E8D5A3", "bg": "#FDFAF5", "text": "#2D2010"},
        "fonts": {"heading": "Playfair Display", "body": "Lato"},
        "mood": "chaleureux, artisanal, premium, gourmand",
    },
    {
        "name": "clean-medical",
        "label": "Santé / Pharmacie / Médecin",
        "sectors": ["pharmacy", "doctor", "health", "hospital", "dentist", "physiotherapist"],
        "colors": {"primary": "#0E7490", "secondary": "#06B6D4", "accent": "#CFFAFE", "bg": "#F8FFFE", "text": "#164E63"},
        "fonts": {"heading": "Inter", "body": "Inter"},
        "mood": "rassurant, professionnel, propre, moderne",
    },
    {
        "name": "industrial-bold",
        "label": "Garage / Auto / Mécanique",
        "sectors": ["car_repair", "car_dealer", "gas_station", "car_wash"],
        "colors": {"primary": "#1C1C1C", "secondary": "#F97316", "accent": "#FED7AA", "bg": "#F5F5F5", "text": "#1C1C1C"},
        "fonts": {"heading": "Outfit", "body": "Inter"},
        "mood": "robuste, expert, technique, fiable",
    },
    {
        "name": "modern-beauty",
        "label": "Coiffure / Beauté / Spa",
        "sectors": ["beauty_salon", "spa", "hair_care", "nail_salon", "barber"],
        "colors": {"primary": "#7C3AED", "secondary": "#C4B5FD", "accent": "#F5F3FF", "bg": "#FDFCFF", "text": "#1E1B2E"},
        "fonts": {"heading": "Cormorant Garamond", "body": "Nunito"},
        "mood": "élégant, féminin, luxueux, apaisant",
    },
    {
        "name": "artisan-bakery",
        "label": "Boulangerie / Pâtisserie",
        "sectors": ["bakery", "pastry"],
        "colors": {"primary": "#78350F", "secondary": "#D97706", "accent": "#FEF3C7", "bg": "#FFFBF0", "text": "#3D1A00"},
        "fonts": {"heading": "Libre Baskerville", "body": "Merriweather Sans"},
        "mood": "chaleureux, artisanal, appétissant, authentique",
    },
    {
        "name": "fresh-market",
        "label": "Épicerie / Primeurs / Bio",
        "sectors": ["grocery_or_supermarket", "food", "supermarket"],
        "colors": {"primary": "#15803D", "secondary": "#4ADE80", "accent": "#DCFCE7", "bg": "#F7FFF8", "text": "#14532D"},
        "fonts": {"heading": "Nunito", "body": "Open Sans"},
        "mood": "frais, naturel, sain, local",
    },
    {
        "name": "tech-services",
        "label": "Informatique / Tech / Telecom",
        "sectors": ["electronics_store", "computer_store"],
        "colors": {"primary": "#1E40AF", "secondary": "#3B82F6", "accent": "#DBEAFE", "bg": "#F8FAFF", "text": "#1E3A5F"},
        "fonts": {"heading": "Space Grotesk", "body": "Inter"},
        "mood": "innovant, moderne, fiable, expertise",
    },
    {
        "name": "legal-premium",
        "label": "Avocat / Notaire / Expert-Comptable",
        "sectors": ["lawyer", "accounting"],
        "colors": {"primary": "#1E1B4B", "secondary": "#7C3AED", "accent": "#EDE9FE", "bg": "#FAFAFA", "text": "#1E1B4B"},
        "fonts": {"heading": "EB Garamond", "body": "Source Sans 3"},
        "mood": "sérieux, prestige, confiance, professionnel",
    },
]


def seed_if_empty(db=None):
    """Seed plans and design presets if tables are empty."""
    if db is not None:
        _do_seed(db)
        return
    db = SessionLocal()
    try:
        _do_seed(db)
    finally:
        db.close()


def _do_seed(db):
    if db.query(Plan).count() == 0:
        for p in DEFAULT_PLANS:
            db.add(Plan(**p))
        print(f"Seeded {len(DEFAULT_PLANS)} plans")

    if db.query(DesignPreset).count() == 0:
        for d in DEFAULT_PRESETS:
            db.add(DesignPreset(**d))
        print(f"Seeded {len(DEFAULT_PRESETS)} design presets")

    db.commit()
