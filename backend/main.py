from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse, Response, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.agents.manager import LocalPulseManager
from backend.services.google_maps import GoogleMapsService
from backend.services.apify_maps import ApifyMapsService
from backend.services.enrichment import enrich_business, WebsiteContactFinder, PerplexityService
from backend.services.scoring import calculate_scores
from backend.services.website_audit import audit_website
from backend.services.monitoring import run_monitoring
from backend.services.scheduler import DailyScheduler
from backend.services.autopilot import run_autopilot
from backend.services.plans import PLAN_CATALOG, public_plan_catalog, apply_plan_features
from backend.services.agent_teams import BUILTIN_MANIFESTS, validate_manifest, fetch_git_manifest, run_safe_tool
from backend.services.agent_prompts_v2 import build_system_prompt, validate_agent_output, repair_prompt
from backend.services.client_onboarding import empty_profile, merge_profile, onboarding_progress, ensure_token, agent_business_context, agent_team_readiness
from backend.models.database import engine, Base, get_db, Business, Plan, DesignPreset, CrmActivity, AgentTeam, BusinessAgentTeam, AgentTeamRun, AutomationZone, AutomationRun
from dotenv import load_dotenv
import os
import asyncio
import json
import re
import datetime
import urllib.parse
import urllib.request
import redis

load_dotenv()

active_logs = {}   # business_id -> asyncio.Queue (SSE, legacy)
log_buffers = {}   # business_id -> {"entries": [...], "finished": bool} (polling)
supervision_scheduler = None   # planificateur de supervision quotidienne
autopilot_scheduler = None      # pipeline nocturne de prospection / génération

try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("Backend : Connecté à Redis")
except Exception:
    class DummyRedis:
        def __init__(self): self.store = {}
        def set(self, k, v, ex=None): self.store[k] = v
        def get(self, k): return self.store.get(k)
    redis_client = DummyRedis()

app = FastAPI(title="Local-Pulse SaaS API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────────────────────
# STARTUP
# ──────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

    # SQLite migrations — add new columns to existing tables
    from sqlalchemy import text, inspect
    NEW_COLS = {
        "businesses": {
            "generated_html": "TEXT",
            "site_config": "TEXT",
            "plan_tier": "TEXT DEFAULT 'free'",
            "subscription_status": "TEXT DEFAULT 'inactive'",
            "mrr_value": "REAL DEFAULT 0",
            "client_signed_at": "TEXT",
            "custom_domain": "TEXT",
            "domain_ssl_active": "INTEGER DEFAULT 0",
            "features_booking_active": "INTEGER DEFAULT 0",
            "features_menu_active": "INTEGER DEFAULT 0",
            "features_click_collect_active": "INTEGER DEFAULT 0",
            "features_chatbot_active": "INTEGER DEFAULT 0",
            "features_seo_blog_active": "INTEGER DEFAULT 0",
            "features_gmb_reviews_sync": "INTEGER DEFAULT 0",
            "features_multilang_active": "INTEGER DEFAULT 0",
            "seo_score": "REAL DEFAULT 0",
            "keywords_tracked": "TEXT",
            "crm_stage": "TEXT DEFAULT 'prospect'",
            "crm_notes": "TEXT",
            "next_contact_at": "TEXT",
            "priority": "TEXT DEFAULT 'medium'",
            "owner_email": "TEXT",
            "owner_phone": "TEXT",
            "owner_first_name": "TEXT",
            "owner_last_name": "TEXT",
            "owner_role": "TEXT",
            "siren": "TEXT",
            "enrichment_status": "TEXT DEFAULT 'not_enriched'",
            "monitoring": "TEXT",
            "tags": "TEXT",
            "deal_value": "REAL DEFAULT 0",
            "last_contacted_at": "TEXT",
            # Run 1 — prospection intelligente
            "digital_health_score": "REAL DEFAULT 0",
            "opportunity_score": "REAL DEFAULT 0",
            "opportunity_breakdown": "TEXT",
            "website_audit": "TEXT",
            "website_audit_status": "TEXT DEFAULT 'not_audited'",
            "business_phone": "TEXT",
            "legal_form": "TEXT",
            "company_creation_date": "TEXT",
            "employee_range": "TEXT",
            "enrichment_details": "TEXT",
            "contact_confidence": "REAL DEFAULT 0",
            # Autopilot lifecycle
            "discovered_at": "TEXT",
            "generated_at": "TEXT",
            "deployed_at": "TEXT",
            "email_ready_at": "TEXT",
            "automation_source": "TEXT",
            "onboarding_token": "TEXT",
            "onboarding_status": "TEXT DEFAULT 'not_started'",
            "onboarding_completeness": "REAL DEFAULT 0",
            "onboarding_updated_at": "TEXT",
            "client_profile": "TEXT",
            "automation_last_scanned_at": "TEXT",
            "automation_selected_at": "TEXT",
            "automation_error_at": "TEXT",
        },
        "automation_runs": {
            "current_business_id": "TEXT",
            "current_business_name": "TEXT",
            "current_stage": "TEXT",
            "current_index": "INTEGER DEFAULT 0",
            "total_selected": "INTEGER DEFAULT 0",
            "heartbeat_at": "TEXT",
        }
    }
    try:
        inspector = inspect(engine)
        for table, cols in NEW_COLS.items():
            try:
                existing = {c["name"] for c in inspector.get_columns(table)}
                with engine.connect() as conn:
                    for col, typedef in cols.items():
                        if col not in existing:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}"))
                            print(f"Migration: {table}.{col} added")
                    conn.commit()
            except Exception as e:
                print(f"Migration {table}: {e}")
    except Exception as e:
        print(f"Migration skipped: {e}")

    # Seed default plans and design presets
    from backend.admin_seed import seed_if_empty
    seed_if_empty()  # creates its own session and closes it properly

    # Sync built-in declarative agent teams. Git-installed teams are preserved.
    from backend.models.database import SessionLocal as _SeedSession
    _team_db = _SeedSession()
    try:
        for manifest in BUILTIN_MANIFESTS:
            manifest = validate_manifest(dict(manifest))
            row = _team_db.query(AgentTeam).filter(AgentTeam.slug == manifest["slug"]).first()
            if row is None:
                row = AgentTeam(
                    slug=manifest["slug"],
                    name=manifest["name"],
                    description=manifest.get("description"),
                    category=manifest.get("category", "general"),
                    source_type="builtin",
                    source_url=None,
                    manifest=manifest,
                    enabled=True,
                    version=manifest.get("version", "1"),
                )
                _team_db.add(row)
            elif row.source_type == "builtin":
                row.name = manifest["name"]
                row.description = manifest.get("description")
                row.category = manifest.get("category", "general")
                row.manifest = manifest
                row.version = manifest.get("version", "1")
        _team_db.commit()
    finally:
        _team_db.close()

    # Planificateur de supervision quotidienne (matin, fenêtre 8h–8h45 par défaut)
    global supervision_scheduler
    if os.getenv("MONITOR_SCHEDULE_ENABLED", "true").lower() == "true":
        try:
            supervision_scheduler = DailyScheduler(
                scheduled_supervision,
                hour=int(os.getenv("MONITOR_HOUR", "8")),
                window_minutes=int(os.getenv("MONITOR_WINDOW_MINUTES", "45")),
                tz=os.getenv("MONITOR_TZ", "Europe/Paris"),
                name="supervision-quotidienne",
            )
            supervision_scheduler.start()
            print(f"🛰️  Supervision planifiée : {supervision_scheduler.status()}")
        except Exception as e:
            print(f"Scheduler init warning: {e}")

    # Autopilot nocturne : scan -> scoring -> sites -> Vercel -> emails prêts.
    global autopilot_scheduler
    if os.getenv("AUTOPILOT_ENABLED", "true").lower() == "true":
        try:
            autopilot_scheduler = DailyScheduler(
                scheduled_autopilot,
                hour=int(os.getenv("AUTOPILOT_HOUR", "2")),
                window_minutes=int(os.getenv("AUTOPILOT_WINDOW_MINUTES", "20")),
                tz=os.getenv("AUTOPILOT_TZ", "Europe/Paris"),
                name="autopilot-prospection",
            )
            autopilot_scheduler.start()
            print(f"🤖 Autopilot planifié : {autopilot_scheduler.status()}")
        except Exception as e:
            print(f"Autopilot scheduler warning: {e}")

    print("✅ Local-Pulse Backend v2 Ready")



def _agent_team_to_dict(row: AgentTeam) -> dict:
    manifest = row.manifest or {}
    return {
        "slug": row.slug,
        "name": row.name,
        "description": row.description,
        "category": row.category,
        "source_type": row.source_type,
        "source_url": row.source_url,
        "enabled": bool(row.enabled),
        "version": row.version,
        "agents": manifest.get("agents") or [],
        "triggers": manifest.get("triggers") or ["manual"],
        "allowed_plans": manifest.get("allowed_plans") or [],
    }


def _sync_business_agent_teams(db: Session, business: Business, plan_slug: str):
    desired = set((PLAN_CATALOG.get(plan_slug) or {}).get("agent_teams", []))
    existing = db.query(BusinessAgentTeam).filter(BusinessAgentTeam.business_id == business.id).all()
    by_slug = {row.team_slug: row for row in existing}

    for slug in desired:
        row = by_slug.get(slug)
        if row is None:
            db.add(BusinessAgentTeam(
                business_id=business.id,
                team_slug=slug,
                enabled=True,
                source="plan",
            ))
        elif row.source == "plan":
            row.enabled = True

    for slug, row in by_slug.items():
        if row.source == "plan" and slug not in desired:
            row.enabled = False


def _business_team_slugs(db: Session, business_id: str) -> list[str]:
    return [
        row.team_slug for row in
        db.query(BusinessAgentTeam)
          .filter(BusinessAgentTeam.business_id == business_id, BusinessAgentTeam.enabled == True)
          .all()
    ]


# ──────────────────────────────────────────────────────────────────────────────
# HEALTH
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Local-Pulse SaaS API v2", "docs": "/docs"}

@app.get("/status")
async def get_status():
    return {
        "status": "Ready",
        "build_sha": os.getenv("APP_BUILD_SHA", "dev"),
        "scoring_engine": os.getenv("SCORING_ENGINE", "opportunity_v1"),
        "api_keys": {
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
            "mistral": bool(os.getenv("MISTRAL_API_KEY")),
            "google_maps": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
            "vercel": bool(os.getenv("VERCEL_API_TOKEN")),
            "pappers": bool(os.getenv("PAPPERS_API_KEY")),
            "perplexity": bool(os.getenv("PERPLEXITY_API_KEY")),
            "stripe": bool(os.getenv("STRIPE_SECRET_KEY")),
        }
    }

