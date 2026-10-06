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
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)
    generated_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    email_ready_at = Column(DateTime, nullable=True)
    automation_source = Column(String, nullable=True)  # manual | autopilot:<zone_id>
    automation_last_scanned_at = Column(DateTime, nullable=True)
    automation_selected_at = Column(DateTime, nullable=True)
    automation_error_at = Column(DateTime, nullable=True)
    automation_warning_at = Column(DateTime, nullable=True)
    automation_warning_message = Column(Text, nullable=True)

    # ── Client onboarding / source of truth ─────────────────────
    onboarding_token = Column(String, nullable=True, unique=True, index=True)
    onboarding_status = Column(String, default="not_started")  # not_started|in_progress|complete
    onboarding_completeness = Column(Float, default=0.0)
    onboarding_updated_at = Column(DateTime, nullable=True)
    client_profile = Column(JSON, nullable=True)

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


class AgentTeam(Base):
    __tablename__ = "agent_teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, default="general")
    source_type = Column(String, default="builtin")  # builtin | git
    source_url = Column(String, nullable=True)
    manifest = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)
    version = Column(String, default="1")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class BusinessAgentTeam(Base):
    __tablename__ = "business_agent_teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String, index=True, nullable=False)
    team_slug = Column(String, index=True, nullable=False)
    enabled = Column(Boolean, default=True)
    source = Column(String, default="plan")  # plan | manual
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AgentTeamRun(Base):
    __tablename__ = "agent_team_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_slug = Column(String, index=True, nullable=False)
    business_id = Column(String, index=True, nullable=True)
    status = Column(String, default="queued")  # queued|running|completed|error
    trigger = Column(String, default="manual")
    outputs = Column(JSON, nullable=True)
    logs = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AutomationZone(Base):
    __tablename__ = "automation_zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    query = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Integer, default=1000)
    enabled = Column(Boolean, default=True)
    min_opportunity_score = Column(Float, default=62.0)
    max_sites_per_run = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger = Column(String, default="scheduled")  # scheduled | manual
    status = Column(String, default="running")     # running | completed | partial | error
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    zones_processed = Column(Integer, default=0)
    businesses_scanned = Column(Integer, default=0)
    opportunities_selected = Column(Integer, default=0)
    sites_generated = Column(Integer, default=0)
    sites_deployed = Column(Integer, default=0)
    emails_ready = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    warnings_count = Column(Integer, default=0)
    summary = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    current_business_id = Column(String, nullable=True)
    current_business_name = Column(String, nullable=True)
    current_stage = Column(String, nullable=True)
    current_index = Column(Integer, default=0)
    total_selected = Column(Integer, default=0)
    heartbeat_at = Column(DateTime, nullable=True)


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


class PmtVoucher(Base):
    """Bon de transport (PMT Cerfa 11574*04) d'un client ambulancier.

    Le scan est conservé hors base (PMT_SCAN_DIR) pour être joint au dossier
    exporté (pièce justificative SCOR), et supprimé avec le dossier.
    """
    __tablename__ = "pmt_vouchers"

    id = Column(String, primary_key=True, index=True)
    business_id = Column(String, nullable=True, index=True)   # client ambulancier
    source_filename = Column(String, nullable=True)
    extraction_provider = Column(String, nullable=True)       # gemini-… | openai-… | manual
    data = Column(JSON, nullable=True)                         # PmtData
    transport = Column(JSON, nullable=True)                    # TransportDetails
    transporteur = Column(JSON, nullable=True)                 # cadre volet 2
    checks = Column(JSON, nullable=True)
    readiness = Column(String, default="a_verifier")           # pret | a_verifier | bloquant
    status = Column(String, default="draft")                   # draft | validated | exported | billed
    scan_path = Column(String, nullable=True)
    scan_mime = Column(String, nullable=True)
    exported_at = Column(DateTime, nullable=True)
    export_batch = Column(String, nullable=True)
    export_snapshot = Column(JSON, nullable=True)   # contrôles figés au moment de l'export (preuve en cas de contrôle)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class PmtExportProfile(Base):
    """Format d'export adapté au logiciel de facturation d'un client ambulancier."""
    __tablename__ = "pmt_export_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String, nullable=True, index=True)
    name = Column(String, nullable=False)
    config = Column(JSON, nullable=False)   # voir backend.services.pmt_export.ExportProfile
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class PmtUser(Base):
    """Compte d'accès au module transport sanitaire (agence ou client ambulancier)."""
    __tablename__ = "pmt_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="client")          # admin | client
    business_id = Column(String, nullable=True, index=True)  # entreprise du client
    active = Column(Boolean, default=True)
    token_version = Column(Integer, default=1)       # +1 = déconnexion de toutes les sessions
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PmtReturn(Base):
    """Ligne de retour CPAM / mutuelle (rejet, paiement, retenue) rattachée à un dossier de transport."""
    __tablename__ = "pmt_returns"

    id = Column(String, primary_key=True, index=True)
    line_key = Column(String, unique=True, index=True)        # empreinte anti-doublon d'import
    business_id = Column(String, nullable=True, index=True)
    voucher_id = Column(String, nullable=True, index=True)
    match_score = Column(Integer, default=0)
    import_batch = Column(String, nullable=True)
    source = Column(String, nullable=True)                    # b2r | tableur | document | manuel
    type_retour = Column(String, default="rejet")             # paiement | rejet | retenue | contestation
    part = Column(String, nullable=True)                      # ro | rc | ro+rc
    numero_facture = Column(String, nullable=True)
    date_facturation = Column(String, nullable=True)
    date_soins = Column(String, nullable=True)
    nir = Column(String, nullable=True)
    nom_patient = Column(String, nullable=True)
    organisme = Column(String, nullable=True)
    montant_facture = Column(Float, nullable=True)
    montant_paye = Column(Float, nullable=True)
    code_rejet = Column(String, nullable=True)
    libelle_rejet = Column(Text, nullable=True)
    categorie = Column(String, nullable=True)
    diagnostic = Column(String, nullable=True)
    status = Column(String, default="a_traiter")              # a_traiter | en_correction | renvoye | recupere | abandonne
    note = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
