from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "local_pulse.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Business(Base):
    __tablename__ = "businesses"

    # Core
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    rating = Column(Float)
    user_ratings_total = Column(Float)
    photos = Column(JSON)
    website = Column(String)
    status = Column(String, default="scanned")  # scanned › processing › pending_validation › completed
    # Legacy score 0-10 conservé pour compatibilité UI / anciens enregistrements.
    potential_score = Column(Float, default=0.0)
    # Run 1 — scoring commercial séparé de la santé digitale.
    digital_health_score = Column(Float, default=0.0)           # 0-100, haut = présence digitale forte
    opportunity_score = Column(Float, default=0.0)              # 0-100, haut = prospect prioritaire
    opportunity_breakdown = Column(JSON, nullable=True)
    website_audit = Column(JSON, nullable=True)
    website_audit_status = Column(String, default="not_audited")
    business_phone = Column(String, nullable=True)
    category = Column(JSON)
    template = Column(String)
    email_status = Column(String, default="not_sent")
    generated_copy = Column(JSON)
    generated_html = Column(Text)
    site_config = Column(JSON)        # structured JSON config for the dynamic renderer
    deployment_url = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # ── SaaS subscription ──────────────────────────────────────
    plan_tier = Column(String, default="free")                 # free | starter | pro | elite
    subscription_status = Column(String, default="inactive")   # inactive | trialing | active | cancelled
    mrr_value = Column(Float, default=0.0)                     # 0 / 49 / 149 / 299
    client_signed_at = Column(DateTime, nullable=True)

    # ── Hosting & domain ───────────────────────────────────────
    custom_domain = Column(String, nullable=True)              # ex: www.moncommerce.fr
    domain_ssl_active = Column(Boolean, default=False)

    # ── Feature flags (toggled per-client by admin) ────────────
    features_booking_active       = Column(Boolean, default=False)   # Réservations en ligne
    features_menu_active          = Column(Boolean, default=False)   # Carte / Catalogue produits
    features_click_collect_active = Column(Boolean, default=False)   # Click & Collect
    features_chatbot_active       = Column(Boolean, default=False)   # Chatbot WhatsApp IA
    features_seo_blog_active      = Column(Boolean, default=False)   # Articles SEO auto
    features_gmb_reviews_sync     = Column(Boolean, default=False)   # Avis Google live
    features_multilang_active     = Column(Boolean, default=False)   # Site multilingue

    # ── SEO metrics ────────────────────────────────────────────
    seo_score = Column(Float, default=0.0)
    keywords_tracked = Column(JSON, nullable=True)             # [{"keyword": "...", "position": 5}]

    # ── CRM ────────────────────────────────────────────────────
    crm_stage = Column(String, default="prospect")             # prospect|contacted|demo_sent|negotiating|won|lost
    crm_notes = Column(Text, nullable=True)
    next_contact_at = Column(DateTime, nullable=True)
    priority = Column(String, default="medium")                # low|medium|high|urgent
    owner_email = Column(String, nullable=True)
    owner_phone = Column(String, nullable=True)
    # ── Enrichissement Pappers / Perplexity ────────────────────
    owner_first_name = Column(String, nullable=True)   # Prénom du dirigeant (Pappers)
    owner_last_name = Column(String, nullable=True)    # Nom du dirigeant (Pappers)
    owner_role = Column(String, nullable=True)         # Qualité (Gérant, Président…)
    siren = Column(String, nullable=True)              # SIREN (Pappers)
    legal_form = Column(String, nullable=True)
    company_creation_date = Column(String, nullable=True)
    employee_range = Column(String, nullable=True)
    enrichment_details = Column(JSON, nullable=True)    # provenance, citations, confiance
    contact_confidence = Column(Float, default=0.0)     # 0-100
    enrichment_status = Column(String, default="not_enriched")
    # ── Supervision (SSL / avis / SEO) ─────────────────────────
    monitoring = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    deal_value = Column(Float, default=0.0)
    last_contacted_at = Column(DateTime, nullable=True)

    # ── Run 2 : moteur commercial interne ──────────────────────
    sales_snapshot = Column(JSON, nullable=True)
    outreach_sequence = Column(JSON, nullable=True)
    outreach_status = Column(String, default="not_started")      # not_started|active|completed|paused
    outreach_step = Column(Integer, default=0)
    outreach_started_at = Column(DateTime, nullable=True)
    last_outreach_at = Column(DateTime, nullable=True)
    next_action = Column(String, nullable=True)
    next_action_reason = Column(Text, nullable=True)
    next_action_due_at = Column(DateTime, nullable=True)
    prospecting_opt_out = Column(Boolean, default=False)


class CrmActivity(Base):
    __tablename__ = "crm_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String, index=True)
    type = Column(String)                                      # call|email|meeting|demo_sent|note
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)         # starter | pro | elite
    price = Column(Float, nullable=False)
    color = Column(String, default="#0071E3")
    icon = Column(String, default="✨")
    badge = Column(String, nullable=True)                      # ex: "Le plus populaire"
    is_popular = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    features = Column(JSON)    # [{"text": "Site 1 page", "included": true}, ...]
    limits = Column(JSON)      # {"pages": 1, "articles_per_month": 0, "modifications": 1, "custom_domain": false}
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class DesignPreset(Base):
    __tablename__ = "design_presets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)                      # "luxury-dining"
    label = Column(String, nullable=False)                     # "Restaurant / Café"
    sectors = Column(JSON)     # ["restaurant", "food", "cafe"]
    colors = Column(JSON)      # {"primary":"#","secondary":"#","accent":"#","bg":"#","text":"#"}
    fonts = Column(JSON)       # {"heading": "Playfair Display", "body": "Lato"}
    mood = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