@app.get("/photo")
async def photo_proxy(url: str):
    """Proxy Google Places photo URLs to bypass CORS/referrer restrictions."""
    import requests as req_lib
    allowed = ("places.googleapis.com", "maps.googleapis.com", "images.unsplash.com", "fal.media", "storage.googleapis.com")
    if not any(h in url for h in allowed):
        raise HTTPException(status_code=403, detail="URL non autorisée")
    try:
        r = await asyncio.to_thread(lambda: req_lib.get(url, timeout=10, allow_redirects=True))
        ct = r.headers.get("content-type", "image/jpeg")
        return Response(content=r.content, media_type=ct,
                        headers={"Cache-Control": "public, max-age=86400",
                                 "Access-Control-Allow-Origin": "*"})
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.get("/geocode")
async def geocode_address(address: str):
    """Convert a city name or postal code to lat/lng."""
    maps_service = GoogleMapsService()
    result = maps_service.geocode(address)
    if isinstance(result, dict) and "error" in result:
        # Fallback to Nominatim (no API key needed)
        try:
            import urllib.request
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(address)}&format=json&limit=1"
            req = urllib.request.Request(url, headers={"User-Agent": "LocalPulse/2.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
            if data:
                return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"]), "display": data[0].get("display_name", address)}
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=f"Impossible de localiser : {address}")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# SITE PREVIEW & CONFIG
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/preview/{business_id}")
async def preview_business(business_id: str, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    if not b.generated_html:
        return HTMLResponse(
            "<html><body style='font-family:sans-serif;display:flex;align-items:center;"
            "justify-content:center;height:100vh;background:#0f172a;color:#94a3b8;'>"
            "<p>⏳ Génération en cours...</p></body></html>"
        )
    return HTMLResponse(content=b.generated_html)

@app.get("/sites/{business_id}/config")
async def get_site_config(business_id: str, db: Session = Depends(get_db)):
    """Return the structured JSON site config for the dynamic renderer."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    if not b.site_config:
        raise HTTPException(status_code=404, detail="No site config generated yet")
    config = b.site_config if isinstance(b.site_config, dict) else json.loads(b.site_config)
    # Overlay active feature flags from DB
    config["features"] = {
        "booking": b.features_booking_active,
        "menu": b.features_menu_active,
        "seo_blog": b.features_seo_blog_active,
        "gmb_reviews": b.features_gmb_reviews_sync,
    }
    config["plan_tier"] = b.plan_tier
    return config


# ──────────────────────────────────────────────────────────────────────────────
# SSE STREAM
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/stream/{business_id}")
async def stream_logs(business_id: str, request: Request):
    if business_id not in active_logs:
        active_logs[business_id] = asyncio.Queue()

    async def event_generator():
        q = active_logs[business_id]
        try:
            while True:
                if await request.is_disconnected():
                    break
                msg = await q.get()
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") == "end":
                    break
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/businesses/{business_id}/logs")
async def get_agent_logs(business_id: str, since: int = 0):
    """Polling fallback for agent logs when SSE (Firebase CDN) is unavailable."""
    buf = log_buffers.get(business_id, {"entries": [], "finished": True})
    entries = buf["entries"]
    return {
        "logs": entries[since:],
        "total": len(entries),
        "finished": buf["finished"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# BUSINESSES (Prospection CRM)
# ──────────────────────────────────────────────────────────────────────────────

def _score_input(data: dict) -> dict:
    """Normalise les données utilisées par les deux moteurs de score."""
    return {
        "website": data.get("website"),
        "rating": data.get("rating") or 0,
        "user_ratings_total": data.get("user_ratings_total") or 0,
        "photos": data.get("photos") or [],
        "category": data.get("category") or data.get("types") or [],
        "address": data.get("address") or data.get("formatted_address") or data.get("vicinity") or "",
        "business_phone": data.get("business_phone") or data.get("phone") or data.get("formatted_phone_number"),
        "owner_phone": data.get("owner_phone"),
        "owner_email": data.get("owner_email") or data.get("contact_email"),
    }


def calculate_potential_score(place_data: dict) -> float:
    """Compatibilité historique: Digital Health ramené sur 10."""
    scores = calculate_scores(_score_input(place_data), place_data.get("website_audit"))
    return round(scores["digital_health"]["score"] / 10.0, 1)


def score_breakdown_for(place_data: dict) -> dict:
    """Compatibilité UI: expose le détail du Digital Health."""
    return calculate_scores(_score_input(place_data), place_data.get("website_audit"))["digital_health"]


def _business_score_input(b: Business) -> dict:
    return _score_input({
        "website": b.website,
        "rating": b.rating,
        "user_ratings_total": b.user_ratings_total,
        "photos": b.photos or [],
        "category": b.category or [],
        "address": b.address,
        "business_phone": b.business_phone,
        "owner_phone": b.owner_phone,
        "owner_email": b.owner_email,
    })


def _refresh_scores(b: Business) -> dict:
    scores = calculate_scores(_business_score_input(b), b.website_audit)
    b.digital_health_score = scores["digital_health"]["score"]
    b.opportunity_score = scores["opportunity"]["score"]
    b.opportunity_breakdown = scores["opportunity"]
    # Legacy 0-10 conservé pour les anciennes vues / prompts.
    b.potential_score = round(b.digital_health_score / 10.0, 1)
    return scores


def _biz_to_dict(b: Business) -> dict:
    scores = calculate_scores(_business_score_input(b), b.website_audit)
    digital = float(b.digital_health_score or scores["digital_health"]["score"])
    opportunity = float(b.opportunity_score or scores["opportunity"]["score"])
    opportunity_breakdown = b.opportunity_breakdown or scores["opportunity"]

    return {
        "id": b.id, "name": b.name, "address": b.address,
        "latitude": b.latitude, "longitude": b.longitude,
        "rating": b.rating, "user_ratings_total": b.user_ratings_total,
        "status": b.status,
        # Legacy + Run 1
        "potential_score": round(digital / 10.0, 1),
        "digital_health_score": round(digital, 1),
        "opportunity_score": round(opportunity, 1),
        "opportunity_label": opportunity_breakdown.get("label") if isinstance(opportunity_breakdown, dict) else None,
        "opportunity_breakdown": opportunity_breakdown,
        "digital_health_breakdown": scores["digital_health"],
        "score_breakdown": scores["digital_health"],
        "website": b.website,
        "business_phone": b.business_phone,
        "website_audit": b.website_audit,
        "website_audit_status": b.website_audit_status,
        "template": b.template,
        "email_status": b.email_status, "generated_copy": b.generated_copy,
        "deployment_url": b.deployment_url,
        "generated_html": bool(b.generated_html),
        "category": b.category or [],
        # Offre / client
        "plan_tier": b.plan_tier, "subscription_status": b.subscription_status,
        "mrr_value": b.mrr_value or 0,
        "custom_domain": b.custom_domain, "domain_ssl_active": b.domain_ssl_active,
        "features_booking_active": b.features_booking_active,
        "features_menu_active": b.features_menu_active,
        "features_click_collect_active": b.features_click_collect_active,
        "features_chatbot_active": b.features_chatbot_active,
        "features_seo_blog_active": b.features_seo_blog_active,
        "features_gmb_reviews_sync": b.features_gmb_reviews_sync,
        "features_multilang_active": b.features_multilang_active,
        "seo_score": b.seo_score or 0, "keywords_tracked": b.keywords_tracked,
        # Enrichissement prospect
        "owner_first_name": b.owner_first_name, "owner_last_name": b.owner_last_name,
        "owner_role": b.owner_role, "siren": b.siren,
        "owner_email": b.owner_email, "owner_phone": b.owner_phone,
        "legal_form": b.legal_form,
        "company_creation_date": b.company_creation_date,
        "employee_range": b.employee_range,
        "enrichment_status": b.enrichment_status,
        "enrichment_details": b.enrichment_details,
        "contact_confidence": b.contact_confidence or 0,
        # CRM
        "crm_stage": b.crm_stage, "crm_notes": b.crm_notes,
        "next_contact_at": b.next_contact_at.isoformat() if b.next_contact_at else None,
        "priority": b.priority, "deal_value": b.deal_value or 0,
        "last_contacted_at": b.last_contacted_at.isoformat() if b.last_contacted_at else None,
        # Supervision
        "monitoring": b.monitoring,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
        "client_signed_at": b.client_signed_at.isoformat() if b.client_signed_at else None,
        "onboarding_status": b.onboarding_status,
        "onboarding_completeness": b.onboarding_completeness or 0,
    }


@app.post("/scan")
async def scan_local_businesses(lat: float, lng: float, background_tasks: BackgroundTasks, radius: int = 500, db: Session = Depends(get_db)):
    maps_service = GoogleMapsService()
    results = maps_service.search_nearby_businesses(lat, lng, radius)

    # Fallback to Apify when Google Maps API is unavailable or returns an error
    using_apify = False
    if isinstance(results, dict) and "error" in results:
        apify_service = ApifyMapsService()
        if apify_service._available():
            print(f"⚡ Fallback Apify Maps (raison: {results['error']})")
            results = apify_service.search_nearby_businesses(lat, lng, radius)
            using_apify = True
        if isinstance(results, dict) and "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])

    # Place Details used to be fetched sequentially (up to 20 HTTP calls),
    # which could make the scan look broken on mobile. Fetch them concurrently
    # and keep a fast fallback when a detail request fails.
    details_by_id = {}
    if not using_apify and isinstance(results, list) and results:
        async def _fetch_place_details(place):
            place_id = (place or {}).get("place_id")
            if not place_id:
                return None, {}
            try:
                details = await asyncio.wait_for(
                    asyncio.to_thread(maps_service.get_business_details, place_id),
                    timeout=10,
                )
                if not isinstance(details, dict) or "error" in details:
                    details = {}
                return place_id, details
            except Exception as exc:
                print(f"Place Details {place_id} skipped: {exc}")
                return place_id, {}

        detail_rows = await asyncio.gather(
            *[_fetch_place_details(place) for place in results[:20]],
            return_exceptions=False,
        )
        details_by_id = {pid: data for pid, data in detail_rows if pid}

    businesses = []
    skipped_invalid = 0
    for place in results:
        if not isinstance(place, dict):
            skipped_invalid += 1
            continue

        place_id = place.get("place_id")
        if not place_id:
            skipped_invalid += 1
            continue

        # For Apify results, website is already in the place dict; skip a second API call
        if using_apify:
            details = {"website": place.get("website", ""), "types": place.get("types", [])}
        else:
            details = details_by_id.get(place_id, {})

        photos_list = details.get("photos") or []
        score_data = {
            "website": details.get("website") or place.get("website"),
            "rating": place.get("rating", 0),
            "user_ratings_total": place.get("user_ratings_total", 0),
            "photos": photos_list,
            "category": details.get("types") or place.get("types") or place.get("category") or [],
            "address": place.get("vicinity") or details.get("formatted_address") or "",
            "business_phone": details.get("formatted_phone_number") or place.get("phone") or place.get("phoneUnformatted"),
        }
        scores = calculate_scores(score_data)
        potential = round(scores["digital_health"]["score"] / 10.0, 1)
        breakdown = scores["digital_health"]
        opportunity = scores["opportunity"]

        location = (place.get("geometry") or {}).get("location") or {}
        lat_val = location.get("lat")
        lng_val = location.get("lng")
        if lat_val is None or lng_val is None:
            skipped_invalid += 1
            continue

        b = db.query(Business).filter(Business.id == place_id).first()
        if not b:
            b = Business(
                id=place_id, name=place.get("name") or "Commerce",
                address=place.get("vicinity"),
                latitude=lat_val, longitude=lng_val,
                rating=place.get("rating"), user_ratings_total=place.get("user_ratings_total"),
                website=details.get("website") or place.get("website"),
                business_phone=score_data.get("business_phone"),
                photos=photos_list,
                category=score_data.get("category") or [],
                potential_score=potential,
                digital_health_score=scores["digital_health"]["score"],
                opportunity_score=opportunity["score"],
                opportunity_breakdown=opportunity,
            )
            db.add(b)
        else:
            b.potential_score = potential
            b.digital_health_score = scores["digital_health"]["score"]
            b.opportunity_score = opportunity["score"]
            b.opportunity_breakdown = opportunity
            b.website = details.get("website") or place.get("website") or b.website
            b.business_phone = score_data.get("business_phone") or b.business_phone
            b.photos = photos_list or b.photos
            b.category = score_data.get("category") or b.category
            b.latitude = lat_val
            b.longitude = lng_val

        # Recalcule depuis l'objet complet: conserve les coordonnées déjà enrichies.
        final_scores = _refresh_scores(b)
        breakdown = final_scores["digital_health"]
        opportunity = final_scores["opportunity"]

        businesses.append({"id": b.id, "name": b.name, "address": b.address,
                            "latitude": b.latitude, "longitude": b.longitude,
                            "rating": b.rating, "user_ratings_total": b.user_ratings_total,
                            "potential_score": b.potential_score,
                            "digital_health_score": b.digital_health_score,
                            "opportunity_score": b.opportunity_score,
                            "opportunity_label": opportunity.get("label"),
                            "opportunity_breakdown": opportunity,
                            "status": b.status, "website": b.website,
                            "business_phone": b.business_phone,
                            "score_breakdown": breakdown})
    db.commit()

    # Les prospects sont maintenant ordonnés par probabilité d'intérêt commercial.
    businesses.sort(key=lambda item: item.get("opportunity_score") or 0, reverse=True)

    # Audit automatique et non bloquant des meilleurs prospects ayant déjà un site.
    if os.getenv("AUTO_AUDIT_ENABLED", "true").lower() == "true":
        top_n = max(0, min(20, int(os.getenv("AUTO_AUDIT_TOP_N", "5"))))
        audit_ids = [x["id"] for x in businesses if x.get("website")][:top_n]
        if audit_ids:
            background_tasks.add_task(_background_audit_businesses, audit_ids)

    return {
        "count": len(businesses),
        "businesses": businesses,
        "source": "apify" if using_apify else "google",
        "skipped_invalid": skipped_invalid,
    }

@app.get("/businesses")
async def list_businesses(db: Session = Depends(get_db)):
    # Priorité commerciale décroissante. Les anciens enregistrements à score nul
    # restent compatibles grâce au recalcul dynamique de _biz_to_dict.
    rows = db.query(Business).order_by(Business.opportunity_score.desc(), Business.potential_score.asc()).all()
    payload = [_biz_to_dict(b) for b in rows]
    payload.sort(key=lambda item: item.get("opportunity_score") or 0, reverse=True)
    return payload

@app.get("/businesses/{business_id}")
async def get_business_detail(business_id: str, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        # Business may have been scanned by another Cloud Run instance (per-instance SQLite).
        # Reconstruct from Google Maps API for standard Places IDs.
        if not business_id.startswith("apify_") and len(business_id) > 10:
            try:
                maps_service = GoogleMapsService()
                details = maps_service.get_business_details(business_id)
                if isinstance(details, dict) and "error" not in details and details.get("name"):
                    loc = details.get("geometry", {}).get("location", {})
                    b = Business(
                        id=business_id,
                        name=details.get("name", "Commerce"),
                        address=details.get("formatted_address", ""),
                        latitude=loc.get("lat"),
                        longitude=loc.get("lng"),
                        rating=details.get("rating", 0.0),
                        user_ratings_total=details.get("user_ratings_total", 0),
                        website=details.get("website"),
                        business_phone=details.get("formatted_phone_number"),
                        category=details.get("types") or [],
                        status="scanned"
                    )
                    _refresh_scores(b)
                    db.add(b)
                    db.commit()
                    db.refresh(b)
                else:
                    raise HTTPException(status_code=404, detail="Not found")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(status_code=404, detail="Not found")
        else:
            raise HTTPException(status_code=404, detail="Not found")
    return _biz_to_dict(b)

@app.patch("/businesses/{business_id}")
async def update_business(business_id: str, data: dict, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b: raise HTTPException(status_code=404, detail="Not found")
    for key, value in data.items():
        if hasattr(b, key):
            setattr(b, key, value)
    db.commit()
    return _biz_to_dict(b)



@app.get("/businesses/{business_id}/onboarding")
async def get_business_onboarding(business_id: str, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b: raise HTTPException(status_code=404, detail="Not found")
    profile = b.client_profile if isinstance(b.client_profile, dict) else empty_profile(b)
    progress = onboarding_progress(profile, b.plan_tier or "starter")
    return {"business_id": b.id, "plan_tier": b.plan_tier, "profile": profile, "progress": progress, "status": b.onboarding_status}

@app.put("/businesses/{business_id}/onboarding")
async def update_business_onboarding(business_id: str, data: dict, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b: raise HTTPException(status_code=404, detail="Not found")
    profile = merge_profile(b, data.get("profile") or data, source=data.get("source") or "client_onboarding")
    b.client_profile = profile
    progress = onboarding_progress(profile, b.plan_tier or "starter")
    b.onboarding_completeness = progress["percent"]
    b.onboarding_status = "complete" if progress["complete"] else "in_progress"
    b.onboarding_updated_at = datetime.datetime.utcnow()
    db.commit()
    return {"profile": profile, "progress": progress, "status": b.onboarding_status}

@app.get("/client/onboarding/{token}")
async def public_onboarding(token: str, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.onboarding_token == token).first()
    if not b: raise HTTPException(status_code=404, detail="Lien d'onboarding invalide")
    profile = b.client_profile if isinstance(b.client_profile, dict) else empty_profile(b)
    return {"business_id": b.id, "business_name": b.name, "plan_tier": b.plan_tier, "profile": profile, "progress": onboarding_progress(profile, b.plan_tier or "starter")}

@app.put("/client/onboarding/{token}")
async def public_update_onboarding(token: str, data: dict, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.onboarding_token == token).first()
    if not b: raise HTTPException(status_code=404, detail="Lien d'onboarding invalide")
    profile = merge_profile(b, data.get("profile") or data, source="client_onboarding")
    b.client_profile = profile
    progress = onboarding_progress(profile, b.plan_tier or "starter")
    b.onboarding_completeness = progress["percent"]
    b.onboarding_status = "complete" if progress["complete"] else "in_progress"
    b.onboarding_updated_at = datetime.datetime.utcnow()
    db.commit()
    return {"profile": profile, "progress": progress, "status": b.onboarding_status}

def _audit_business_record(b: Business) -> dict:
    """Audit un prospect et recalcule immédiatement les deux scores."""
    if not b.website:
        report = audit_website("")
        b.website_audit = report
        b.website_audit_status = report.get("status", "no_website")
        _refresh_scores(b)
        return report

    report = audit_website(b.website)
    b.website_audit = report
    b.website_audit_status = report.get("status", "error")
    _refresh_scores(b)
    return report


def _background_audit_businesses(business_ids: list[str]):
    """Tâche post-scan: audite les meilleurs sites sans ralentir la carte."""
    from backend.models.database import SessionLocal
    local_db = SessionLocal()
    try:
        for bid in business_ids:
            b = local_db.query(Business).filter(Business.id == bid).first()
            if not b or not b.website:
                continue
            try:
                _audit_business_record(b)
                local_db.commit()
            except Exception as exc:
                print(f"Auto audit {bid} failed: {exc}")
                b.website_audit_status = "error"
                local_db.commit()
    finally:
        local_db.close()


@app.post("/businesses/{business_id}/audit-site")
async def audit_business_site(business_id: str, db: Session = Depends(get_db)):
    """Audit technique/SEO/conversion du site existant + recalcul Opportunity Score."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    report = await asyncio.to_thread(audit_website, b.website or "")
    b.website_audit = report
    b.website_audit_status = report.get("status", "error")
    _refresh_scores(b)
    db.commit()
    db.refresh(b)
    return {
        "id": b.id,
        "website_audit": report,
        "digital_health_score": b.digital_health_score,
        "opportunity_score": b.opportunity_score,
        "opportunity_breakdown": b.opportunity_breakdown,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ORCHESTRATION & DEPLOY
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/orchestrate/{business_id}")
async def start_orchestration(business_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if b and b.status == "processing":
        return {"status": "Already processing"}
    if b:
        b.status = "processing"
        db.commit()
    active_logs[business_id] = asyncio.Queue()

    async def run_orchestration_task(bid: str):
        from .models.database import SessionLocal
        new_db = SessionLocal()
        # Init polling buffer
        log_buffers[bid] = {"entries": [], "finished": False}
        try:
            biz = new_db.query(Business).filter(Business.id == bid).first()
            maps_service = GoogleMapsService()
            details = maps_service.get_business_details(bid)

            if not biz:
                biz = Business(id=bid, name=details.get("name", "Commerce"),
                               address=details.get("formatted_address", ""),
                               rating=details.get("rating", 0.0),
                               potential_score=calculate_potential_score(details), status="processing")
                new_db.add(biz)

            # Toujours rafraîchir photos/website/category, que le business soit
            # nouveau ou existant — sinon "types" reste vide au 1er passage et
            # _detect_sector() retombe systématiquement sur "generic".
            biz.photos = details.get("photos", [])
            biz.website = details.get("website")
            biz.business_phone = details.get("formatted_phone_number") or biz.business_phone
            biz.category = details.get("types", [])
            _refresh_scores(biz)
            new_db.commit()

            business_data = {
                "name": biz.name, "address": biz.address, "rating": biz.rating,
                "phone": details.get("formatted_phone_number", ""),
                "user_ratings_total": details.get("user_ratings_total", 0),
                "business_id": bid, "types": biz.category or [],
                "photos": biz.photos or [],
                "reviews": details.get("reviews", []),
                "website": details.get("website", ""),
            }
            manager = LocalPulseManager(business_data, log_queue=active_logs.get(bid))
            manager.log_buffer = log_buffers[bid]["entries"]  # attach polling buffer

            # Phase 0 — Design brief FIRST (before investigation)
            design_brief = await asyncio.to_thread(manager.run_design_crew)
            biz.site_config = design_brief
            new_db.commit()

            # Phase 1 — Investigation + Copywriting + Photos
            prep_result = await asyncio.to_thread(manager.run_prep_crew)
            biz.generated_copy = {k: prep_result.get(k, "") for k in ["report", "copywriting", "ai_photos", "design"]}
            new_db.commit()

            build_result = await asyncio.to_thread(manager.run_build_crew, prep_result)

            biz.generated_html = build_result.get("html", "")
            # Store JSON config if produced
            if build_result.get("site_config"):
                biz.site_config = build_result["site_config"]
            biz.generated_copy = {**biz.generated_copy, "email": build_result.get("email", "")}
            biz.status = "pending_validation"
            new_db.commit()

            if bid in active_logs:
                await active_logs[bid].put({"type": "chat", "agent": "Système",
                    "message": "✅ Site généré ! Onglet **Aperçu** pour valider avant déploiement."})
                await active_logs[bid].put({"type": "end"})
                del active_logs[bid]
            if bid in log_buffers:
                log_buffers[bid]["entries"].append({"type": "end", "agent": "Système",
                    "message": "✅ Site généré ! Onglet Aperçu pour valider."})
                log_buffers[bid]["finished"] = True
            if manager.redis_client:
                manager.redis_client.set(f"status:{bid}", "👀 En attente de validation...")

        except Exception as e:
            import traceback; traceback.print_exc()
            try:
                err_db = SessionLocal(); tbiz = err_db.query(Business).filter(Business.id == bid).first()
                if tbiz: tbiz.status = "error"; err_db.commit(); err_db.close()
            except Exception: pass
            if bid in active_logs:
                await active_logs[bid].put({"type": "error", "message": str(e)})
                await active_logs[bid].put({"type": "end"})
                del active_logs[bid]
            if bid in log_buffers:
                log_buffers[bid]["entries"].append({"type": "error", "message": str(e)})
                log_buffers[bid]["finished"] = True
        finally:
            new_db.close()

    background_tasks.add_task(run_orchestration_task, business_id)
    return {"status": "Processing Started"}

# ──────────────────────────────────────────────────────────────────────────────
# PARTIAL REGENERATION
# ──────────────────────────────────────────────────────────────────────────────

def _business_data_from_db(biz, details: dict) -> dict:
    public_base = (os.getenv("PUBLIC_BASE_URL") or os.getenv("FRONTEND_URL") or "https://pme-local-pulse.web.app").rstrip("/")
    bid = urllib.parse.quote(str(biz.id), safe="")
    return {
        "name": biz.name, "address": biz.address, "rating": biz.rating,
        "phone": details.get("formatted_phone_number", "") or biz.business_phone or "",
        "user_ratings_total": details.get("user_ratings_total", 0) or biz.user_ratings_total or 0,
        "business_id": biz.id, "types": biz.category or [],
        "photos": biz.photos or [],
        "reviews": details.get("reviews", []),
        "website": details.get("website", "") or biz.website or "",
        "potential_score": biz.potential_score or 0,
        "digital_health_score": biz.digital_health_score or 0,
        "opportunity_score": biz.opportunity_score or 0,
        "website_audit": biz.website_audit or {},
        "owner_first_name": biz.owner_first_name or "",
        "deployment_url": biz.deployment_url or "",
        "payment_links": {
            "starter": f"{public_base}/buy/{bid}/starter",
            "pro": f"{public_base}/buy/{bid}/pro",
            "elite": f"{public_base}/buy/{bid}/elite",
        },
        "plan_catalog": public_plan_catalog(),
        "client_profile": biz.client_profile if isinstance(biz.client_profile, dict) else empty_profile(biz),
        "onboarding_status": biz.onboarding_status,
        "onboarding_completeness": biz.onboarding_completeness or 0,
    }


@app.post("/businesses/{business_id}/regenerate/email")
async def regenerate_email(business_id: str, db: Session = Depends(get_db)):
    """Synchronous: regenerates only the email and returns it immediately."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")

    copy_data = b.generated_copy or {}
    if isinstance(copy_data, str):
        try: copy_data = json.loads(copy_data)
        except: copy_data = {}

    maps_service = GoogleMapsService()
    details = maps_service.get_business_details(business_id)
    if isinstance(details, dict) and "error" in details:
        details = {}

    business_data = _business_data_from_db(b, details)
    manager = LocalPulseManager(business_data)

    prep_data = {
        "report": copy_data.get("report", ""),
        "copywriting": copy_data.get("copywriting", ""),
    }
    email_text = await asyncio.to_thread(manager.run_email_only, prep_data)

    copy_data["email"] = email_text
    b.generated_copy = copy_data
    db.commit()
    return {"email": email_text}


@app.post("/businesses/{business_id}/regenerate/site")
async def regenerate_site(business_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Background: rebuilds HTML from existing prep_data (keeps analysis/copy)."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    if b.status == "processing":
        return {"status": "Already processing"}

    prev_status = b.status
    b.status = "processing"
    db.commit()
    active_logs[business_id] = asyncio.Queue()

    async def _regen_site(bid: str, old_status: str):
        from .models.database import SessionLocal
        new_db = SessionLocal()
        log_buffers[bid] = {"entries": [], "finished": False}
        try:
            biz = new_db.query(Business).filter(Business.id == bid).first()
            copy_data = biz.generated_copy or {}
            if isinstance(copy_data, str):
                try: copy_data = json.loads(copy_data)
                except: copy_data = {}

            maps_service = GoogleMapsService()
            details = maps_service.get_business_details(bid)
            if isinstance(details, dict) and "error" in details:
                details = {}

            biz.photos   = details.get("photos", []) or biz.photos
            biz.website  = details.get("website") or biz.website
            biz.category = details.get("types", []) or biz.category
            new_db.commit()

            business_data = _business_data_from_db(biz, details)
            manager = LocalPulseManager(business_data, log_queue=active_logs.get(bid))
            manager.log_buffer = log_buffers[bid]["entries"]

            if biz.site_config:
                design = biz.site_config if isinstance(biz.site_config, dict) else json.loads(biz.site_config)
                manager.design_brief = design

            prep_data = {
                "report": copy_data.get("report", ""),
                "copywriting": copy_data.get("copywriting", ""),
                "ai_photos": copy_data.get("ai_photos", ""),
                "design": copy_data.get("design", ""),
            }

            build_result = await asyncio.to_thread(manager.run_build_crew, prep_data)
            biz.generated_html = build_result.get("html", "")
            biz.generated_copy = {**copy_data, "email": build_result.get("email", copy_data.get("email", ""))}
            biz.status = "pending_validation"
            new_db.commit()

            msg = "✅ Site régénéré ! Onglet **Aperçu** pour valider."
            if bid in active_logs:
                await active_logs[bid].put({"type": "chat", "agent": "Système", "message": msg})
                await active_logs[bid].put({"type": "end"})
                del active_logs[bid]
            if bid in log_buffers:
                log_buffers[bid]["entries"].append({"type": "end", "agent": "Système", "message": msg})
                log_buffers[bid]["finished"] = True
        except Exception as e:
            import traceback; traceback.print_exc()
            try:
                err_db = SessionLocal()
                tbiz = err_db.query(Business).filter(Business.id == bid).first()
                if tbiz: tbiz.status = old_status; err_db.commit(); err_db.close()
            except Exception: pass
            if bid in active_logs:
                await active_logs[bid].put({"type": "error", "message": str(e)})
                await active_logs[bid].put({"type": "end"})
                del active_logs[bid]
            if bid in log_buffers:
                log_buffers[bid]["entries"].append({"type": "error", "message": str(e)})
                log_buffers[bid]["finished"] = True
        finally:
            new_db.close()

    background_tasks.add_task(_regen_site, business_id, prev_status)
    return {"status": "started"}


@app.post("/businesses/{business_id}/regenerate/copy")
async def regenerate_copy(business_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Background: re-runs the analysis + copywriting phase only."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    if b.status == "processing":
        return {"status": "Already processing"}

    prev_status = b.status
    b.status = "processing"
    db.commit()
    active_logs[business_id] = asyncio.Queue()

    async def _regen_copy(bid: str, old_status: str):
        from .models.database import SessionLocal
        new_db = SessionLocal()
        log_buffers[bid] = {"entries": [], "finished": False}
        try:
            biz = new_db.query(Business).filter(Business.id == bid).first()
            maps_service = GoogleMapsService()
            details = maps_service.get_business_details(bid)
            if isinstance(details, dict) and "error" in details:
                details = {}

            biz.photos   = details.get("photos", []) or biz.photos
            biz.website  = details.get("website") or biz.website
            biz.category = details.get("types", []) or biz.category
            new_db.commit()

            business_data = _business_data_from_db(biz, details)
            manager = LocalPulseManager(business_data, log_queue=active_logs.get(bid))
            manager.log_buffer = log_buffers[bid]["entries"]

            prep_result = await asyncio.to_thread(manager.run_prep_crew)

            old_copy = biz.generated_copy or {}
            if isinstance(old_copy, str):
                try: old_copy = json.loads(old_copy)
                except: old_copy = {}

            biz.generated_copy = {
                **old_copy,
                "report": prep_result.get("report", ""),
                "copywriting": prep_result.get("copywriting", ""),
                "design": prep_result.get("design", old_copy.get("design", "")),
            }
            biz.status = old_status
            new_db.commit()

            msg = "✅ Analyse & copy régénérés !"
            if bid in active_logs:
                await active_logs[bid].put({"type": "chat", "agent": "Système", "message": msg})
                await active_logs[bid].put({"type": "end"})
                del active_logs[bid]
            if bid in log_buffers:
                log_buffers[bid]["entries"].append({"type": "end", "agent": "Système", "message": msg})
                log_buffers[bid]["finished"] = True
        except Exception as e:
            import traceback; traceback.print_exc()
            try:
                err_db = SessionLocal()
                tbiz = err_db.query(Business).filter(Business.id == bid).first()
                if tbiz: tbiz.status = old_status; err_db.commit(); err_db.close()
            except Exception: pass
            if bid in active_logs:
                await active_logs[bid].put({"type": "error", "message": str(e)})
                await active_logs[bid].put({"type": "end"})
                del active_logs[bid]
            if bid in log_buffers:
                log_buffers[bid]["entries"].append({"type": "error", "message": str(e)})
                log_buffers[bid]["finished"] = True
        finally:
            new_db.close()

    background_tasks.add_task(_regen_copy, business_id, prev_status)
    return {"status": "started"}


@app.post("/deploy/{business_id}")
async def deploy_business(business_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not (os.getenv("VERCEL_API_TOKEN") or "").strip():
        raise HTTPException(
            status_code=503,
            detail="Déploiement Vercel indisponible : VERCEL_API_TOKEN absent du backend."
        )
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b: raise HTTPException(status_code=404, detail="Not found")
    if not b.generated_html: raise HTTPException(status_code=400, detail="No HTML yet")
    if b.status == "completed": return {"status": "Already deployed", "url": b.deployment_url}
    b.status = "processing"; db.commit()

    async def do_deploy(bid: str):
        from .models.database import SessionLocal
        new_db = SessionLocal()
        try:
            biz = new_db.query(Business).filter(Business.id == bid).first()
            if bid not in active_logs: active_logs[bid] = asyncio.Queue()
            manager = LocalPulseManager({"name": biz.name, "address": biz.address or "",
                                         "rating": biz.rating or 0, "business_id": bid},
                                        log_queue=active_logs.get(bid))
            manager._push_log("L'Ingénieur", f"🚀 Déploiement de **{biz.name}** sur Vercel...", "chat")
            result = await asyncio.to_thread(manager.run_deploy_crew, biz.generated_html)
            m = re.search(r'https://[a-zA-Z0-9._\-]+\.vercel\.app', result)
            if not m:
                raise RuntimeError(f"Vercel n'a retourné aucune URL exploitable : {str(result)[:300]}")
            biz.deployment_url = m.group(0)
            biz.status = "completed"
            new_db.commit()

            # Final sales email is generated only after the Vercel URL exists,
            # so the prospect receives a real preview link + direct checkout CTAs.
            try:
                copy_data = biz.generated_copy or {}
                if isinstance(copy_data, str):
                    try:
                        copy_data = json.loads(copy_data)
                    except Exception:
                        copy_data = {}
                maps_service = GoogleMapsService()
                details = maps_service.get_business_details(bid)
                if isinstance(details, dict) and "error" in details:
                    details = {}
                business_data = _business_data_from_db(biz, details)
                email_manager = LocalPulseManager(business_data)
                final_email = await asyncio.to_thread(
                    email_manager.run_email_only,
                    {
                        "report": copy_data.get("report", ""),
                        "copywriting": copy_data.get("copywriting", ""),
                    },
                )
                copy_data["email"] = final_email
                biz.generated_copy = copy_data
                new_db.commit()
                manager._push_log(
                    "Le Closer",
                    "✅ Email final mis à jour avec preview Vercel + liens Stripe.",
                    "chat",
                )
            except Exception as email_exc:
                manager._push_log(
                    "Le Closer",
                    f"⚠️ Site déployé, mais email final non régénéré : {email_exc}",
                    "system",
                )

            if bid in active_logs:
                await active_logs[bid].put({"type": "chat", "agent": "L'Ingénieur",
                                             "message": f"✅ Déployé ! {biz.deployment_url}"})
                await active_logs[bid].put({"type": "end"})
                del active_logs[bid]
        except Exception as e:
            try:
                err_db = SessionLocal(); tbiz = err_db.query(Business).filter(Business.id == bid).first()
                if tbiz: tbiz.status = "error"; err_db.commit(); err_db.close()
            except Exception: pass
            if bid in active_logs:
                await active_logs[bid].put({"type": "error", "message": str(e)})
                await active_logs[bid].put({"type": "end"})
                del active_logs[bid]
        finally: new_db.close()

    background_tasks.add_task(do_deploy, business_id)
    return {"status": "Deployment started"}



# ──────────────────────────────────────────────────────────────────────────────
# AGENT TEAMS V1 — declarative, installable from Git manifests
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/agent-teams")
async def list_agent_teams(business_id: str = None, db: Session = Depends(get_db)):
    rows = db.query(AgentTeam).order_by(AgentTeam.category, AgentTeam.name).all()
    assigned = set(_business_team_slugs(db, business_id)) if business_id else set()
    payload = []
    for row in rows:
        item = _agent_team_to_dict(row)
        item["assigned"] = row.slug in assigned if business_id else None
        payload.append(item)
    return payload


@app.post("/agent-teams/install")
async def install_agent_team(data: dict, db: Session = Depends(get_db)):
    repo_url = str(data.get("repo_url") or "").strip()
    manifest_path = str(data.get("manifest_path") or "team.yaml").strip()
    ref = str(data.get("ref") or "main").strip()
    if not repo_url:
        raise HTTPException(status_code=400, detail="repo_url requis.")
    try:
        manifest = await asyncio.to_thread(fetch_git_manifest, repo_url, manifest_path, ref)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Installation refusée : {exc}")

    row = db.query(AgentTeam).filter(AgentTeam.slug == manifest["slug"]).first()
    if row and row.source_type == "builtin":
        raise HTTPException(status_code=409, detail="Ce slug est réservé à une équipe intégrée.")
    if row is None:
        row = AgentTeam(
            slug=manifest["slug"],
            name=manifest["name"],
            description=manifest.get("description"),
            category=manifest.get("category", "general"),
            source_type="git",
            source_url=repo_url,
            manifest=manifest,
            enabled=True,
            version=manifest.get("version", "1"),
        )
        db.add(row)
    else:
        row.name = manifest["name"]
        row.description = manifest.get("description")
        row.category = manifest.get("category", "general")
        row.source_url = repo_url
        row.manifest = manifest
        row.enabled = True
        row.version = manifest.get("version", "1")
    db.commit()
    db.refresh(row)
    return _agent_team_to_dict(row)


@app.patch("/agent-teams/{team_slug}")
async def update_agent_team(team_slug: str, data: dict, db: Session = Depends(get_db)):
    row = db.query(AgentTeam).filter(AgentTeam.slug == team_slug).first()
    if not row:
        raise HTTPException(status_code=404, detail="Équipe introuvable.")
    if "enabled" in data:
        row.enabled = bool(data["enabled"])
    db.commit()
    return _agent_team_to_dict(row)


@app.delete("/agent-teams/{team_slug}")
async def delete_agent_team(team_slug: str, db: Session = Depends(get_db)):
    row = db.query(AgentTeam).filter(AgentTeam.slug == team_slug).first()
    if not row:
        raise HTTPException(status_code=404, detail="Équipe introuvable.")
    if row.source_type == "builtin":
        raise HTTPException(status_code=400, detail="Une équipe intégrée peut être désactivée mais pas supprimée.")
    db.query(BusinessAgentTeam).filter(BusinessAgentTeam.team_slug == team_slug).delete()
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


@app.post("/agent-teams/{team_slug}/assign/{business_id}")
async def assign_agent_team(team_slug: str, business_id: str, data: dict = None, db: Session = Depends(get_db)):
    team = db.query(AgentTeam).filter(AgentTeam.slug == team_slug).first()
    business = db.query(Business).filter(Business.id == business_id).first()
    if not team or not business:
        raise HTTPException(status_code=404, detail="Équipe ou commerce introuvable.")
    enabled = True if data is None else bool(data.get("enabled", True))
    row = db.query(BusinessAgentTeam).filter(
        BusinessAgentTeam.business_id == business_id,
        BusinessAgentTeam.team_slug == team_slug,
    ).first()
    if row is None:
        row = BusinessAgentTeam(
            business_id=business_id,
            team_slug=team_slug,
            enabled=enabled,
            source="manual",
        )
        db.add(row)
    else:
        row.enabled = enabled
        row.source = "manual"
    db.commit()
    return {"business_id": business_id, "team_slug": team_slug, "enabled": enabled}


@app.get("/agent-teams/runs")
async def list_agent_team_runs(limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(200, limit))
    rows = db.query(AgentTeamRun).order_by(AgentTeamRun.id.desc()).limit(limit).all()
    return [{
        "id": r.id,
        "team_slug": r.team_slug,
        "business_id": r.business_id,
        "status": r.status,
        "trigger": r.trigger,
        "outputs": r.outputs,
        "logs": r.logs,
        "error": r.error,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    } for r in rows]


@app.post("/agent-teams/{team_slug}/run")
async def run_agent_team(team_slug: str, business_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    team = db.query(AgentTeam).filter(AgentTeam.slug == team_slug).first()
    business = db.query(Business).filter(Business.id == business_id).first()
    if not team or not team.enabled:
        raise HTTPException(status_code=404, detail="Équipe introuvable ou désactivée.")
    if not business:
        raise HTTPException(status_code=404, detail="Commerce introuvable.")

    readiness = agent_team_readiness(business, team_slug)
    if business.subscription_status == "active" and not readiness["ready"]:
        missing = ", ".join(item["label"] for item in readiness["missing"])
        raise HTTPException(
            status_code=409,
            detail=f"Onboarding incomplet pour {team.name} : {missing}",
        )

    run = AgentTeamRun(
        team_slug=team_slug,
        business_id=business_id,
        status="queued",
        trigger="manual",
        outputs={},
        logs=[],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    run_id = run.id

    async def _execute_team(rid: int):
        from backend.models.database import SessionLocal
        local_db = SessionLocal()
        try:
            run_row = local_db.query(AgentTeamRun).filter(AgentTeamRun.id == rid).first()
            team_row = local_db.query(AgentTeam).filter(AgentTeam.slug == team_slug).first()
            biz = local_db.query(Business).filter(Business.id == business_id).first()
            if not run_row or not team_row or not biz:
                return

            run_row.status = "running"
            run_row.started_at = datetime.datetime.utcnow()
            local_db.commit()

            manifest = validate_manifest(dict(team_row.manifest or {}))
            context = agent_business_context(biz)
            manager = LocalPulseManager(context)
            outputs = {}
            logs = []
            agents = manifest["agents"]
            total_agents = len(agents)

            for index, agent in enumerate(agents, start=1):
                agent_id = agent["id"]
                output_key = agent.get("output_key") or agent_id
                next_agent = agents[index].get("name", agents[index]["id"]) if index < total_agents else "aucun"

                tool_results = {}
                for tool_name in agent.get("tools", []):
                    tool_results[tool_name] = await asyncio.to_thread(run_safe_tool, tool_name, biz)

                system_prompt = build_system_prompt(
                    team=manifest["name"],
                    agent_name=agent.get("name", agent_id),
                    role=agent.get("role", ""),
                    business_name=biz.name or "Commerce",
                    index=index,
                    total=total_agents,
                    next_agent=next_agent,
                    business_data=context,
                    tool_results=tool_results,
                    previous_results=outputs,
                    mission=agent["prompt"],
                )
                temperature = float(agent.get("temperature", 0.1))
                prompt_version = agent.get("prompt_version", f"{agent_id}@v1")

                log_entry = {
                    "agent": agent_id,
                    "name": agent.get("name", agent_id),
                    "status": "running",
                    "step": index,
                    "prompt_version": prompt_version,
                    "temperature": temperature,
                    "validation_retry": False,
                }
                logs.append(log_entry)
                run_row.logs = logs
                local_db.commit()

                raw = await asyncio.to_thread(
                    manager._call,
                    "Exécute ta mission et retourne uniquement le JSON demandé.",
                    3200,
                    system_prompt,
                    temperature,
                )

                try:
                    envelope = validate_agent_output(agent_id, raw)
                except Exception as validation_exc:
                    log_entry["validation_retry"] = True
                    repair = repair_prompt(agent_id, str(validation_exc), raw)
                    raw = await asyncio.to_thread(
                        manager._call,
                        repair,
                        3200,
                        system_prompt,
                        0.1,
                    )
                    envelope = validate_agent_output(agent_id, raw)

                # V2: only the structured resultat is forwarded to following agents.
                outputs[output_key] = envelope.resultat
                log_entry["status"] = "completed"
                log_entry["envelope_status"] = envelope.statut
                log_entry["confidence"] = envelope.confiance
                log_entry["missing_data"] = envelope.donnees_manquantes
                log_entry["alerts"] = envelope.alertes
                log_entry["preview"] = json.dumps(envelope.resultat, ensure_ascii=False, default=str)[:500]

                run_row.outputs = outputs
                run_row.logs = logs
                local_db.commit()

                # Stop early instead of letting downstream agents work on blocking gaps.
                if envelope.statut == "incomplet":
                    run_row.status = "incomplete"
                    run_row.error = "Données bloquantes manquantes : " + "; ".join(envelope.donnees_manquantes[:20])
                    run_row.finished_at = datetime.datetime.utcnow()
                    local_db.commit()
                    return

            run_row.status = "completed"
            run_row.outputs = outputs
            run_row.logs = logs
            run_row.finished_at = datetime.datetime.utcnow()
            local_db.commit()
        except Exception as exc:
            try:
                run_row = local_db.query(AgentTeamRun).filter(AgentTeamRun.id == rid).first()
                if run_row:
                    run_row.status = "error"
                    run_row.error = str(exc)[:2000]
                    run_row.finished_at = datetime.datetime.utcnow()
                    local_db.commit()
            except Exception:
                pass
        finally:
            local_db.close()

    background_tasks.add_task(_execute_team, run_id)
    return {"status": "queued", "run_id": run_id, "team_slug": team_slug, "business_id": business_id}


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN — KPIs
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/admin/kpis")
async def get_kpis(db: Session = Depends(get_db)):
    all_biz = db.query(Business).all()
    plans   = db.query(Plan).filter(Plan.is_active == True).all()
    plan_prices = {p.slug: p.price for p in plans}

    active_clients  = [b for b in all_biz if b.subscription_status == "active"]
    deployed        = [b for b in all_biz if b.status == "completed"]
    pipeline        = [b for b in all_biz if b.status in ("processing", "pending_validation")]
    total_scanned   = len(all_biz)

    mrr = sum(b.mrr_value or 0 for b in active_clients)
    arr = mrr * 12

    tier_breakdown = {}
    for slug in ["free", "starter", "pro", "elite"]:
        tier_breakdown[slug] = len([b for b in active_clients if b.plan_tier == slug])

    avg_plan = sum(plan_prices.values()) / len(plan_prices) if plan_prices else 99
    ltv  = round(avg_plan * 18, 2)
    cac  = 45.0
    churn_rate = 3.2  # simulated

    return {
        "mrr": round(mrr, 2),
        "arr": round(arr, 2),
        "mrr_growth_pct": 12.5,
        "total_active_clients": len(active_clients),
        "total_scanned": total_scanned,
        "sites_deployed": len(deployed),
        "sites_pipeline": len(pipeline),
        "churn_rate": churn_rate,
        "ltv": ltv,
        "cac": cac,
        "ltv_cac_ratio": round(ltv / cac, 1) if cac else 0,
        "tier_breakdown": tier_breakdown,
        "status_breakdown": {
            "scanned": len([b for b in all_biz if b.status == "scanned"]),
            "processing": len([b for b in all_biz if b.status == "processing"]),
            "pending_validation": len([b for b in all_biz if b.status == "pending_validation"]),
            "completed": len([b for b in all_biz if b.status == "completed"]),
            "error": len([b for b in all_biz if b.status == "error"]),
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN — PLANS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/admin/plans")
async def list_plans(db: Session = Depends(get_db)):
    return db.query(Plan).order_by(Plan.sort_order).all()

@app.post("/admin/plans")
async def create_plan(data: dict, db: Session = Depends(get_db)):
    plan = Plan(**data)
    db.add(plan); db.commit(); db.refresh(plan)
    return plan

@app.put("/admin/plans/{plan_id}")
async def update_plan(plan_id: int, data: dict, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan: raise HTTPException(status_code=404, detail="Plan not found")
    for k, v in data.items():
        if hasattr(plan, k): setattr(plan, k, v)
    db.commit(); return plan

@app.delete("/admin/plans/{plan_id}")
async def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan: raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan); db.commit()
    return {"status": "deleted"}


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN — DESIGN PRESETS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/admin/design-presets")
async def list_design_presets(db: Session = Depends(get_db)):
    return db.query(DesignPreset).order_by(DesignPreset.id).all()

@app.post("/admin/design-presets")
async def create_design_preset(data: dict, db: Session = Depends(get_db)):
    preset = DesignPreset(**data)
    db.add(preset); db.commit(); db.refresh(preset)
    return preset

@app.put("/admin/design-presets/{preset_id}")
async def update_design_preset(preset_id: int, data: dict, db: Session = Depends(get_db)):
    preset = db.query(DesignPreset).filter(DesignPreset.id == preset_id).first()
    if not preset: raise HTTPException(status_code=404, detail="Preset not found")
    for k, v in data.items():
        if hasattr(preset, k): setattr(preset, k, v)
    db.commit(); return preset

@app.delete("/admin/design-presets/{preset_id}")
async def delete_design_preset(preset_id: int, db: Session = Depends(get_db)):
    preset = db.query(DesignPreset).filter(DesignPreset.id == preset_id).first()
    if not preset: raise HTTPException(status_code=404, detail="Not found")
    db.delete(preset); db.commit()
    return {"status": "deleted"}


# ──────────────────────────────────────────────────────────────────────────────
# STRIPE — SUBSCRIPTIONS
# ──────────────────────────────────────────────────────────────────────────────

PLAN_PRICES = {slug: int(plan["price"] * 100) for slug, plan in PLAN_CATALOG.items()}
PLAN_MRR = {slug: float(plan["price"]) for slug, plan in PLAN_CATALOG.items()}


def _create_stripe_checkout(business: Business, plan: str):
    import stripe as _stripe

    secret = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Paiement temporairement indisponible : STRIPE_SECRET_KEY absent du backend."
        )
    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Plan invalide : {plan}")

    _stripe.api_key = secret
    frontend_url = (os.environ.get("FRONTEND_URL") or "https://pme-local-pulse.web.app").rstrip("/")
    preview_url = business.deployment_url or f"{frontend_url}/demo/{urllib.parse.quote(str(business.id), safe='')}"
    onboarding_token = ensure_token(business)

    plan_info = PLAN_CATALOG[plan]
    included_preview = " · ".join(plan_info["features"][:4])
    session = _stripe.checkout.Session.create(
        mode="subscription",
        client_reference_id=str(business.id),
        line_items=[{
            "price_data": {
                "currency": plan_info["currency"],
                "unit_amount": PLAN_PRICES[plan],
                "recurring": {"interval": "month"},
                "product_data": {
                    "name": f"Local-Pulse {plan_info['name']} — {plan_info['positioning']}",
                    "description": included_preview[:450],
                },
            },
            "quantity": 1,
        }],
        metadata={"business_id": str(business.id), "plan": plan},
        subscription_data={"metadata": {"business_id": str(business.id), "plan": plan}},
        success_url=f"{frontend_url}/app/?payment=success&plan={plan}&onboarding={onboarding_token}",
        cancel_url=preview_url,
    )
    return session


@app.post("/create-checkout-session")
async def create_checkout_session(business_id: str, plan: str, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")
    ensure_token(b)
    db.commit()
    session = await asyncio.to_thread(_create_stripe_checkout, b, plan)
    return {"checkout_url": session.url}


@app.get("/buy/{business_id}/{plan}")
async def buy_plan(business_id: str, plan: str, db: Session = Depends(get_db)):
    """Public email CTA: create a secure Stripe Checkout and redirect the prospect."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")
    ensure_token(b)
    db.commit()
    session = await asyncio.to_thread(_create_stripe_checkout, b, plan)
    if not session.url:
        raise HTTPException(status_code=502, detail="Stripe n'a retourné aucune URL de paiement.")
    return RedirectResponse(url=session.url, status_code=303)


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    import stripe as _stripe
    _stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = _stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except _stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {})
        business_id = meta.get("business_id")
        plan = meta.get("plan")
        if business_id and plan:
            b = db.query(Business).filter(Business.id == business_id).first()
            if b and plan in PLAN_CATALOG:
                apply_plan_features(b, plan)
                b.subscription_status = "active"
                b.client_signed_at = datetime.datetime.utcnow()
                ensure_token(b)
                if not isinstance(b.client_profile, dict):
                    b.client_profile = empty_profile(b)
                progress = onboarding_progress(b.client_profile, plan)
                b.onboarding_completeness = progress["percent"]
                b.onboarding_status = "complete" if progress["complete"] else "in_progress"
                b.onboarding_updated_at = datetime.datetime.utcnow()
                _sync_business_agent_teams(db, b, plan)
                db.commit()

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        customer_id = sub.get("customer")
        # Try to match by stripe_customer_id if column exists, otherwise use metadata
        meta = sub.get("metadata", {})
        business_id = meta.get("business_id")
        b = None
        if business_id:
            b = db.query(Business).filter(Business.id == business_id).first()
        if b:
            b.subscription_status = "cancelled"
            db.commit()

    return {"status": "ok"}


@app.get("/demo/{business_id}")
async def demo_page(business_id: str, db: Session = Depends(get_db)):
    """Public demo page that wraps the generated site in a branded iframe."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")

    plan_prices = {slug: plan["price"] for slug, plan in PLAN_CATALOG.items()}
    cta_price = plan_prices.get(b.plan_tier, PLAN_CATALOG["starter"]["price"]) if b.plan_tier != "free" else PLAN_CATALOG["starter"]["price"]

    if not b.generated_html:
        content = """<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Démo Local-Pulse</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background:#0f172a; color:#e2e8f0; display:flex; align-items:center;
         justify-content:center; height:100vh; flex-direction:column; gap:16px; }
  p { font-size:1.1rem; color:#94a3b8; }
</style>
</head>
<body>
  <div style="font-size:3rem">⏳</div>
  <p>Le site de <strong style="color:#e2e8f0">{name}</strong> est en cours de génération.</p>
  <p style="font-size:.875rem">Revenez dans quelques instants.</p>
</body>
</html>""".format(name=b.name)
        return HTMLResponse(content=content)

    html = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Démo – {name} · Local-Pulse</title>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; overflow:hidden; background:#0f172a; }}

    /* Top banner */
    .banner {{
      position:fixed; top:0; left:0; right:0; z-index:9999;
      background:linear-gradient(135deg,#4f46e5,#7c3aed);
      color:#fff; padding:10px 20px;
      display:flex; align-items:center; justify-content:center; gap:8px;
      font-size:.85rem; font-weight:600; letter-spacing:.01em;
      box-shadow:0 2px 16px rgba(79,70,229,.4);
    }}
    .banner span {{ opacity:.85; }}

    /* Iframe */
    iframe {{
      position:fixed; top:42px; left:0; right:0; bottom:0;
      width:100%; height:calc(100vh - 42px); border:none;
    }}

    /* CTA button */
    .cta {{
      position:fixed; bottom:24px; right:24px; z-index:9999;
      background:linear-gradient(135deg,#4f46e5,#7c3aed);
      color:#fff; padding:14px 22px; border-radius:14px;
      font-size:.9rem; font-weight:700; text-decoration:none;
      box-shadow:0 8px 24px rgba(79,70,229,.5);
      display:flex; align-items:center; gap:8px;
      transition:transform .15s, box-shadow .15s;
    }}
    .cta:hover {{ transform:translateY(-2px); box-shadow:0 12px 32px rgba(79,70,229,.6); }}
    .cta .arrow {{ font-size:1.1rem; }}
  </style>
</head>
<body>
  <div class="banner">
    ✨ <span>Site démo créé par <strong>Local-Pulse</strong> pour {name}</span>
  </div>

  <iframe src="/preview/{business_id}" title="Aperçu du site de {name}"></iframe>

  <a href="/pricing?business_id={business_id}" class="cta">
    Obtenir ce site <span class="arrow">→</span> {price}€/mois
  </a>
</body>
</html>""".format(name=b.name, business_id=business_id, price=cta_price)

    return HTMLResponse(content=html)


@app.get("/pricing-page")
async def pricing_page(business_id: str = None, db: Session = Depends(get_db)):
    """Public commercial catalog. Single source of truth for plan content."""
    business = None
    if business_id:
        b = db.query(Business).filter(Business.id == business_id).first()
        if b:
            business = {
                "id": b.id,
                "name": b.name,
                "plan_tier": b.plan_tier,
                "subscription_status": b.subscription_status,
            }
    return {"plans": public_plan_catalog(), "business": business}


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN — PER-CLIENT MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/admin/clients")
async def list_clients(db: Session = Depends(get_db)):
    """Return all businesses with SaaS subscription data for admin CRM."""
    return [_biz_to_dict(b) for b in db.query(Business).order_by(Business.updated_at.desc()).all()]

@app.patch("/admin/clients/{business_id}")
async def update_client_subscription(business_id: str, data: dict, db: Session = Depends(get_db)):
    """Update plan tier, feature flags, domain for a specific client."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b: raise HTTPException(status_code=404, detail="Not found")

    ALLOWED = {
        "plan_tier", "subscription_status", "mrr_value", "client_signed_at",
        "custom_domain", "domain_ssl_active",
        "features_booking_active", "features_menu_active",
        "features_click_collect_active", "features_chatbot_active",
        "features_seo_blog_active", "features_gmb_reviews_sync",
        "features_multilang_active",
        "seo_score", "keywords_tracked"
    }
    for k, v in data.items():
        if k in ALLOWED: setattr(b, k, v)

    # Auto-set mrr_value from Plan table price (not hardcoded)
    if "plan_tier" in data and "mrr_value" not in data:
        plan = db.query(Plan).filter(Plan.slug == data["plan_tier"]).first()
        b.mrr_value = plan.price if plan else 0

    db.commit()
    return _biz_to_dict(b)


# ──────────────────────────────────────────────────────────────────────────────
# CRM
# ──────────────────────────────────────────────────────────────────────────────

def _crm_dict(b: Business) -> dict:
    scores = calculate_scores(_business_score_input(b), b.website_audit)
    opportunity_breakdown = b.opportunity_breakdown or scores["opportunity"]
    return {
        "id": b.id,
        "name": b.name,
        "address": b.address,
        "website": b.website,
        "business_phone": b.business_phone,
        "potential_score": round(float(b.digital_health_score or scores["digital_health"]["score"]) / 10.0, 1),
        "digital_health_score": float(b.digital_health_score or scores["digital_health"]["score"]),
        "opportunity_score": float(b.opportunity_score or scores["opportunity"]["score"]),
        "opportunity_label": opportunity_breakdown.get("label") if isinstance(opportunity_breakdown, dict) else None,
        "opportunity_breakdown": opportunity_breakdown,
        "website_audit": b.website_audit,
        "website_audit_status": b.website_audit_status,
        "rating": b.rating,
        "user_ratings_total": b.user_ratings_total,
        "category": b.category,
        "status": b.status,
        "email_status": b.email_status,
        "subscription_status": b.subscription_status,
        "plan_tier": b.plan_tier,
        "mrr_value": b.mrr_value,
        "crm_stage": b.crm_stage or "prospect",
        "crm_notes": b.crm_notes,
        "next_contact_at": b.next_contact_at.isoformat() if b.next_contact_at else None,
        "last_contacted_at": b.last_contacted_at.isoformat() if b.last_contacted_at else None,
        "priority": b.priority or "medium",
        "owner_first_name": b.owner_first_name,
        "owner_last_name": b.owner_last_name,
        "owner_role": b.owner_role,
        "owner_email": b.owner_email,
        "owner_phone": b.owner_phone,
        "siren": b.siren,
        "legal_form": b.legal_form,
        "company_creation_date": b.company_creation_date,
        "employee_range": b.employee_range,
        "enrichment_status": b.enrichment_status,
        "enrichment_details": b.enrichment_details,
        "contact_confidence": b.contact_confidence or 0,
        "tags": b.tags or [],
        "deal_value": b.deal_value or 0,
    }


@app.get("/crm/pipeline")
async def get_crm_pipeline(db: Session = Depends(get_db)):
    businesses = db.query(Business).all()
    stages = ["prospect", "contacted", "demo_sent", "negotiating", "won", "lost"]
    pipeline = {s: [] for s in stages}
    for b in businesses:
        stage = b.crm_stage or "prospect"
        pipeline.setdefault(stage, []).append(_crm_dict(b))
    won_count = sum(1 for b in businesses if (b.crm_stage or "prospect") == "won")
    contacted_count = sum(1 for b in businesses if (b.crm_stage or "prospect") not in ["prospect", "lost"])
    total_pipeline_value = sum(b.deal_value or 0 for b in businesses if (b.crm_stage or "prospect") == "negotiating")
    return {
        "pipeline": pipeline,
        "stats": {
            "total_prospects": len(businesses),
            "pipeline_value": total_pipeline_value,
            "won_clients": won_count,
            "conversion_rate": round(won_count / max(contacted_count, 1) * 100, 1),
        }
    }

@app.patch("/businesses/{business_id}/crm")
async def update_crm(business_id: str, data: dict, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    for field in {"crm_stage", "crm_notes", "priority", "owner_email", "owner_phone", "deal_value", "tags"}:
        if field in data:
            setattr(b, field, data[field])
    if "owner_email" in data or "owner_phone" in data:
        _refresh_scores(b)
    if "next_contact_at" in data:
        val = data["next_contact_at"]
        b.next_contact_at = datetime.datetime.fromisoformat(val) if val else None
    if data.get("crm_stage") in ["contacted", "demo_sent", "negotiating", "won"]:
        b.last_contacted_at = datetime.datetime.utcnow()
    db.commit()
    return {"ok": True}

@app.get("/businesses/{business_id}/activities")
async def get_activities(business_id: str, db: Session = Depends(get_db)):
    acts = (db.query(CrmActivity)
            .filter(CrmActivity.business_id == business_id)
            .order_by(CrmActivity.created_at.desc())
            .all())
    return [{"id": a.id, "type": a.type, "content": a.content,
             "created_at": a.created_at.isoformat()} for a in acts]

@app.post("/businesses/{business_id}/activities")
async def add_activity(business_id: str, data: dict, db: Session = Depends(get_db)):
    act = CrmActivity(
        business_id=business_id,
        type=data.get("type", "note"),
        content=data.get("content", ""),
    )
    db.add(act)
    b = db.query(Business).filter(Business.id == business_id).first()
    if b:
        b.last_contacted_at = datetime.datetime.utcnow()
    db.commit()
    return {"id": act.id, "type": act.type, "content": act.content,
            "created_at": act.created_at.isoformat()}


# ──────────────────────────────────────────────────────────────────────────────
# FIND EMAIL
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/businesses/{business_id}/find-email")
async def find_business_email(business_id: str, db: Session = Depends(get_db)):
    """Recherche un email professionnel publié, avec sources et diagnostic.

    Ordre : site officiel -> données déjà vérifiées -> enrichissement légal/web.
    Les suggestions de type contact@domaine restent non vérifiées et ne sont
    jamais enregistrées automatiquement.
    """
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")

    found = []
    sources = {}
    pages_checked = []
    diagnostics = []
    keys_configured = {
        "pappers": bool(os.getenv("PAPPERS_API_KEY")),
        "perplexity": bool(os.getenv("PERPLEXITY_API_KEY")),
    }

    # 1) Source propriétaire : pages publiques du site du commerce.
    if b.website:
        try:
            website_data = await asyncio.to_thread(WebsiteContactFinder().find, b.website)
            pages_checked = website_data.get("pages_checked", [])
            for email_value in website_data.get("emails", []):
                email_value = (email_value or "").strip().lower()
                if email_value and email_value not in found:
                    found.append(email_value)
                    sources[email_value] = website_data.get("email_sources", {}).get(
                        email_value, {"source": "website", "confidence": 90}
                    )
            diagnostics.append({
                "source": "website",
                "status": "found" if website_data.get("emails") else "no_result",
                "pages_checked": len(pages_checked),
            })
        except Exception as exc:
            diagnostics.append({"source": "website", "status": "error", "detail": str(exc)[:160]})
    else:
        diagnostics.append({"source": "website", "status": "unavailable", "detail": "Aucun site connu"})

    # 2) Email CRM déjà vérifié/enrichi.
    if b.owner_email and "@" in b.owner_email:
        email_value = b.owner_email.strip().lower()
        if email_value not in found:
            found.append(email_value)
            sources[email_value] = {
                "source": "crm",
                "confidence": int(b.contact_confidence or 80),
            }

    # 3) Pipeline complet : Pappers + site + recherche web.
    # Cela corrige l'ancien /find-email qui ignorait Pappers.
    enrichment = {}
    if not found:
        try:
            enrichment = await asyncio.to_thread(
                enrich_business, b.name, b.address or "", b.website or ""
            )
            candidate = (enrichment.get("contact_email") or "").strip().lower()
            details = enrichment.get("enrichment_details") or {}
            field_sources = details.get("field_sources") or {}
            candidate_source = field_sources.get("contact_email")
            if candidate and "@" in candidate:
                found.append(candidate)
                confidence = int(enrichment.get("contact_confidence") or 0)
                sources[candidate] = {
                    "source": candidate_source or "enrichment",
                    "confidence": confidence,
                    "citations": details.get("citations") or [],
                }

            for provider in ("pappers", "perplexity"):
                configured = keys_configured[provider]
                used = provider in (enrichment.get("enrichment_source") or {})
                diagnostics.append({
                    "source": provider,
                    "status": "found" if used else ("no_result" if configured else "not_configured"),
                })

            # Conserve aussi le dirigeant/SIREN trouvé pendant la recherche email.
            enrichment_map = {
                "owner_first_name": "owner_first_name",
                "owner_last_name": "owner_last_name",
                "owner_role": "owner_role",
                "siren": "siren",
                "legal_form": "legal_form",
                "company_creation_date": "company_creation_date",
                "employee_range": "employee_range",
                "phone": "owner_phone",
                "enrichment_details": "enrichment_details",
            }
            for src, dst in enrichment_map.items():
                if enrichment.get(src) and not getattr(b, dst, None):
                    setattr(b, dst, enrichment[src])
        except Exception as exc:
            diagnostics.append({"source": "enrichment", "status": "error", "detail": str(exc)[:160]})

    if found:
        best = found[0]
        src = sources.get(best, {})
        if not b.owner_email or src.get("confidence", 0) >= int(b.contact_confidence or 0):
            b.owner_email = best
            b.contact_confidence = float(src.get("confidence", b.contact_confidence or 0))
            b.enrichment_status = "enriched"
            _refresh_scores(b)
            db.commit()

    suggestions = []
    if b.website:
        parsed = urllib.parse.urlparse(b.website if "://" in b.website else "https://" + b.website)
        domain = (parsed.netloc or "").lower().lstrip("www.")
        if domain and "." in domain:
            suggestions = [f"contact@{domain}", f"info@{domain}", f"bonjour@{domain}"]
            suggestions = [x for x in suggestions if x not in found][:3]

    if found:
        message = f"{len(found)} email(s) publié(s)/vérifié(s) trouvé(s)"
    else:
        available = [k for k, v in keys_configured.items() if v]
        message = "Aucun email professionnel publié trouvé"
        if not available:
            message += " · Pappers et recherche web non configurés"

    return {
        "found": found[:5],
        "verified_sources": sources,
        "unverified_suggestions": suggestions,
        "guesses": suggestions,
        "website": b.website,
        "pages_checked": pages_checked,
        "keys_configured": keys_configured,
        "diagnostics": diagnostics,
        "message": message,
    }

# ──────────────────────────────────────────────────────────────────────────────
# ENRICHISSEMENT CONTACT (Pappers + Perplexity)
# ──────────────────────────────────────────────────────────────────────────────
@app.post("/businesses/{business_id}/enrich")
async def enrich_business_contact(business_id: str, db: Session = Depends(get_db)):
    """
    Enrichit un commerce : dirigeant (nom/prénom + SIREN via Pappers) et
    coordonnées (email/téléphone via Perplexity). Complète /find-email.
    """
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")

    b.enrichment_status = "enriching"
    db.commit()
    try:
        data = await asyncio.to_thread(enrich_business, b.name, b.address or "", b.website or "")
    except Exception as e:
        b.enrichment_status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {e}")

    # Mapping vers le modèle existant
    field_map = {
        "owner_first_name": "owner_first_name",
        "owner_last_name": "owner_last_name",
        "owner_role": "owner_role",
        "siren": "siren",
        "legal_form": "legal_form",
        "company_creation_date": "company_creation_date",
        "employee_range": "employee_range",
        "contact_email": "owner_email",
        "phone": "owner_phone",
        "contact_confidence": "contact_confidence",
        "enrichment_details": "enrichment_details",
    }
    for src, dst in field_map.items():
        if data.get(src):
            setattr(b, dst, data[src])
    b.enrichment_status = data.get("enrichment_status", "enriched")
    _refresh_scores(b)
    db.commit()

    return {
        "id": b.id,
        "owner_first_name": b.owner_first_name,
        "owner_last_name": b.owner_last_name,
        "owner_role": b.owner_role,
        "siren": b.siren,
        "legal_form": b.legal_form,
        "company_creation_date": b.company_creation_date,
        "employee_range": b.employee_range,
        "owner_email": b.owner_email,
        "owner_phone": b.owner_phone,
        "business_phone": b.business_phone,
        "contact_confidence": b.contact_confidence or 0,
        "enrichment_details": b.enrichment_details,
        "digital_health_score": b.digital_health_score,
        "opportunity_score": b.opportunity_score,
        "opportunity_breakdown": b.opportunity_breakdown,
        "enrichment_status": b.enrichment_status,
        "enrichment_source": data.get("enrichment_source", {}),
        "keys_configured": data.get("keys_configured", {}),
    }


# ──────────────────────────────────────────────────────────────────────────────
# SUPERVISION (SSL / avis Google / SEO) + planificateur quotidien
# ──────────────────────────────────────────────────────────────────────────────
def _supervise_business(business, db, maps) -> dict:
    """Supervise un site déployé et persiste l'état (SSL, avis, SEO)."""
    report = run_monitoring(business, maps)
    # Reflète l'état dans les champs du modèle existant
    ssl_status = report.get("ssl", {}).get("status")
    business.domain_ssl_active = bool(ssl_status == "ok")
    seo_score = report.get("seo", {}).get("score")
    if seo_score is not None:
        business.seo_score = seo_score
    rv = report.get("reviews", {})
    if rv.get("status") == "ok":
        if rv.get("rating"):
            business.rating = rv["rating"]
        if rv.get("total"):
            business.user_ratings_total = rv["total"]
        # Signale qu'une re-publication rafraîchirait le SEO (note/avis)
        report["needs_seo_refresh"] = bool(rv.get("new_reviews", 0) > 0 or rv.get("rating_delta", 0) not in (0, None))
    business.monitoring = report
    db.commit()
    return report


@app.post("/monitor/{business_id}")
async def monitor_site(business_id: str, db: Session = Depends(get_db)):
    """Vérifie SSL + avis Google + santé SEO d'un site déployé."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    report = await asyncio.to_thread(_supervise_business, b, db, GoogleMapsService())
    return {"id": b.id, "monitoring": report}


def _supervise_all_sites(limit: int = 200) -> dict:
    """Supervise tous les sites déployés (endpoint /monitor-all + planificateur)."""
    from backend.models.database import SessionLocal
    db = SessionLocal()
    maps = GoogleMapsService()
    summary = {"checked": 0, "ok": 0, "warning": 0, "error": 0, "partial": 0, "problems": []}
    try:
        targets = db.query(Business).filter(Business.deployment_url.isnot(None)).limit(limit).all()
        for b in targets:
            try:
                report = _supervise_business(b, db, maps)
            except Exception as e:
                print(f"Supervision failed for {getattr(b,'id','?')}: {e}")
                summary["error"] += 1
                summary["checked"] += 1
                continue
            overall = report.get("overall", "error")
            summary["checked"] += 1
            summary[overall] = summary.get(overall, 0) + 1
            if overall in ("warning", "error"):
                summary["problems"].append({
                    "name": b.name, "url": b.deployment_url, "overall": overall,
                    "ssl": report.get("ssl", {}).get("status"),
                    "ssl_days_left": report.get("ssl", {}).get("days_left"),
                    "seo_score": report.get("seo", {}).get("score"),
                })
        return summary
    finally:
        db.close()


@app.post("/monitor-all")
async def monitor_all(limit: int = 200, db: Session = Depends(get_db)):
    summary = await asyncio.to_thread(_supervise_all_sites, limit)
    return summary


async def scheduled_supervision() -> dict:
    """Tâche quotidienne : supervise tous les sites + alerte si problèmes."""
    summary = await asyncio.to_thread(_supervise_all_sites, 200)
    if summary.get("problems"):
        from backend.services.alerts import send_alert
        await asyncio.to_thread(
            send_alert,
            f"[Local-Pulse] Supervision : {len(summary['problems'])} site(s) à surveiller",
            summary,
        )
    return summary


@app.get("/scheduler/status")
async def scheduler_status():
    if not supervision_scheduler:
        return {"enabled": False, "detail": "Planificateur désactivé (MONITOR_SCHEDULE_ENABLED=false)"}
    return supervision_scheduler.status()


async def scheduled_autopilot() -> dict:
    """Tâche nocturne autonome : prospection, génération, déploiement et emails prêts."""
    return await run_autopilot("scheduled")


def _autopilot_window_start(kind: str = "today") -> datetime.datetime:
    """Return a UTC-naive datetime for dashboard aggregation in Europe/Paris."""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(os.getenv("AUTOPILOT_TZ", "Europe/Paris"))
    except Exception:
        tz = datetime.timezone.utc
    now = datetime.datetime.now(tz)
    if kind == "night":
        # "Cette nuit" = depuis 18h la veille jusqu'à maintenant.
        day = now.date() if now.hour >= 18 else (now - datetime.timedelta(days=1)).date()
        start_local = datetime.datetime.combine(day, datetime.time(18, 0), tzinfo=tz)
    else:
        start_local = datetime.datetime.combine(now.date(), datetime.time(0, 0), tzinfo=tz)
    return start_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)


@app.get("/automation/dashboard")
async def automation_dashboard(db: Session = Depends(get_db)):
    """Morning cockpit: what Local Pulse already did today / overnight."""
    today_start = _autopilot_window_start("today")
    night_start = _autopilot_window_start("night")

    def aggregate(start):
        runs = (
            db.query(AutomationRun)
            .filter(AutomationRun.started_at >= start)
            .order_by(AutomationRun.started_at.desc())
            .all()
        )
        return {
            "runs": len(runs),
            "businesses_scanned": sum(r.businesses_scanned or 0 for r in runs),
            "opportunities_selected": sum(r.opportunities_selected or 0 for r in runs),
            "sites_generated": sum(r.sites_generated or 0 for r in runs),
            "sites_deployed": sum(r.sites_deployed or 0 for r in runs),
            "emails_ready": sum(r.emails_ready or 0 for r in runs),
            "errors": sum(r.errors_count or 0 for r in runs),
        }

    email_ready_total = 0
    email_without_recipient = 0
    ready_rows = db.query(Business).filter(Business.email_status == "ready").all()
    for b in ready_rows:
        copy_data = b.generated_copy or {}
        if isinstance(copy_data, str):
            try:
                copy_data = json.loads(copy_data)
            except Exception:
                copy_data = {}
        if (copy_data.get("email") or "").strip():
            email_ready_total += 1
            if not (b.owner_email or "").strip():
                email_without_recipient += 1

    last_run = db.query(AutomationRun).order_by(AutomationRun.id.desc()).first()
    zones = db.query(AutomationZone).order_by(AutomationZone.id).all()
    return {
        "today": aggregate(today_start),
        "overnight": aggregate(night_start),
        "queue": {
            "emails_ready_total": email_ready_total,
            "emails_missing_recipient": email_without_recipient,
            "sites_waiting_validation": db.query(Business).filter(Business.status == "pending_validation").count(),
            "errors": db.query(Business).filter(Business.status == "error").count(),
        },
        "autopilot": {
            "enabled": bool(autopilot_scheduler),
            "scheduler": autopilot_scheduler.status() if autopilot_scheduler else None,
            "zones_enabled": len([z for z in zones if z.enabled]),
            "zones_total": len(zones),
            "auto_deploy": os.getenv("AUTOPILOT_AUTO_DEPLOY", "true").lower() == "true",
            "email_send_mode": "approval_required",
        },
        "last_run": {
            "id": last_run.id,
            "status": last_run.status,
            "trigger": last_run.trigger,
            "started_at": last_run.started_at.isoformat() if last_run and last_run.started_at else None,
            "finished_at": last_run.finished_at.isoformat() if last_run and last_run.finished_at else None,
            "summary": last_run.summary,
            "error": last_run.error,
            "current_business_id": last_run.current_business_id,
            "current_business_name": last_run.current_business_name,
            "current_stage": last_run.current_stage,
            "current_index": last_run.current_index or 0,
            "total_selected": last_run.total_selected or 0,
            "heartbeat_at": last_run.heartbeat_at.isoformat() if last_run.heartbeat_at else None,
            "stalled": bool(
                last_run.status == "running"
                and last_run.heartbeat_at
                and last_run.heartbeat_at < datetime.datetime.utcnow() - datetime.timedelta(minutes=45)
            ),
        } if last_run else None,
    }


@app.get("/automation/projects")
async def automation_projects(kind: str = "scanned", scope: str = "overnight", limit: int = 200, db: Session = Depends(get_db)):
    """List the exact projects behind a dashboard metric card."""
    start = _autopilot_window_start("night" if scope == "overnight" else "today")
    q = db.query(Business)
    if kind == "scanned":
        q = q.filter(Business.automation_last_scanned_at >= start)
    elif kind == "opportunities":
        q = q.filter(Business.automation_selected_at >= start)
    elif kind == "generated":
        q = q.filter(Business.generated_at >= start)
    elif kind == "deployed":
        q = q.filter(Business.deployed_at >= start)
    elif kind == "emails":
        q = q.filter(Business.email_ready_at >= start)
    elif kind == "errors":
        q = q.filter(Business.automation_error_at >= start)
    else:
        raise HTTPException(status_code=400, detail="Type de liste inconnu.")

    rows = q.order_by(Business.opportunity_score.desc(), Business.updated_at.desc()).limit(max(1, min(500, limit))).all()
    return [{
        "id": b.id,
        "name": b.name,
        "address": b.address,
        "opportunity_score": b.opportunity_score or 0,
        "digital_health_score": b.digital_health_score or 0,
        "status": b.status,
        "website": b.website,
        "deployment_url": b.deployment_url,
        "email_status": b.email_status,
        "automation_source": b.automation_source,
    } for b in rows]


@app.get("/automation/zones")
async def list_automation_zones(db: Session = Depends(get_db)):
    rows = db.query(AutomationZone).order_by(AutomationZone.id).all()
    return [{
        "id": z.id,
        "name": z.name,
        "query": z.query,
        "latitude": z.latitude,
        "longitude": z.longitude,
        "radius": z.radius,
        "enabled": z.enabled,
        "min_opportunity_score": z.min_opportunity_score,
        "max_sites_per_run": z.max_sites_per_run,
    } for z in rows]


@app.post("/automation/zones")
async def create_automation_zone(data: dict, db: Session = Depends(get_db)):
    name = str(data.get("name") or data.get("query") or "").strip()
    query = str(data.get("query") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nom ou ville requis.")

    lat = data.get("latitude")
    lng = data.get("longitude")
    if lat is None or lng is None:
        if not query:
            raise HTTPException(status_code=400, detail="query requis si latitude/longitude absentes.")
        geo = await asyncio.to_thread(GoogleMapsService().geocode, query)
        if not isinstance(geo, dict) or "error" in geo:
            raise HTTPException(status_code=400, detail=f"Impossible de localiser {query}.")
        lat, lng = geo["lat"], geo["lng"]

    zone = AutomationZone(
        name=name,
        query=query or name,
        latitude=float(lat),
        longitude=float(lng),
        radius=max(100, min(5000, int(data.get("radius") or 1000))),
        enabled=bool(data.get("enabled", True)),
        min_opportunity_score=max(0, min(100, float(data.get("min_opportunity_score") or 62))),
        max_sites_per_run=max(0, min(20, int(data.get("max_sites_per_run") or 3))),
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return {"id": zone.id, "name": zone.name, "status": "created"}


@app.patch("/automation/zones/{zone_id}")
async def update_automation_zone(zone_id: int, data: dict, db: Session = Depends(get_db)):
    zone = db.query(AutomationZone).filter(AutomationZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone introuvable.")
    allowed = {"name", "query", "radius", "enabled", "min_opportunity_score", "max_sites_per_run"}
    for key, value in data.items():
        if key in allowed:
            setattr(zone, key, value)
    zone.radius = max(100, min(5000, int(zone.radius or 1000)))
    zone.min_opportunity_score = max(0, min(100, float(zone.min_opportunity_score or 62)))
    zone.max_sites_per_run = max(0, min(20, int(zone.max_sites_per_run or 3)))
    db.commit()
    return {"status": "updated"}


@app.delete("/automation/zones/{zone_id}")
async def delete_automation_zone(zone_id: int, db: Session = Depends(get_db)):
    zone = db.query(AutomationZone).filter(AutomationZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone introuvable.")
    db.delete(zone)
    db.commit()
    return {"status": "deleted"}


@app.post("/automation/run")
async def run_automation_now(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manual test button; refuses to stack a second healthy run."""
    stale_before = datetime.datetime.utcnow() - datetime.timedelta(minutes=45)
    active = db.query(AutomationRun).filter(
        AutomationRun.status == "running",
        AutomationRun.heartbeat_at.isnot(None),
        AutomationRun.heartbeat_at >= stale_before,
    ).order_by(AutomationRun.id.desc()).first()
    if active:
        raise HTTPException(
            status_code=409,
            detail=f"Un run est déjà en cours (#{active.id} · {active.current_business_name or 'scan'} · {active.current_stage or 'en cours'}).",
        )

    async def _run():
        try:
            await run_autopilot("manual")
        except Exception as exc:
            print(f"Autopilot manual run failed: {exc}")
    background_tasks.add_task(_run)
    return {"status": "started"}


@app.get("/automation/runs")
async def automation_runs(limit: int = 30, db: Session = Depends(get_db)):
    rows = db.query(AutomationRun).order_by(AutomationRun.id.desc()).limit(max(1, min(100, limit))).all()
    return [{
        "id": r.id,
        "trigger": r.trigger,
        "status": r.status,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "zones_processed": r.zones_processed,
        "businesses_scanned": r.businesses_scanned,
        "opportunities_selected": r.opportunities_selected,
        "sites_generated": r.sites_generated,
        "sites_deployed": r.sites_deployed,
        "emails_ready": r.emails_ready,
        "errors_count": r.errors_count,
        "summary": r.summary,
        "error": r.error,
    } for r in rows]


@app.get("/automation/scheduler/status")
async def automation_scheduler_status():
    if not autopilot_scheduler:
        return {"enabled": False, "detail": "Autopilot désactivé"}
    return autopilot_scheduler.status()


@app.post("/recalculate-scores")
async def recalculate_scores(db: Session = Depends(get_db)):
    """Recalcule Digital Health + Opportunity Score sur tous les prospects."""
    rows = db.query(Business).all()
    updated = 0
    for b in rows:
        before = (b.digital_health_score or 0, b.opportunity_score or 0)
        _refresh_scores(b)
        after = (b.digital_health_score or 0, b.opportunity_score or 0)
        if before != after:
            updated += 1
    db.commit()
    return {"recalculated": len(rows), "updated": updated}
