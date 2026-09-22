from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.agents.manager import LocalPulseManager
from backend.services.google_maps import GoogleMapsService
from backend.services.apify_maps import ApifyMapsService
from backend.services.enrichment import enrich_business
from backend.services.scoring import calculate_scores
from backend.services.website_audit import audit_website
from backend.services.sales_engine import build_sales_snapshot, build_outreach_sequence, derive_next_action, due_date
from backend.services.monitoring import run_monitoring
from backend.services.scheduler import DailyScheduler
from backend.models.database import engine, Base, get_db, Business, Plan, DesignPreset, CrmActivity
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
            # Run 2 — moteur commercial interne
            "sales_snapshot": "TEXT",
            "outreach_sequence": "TEXT",
            "outreach_status": "TEXT DEFAULT 'not_started'",
            "outreach_step": "INTEGER DEFAULT 0",
            "outreach_started_at": "TEXT",
            "last_outreach_at": "TEXT",
            "next_action": "TEXT",
            "next_action_reason": "TEXT",
            "next_action_due_at": "TEXT",
            "prospecting_opt_out": "INTEGER DEFAULT 0",
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

    print("✅ Local-Pulse Backend v2 Ready")


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
        "api_keys": {
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
            "mistral": bool(os.getenv("MISTRAL_API_KEY")),
            "google_maps": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
            "vercel": bool(os.getenv("VERCEL_API_TOKEN")),
            "pappers": bool(os.getenv("PAPPERS_API_KEY")),
            "perplexity": bool(os.getenv("PERPLEXITY_API_KEY")),
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
        # Run 2 — moteur commercial
        "sales_snapshot": b.sales_snapshot,
        "outreach_sequence": b.outreach_sequence or [],
        "outreach_status": b.outreach_status or "not_started",
        "outreach_step": b.outreach_step or 0,
        "outreach_started_at": b.outreach_started_at.isoformat() if b.outreach_started_at else None,
        "last_outreach_at": b.last_outreach_at.isoformat() if b.last_outreach_at else None,
        "next_action": b.next_action or dynamic_action.get("action"),
        "next_action_label": dynamic_action.get("label"),
        "next_action_reason": b.next_action_reason or dynamic_action.get("reason"),
        "next_action_due_at": b.next_action_due_at.isoformat() if b.next_action_due_at else dynamic_action.get("due_at"),
        "prospecting_opt_out": bool(b.prospecting_opt_out),
        # Supervision
        "monitoring": b.monitoring,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
        "client_signed_at": b.client_signed_at.isoformat() if b.client_signed_at else None,
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

    businesses = []
    for place in results:
        # For Apify results, website is already in the place dict; skip a second API call
        if using_apify:
            details = {"website": place.get("website", "")}
        else:
            details = maps_service.get_business_details(place["place_id"])
            if isinstance(details, dict) and "error" in details:
                details = {}

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

        lat_val = place["geometry"]["location"]["lat"]
        lng_val = place["geometry"]["location"]["lng"]
        if lat_val is None or lng_val is None:
            continue

        b = db.query(Business).filter(Business.id == place["place_id"]).first()
        if not b:
            b = Business(
                id=place["place_id"], name=place["name"],
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

    return {"count": len(businesses), "businesses": businesses, "source": "apify" if using_apify else "google"}

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
    return {
        "name": biz.name, "address": biz.address, "rating": biz.rating,
        "phone": details.get("formatted_phone_number", ""),
        "user_ratings_total": details.get("user_ratings_total", 0),
        "business_id": biz.id, "types": biz.category or [],
        "photos": biz.photos or [],
        "reviews": details.get("reviews", []),
        "website": details.get("website", "") or biz.website or "",
        "potential_score": biz.potential_score or 0,
        "digital_health_score": biz.digital_health_score or 0,
        "opportunity_score": biz.opportunity_score or 0,
        "website_audit": biz.website_audit or {},
        "owner_first_name": biz.owner_first_name or "",
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
            m = re.search(r'https://[a-zA-Z0-9\-]+\.vercel\.app', result)
            if m: biz.deployment_url = m.group(0)
            biz.status = "completed"; new_db.commit()
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

PLAN_PRICES = {
    "starter": 4900,
    "pro":     14900,
    "elite":   29900,
}

PLAN_MRR = {
    "starter": 49.0,
    "pro":     149.0,
    "elite":   299.0,
}

@app.post("/create-checkout-session")
async def create_checkout_session(business_id: str, plan: str, db: Session = Depends(get_db)):
    import stripe as _stripe
    _stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Plan invalide : {plan}")
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")
    frontend_url = os.environ.get("FRONTEND_URL", "https://pme-local-pulse.web.app")
    session = _stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{
            "price_data": {
                "currency": "eur",
                "unit_amount": PLAN_PRICES[plan],
                "recurring": {"interval": "month"},
                "product_data": {
                    "name": f"Local-Pulse {plan.capitalize()}",
                    "description": f"Abonnement {plan} pour {b.name}",
                },
            },
            "quantity": 1,
        }],
        metadata={"business_id": business_id, "plan": plan},
        success_url=f"{frontend_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=frontend_url,
    )
    return {"checkout_url": session.url}


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
            if b:
                b.plan_tier = plan
                b.subscription_status = "active"
                b.mrr_value = PLAN_MRR.get(plan, 0.0)
                b.client_signed_at = datetime.datetime.utcnow()
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

    plan_prices = {"starter": 49, "pro": 149, "elite": 299}
    cta_price = plan_prices.get(b.plan_tier, 49) if b.plan_tier != "free" else 49

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
    """Returns business info + plan details for the frontend pricing modal."""
    plans = [
        {
            "slug": "starter",
            "name": "Starter",
            "price": 49,
            "features": [
                "Site vitrine 5 pages",
                "Hébergement inclus",
                "SSL",
                "Mise à jour mensuelle",
            ],
            "is_popular": False,
        },
        {
            "slug": "pro",
            "name": "Pro",
            "price": 149,
            "features": [
                "Tout Starter",
                "SEO local",
                "Fiche Google optimisée",
                "Rapport mensuel",
            ],
            "is_popular": True,
        },
        {
            "slug": "elite",
            "name": "Elite",
            "price": 299,
            "features": [
                "Tout Pro",
                "Blog SEO auto",
                "Avis Google sync",
                "Support prioritaire",
                "Domaine personnalisé",
            ],
            "is_popular": False,
        },
    ]
    business = None
    if business_id:
        b = db.query(Business).filter(Business.id == business_id).first()
        if b:
            business = {"id": b.id, "name": b.name, "plan_tier": b.plan_tier,
                        "subscription_status": b.subscription_status}
    return {"plans": plans, "business": business}


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
# SALES PLAYBOOK — Run 2
# ──────────────────────────────────────────────────────────────────────────────

def _sales_data(b: Business) -> dict:
    return {
        "id": b.id,
        "name": b.name,
        "address": b.address,
        "rating": b.rating or 0,
        "user_ratings_total": b.user_ratings_total or 0,
        "website": b.website,
        "website_audit": b.website_audit or {},
        "digital_health_score": b.digital_health_score or 0,
        "opportunity_score": b.opportunity_score or 0,
        "generated_html": bool(b.generated_html),
        "deployment_url": b.deployment_url,
        "owner_first_name": b.owner_first_name,
        "owner_last_name": b.owner_last_name,
        "owner_email": b.owner_email,
        "owner_phone": b.owner_phone,
        "business_phone": b.business_phone,
        "crm_stage": b.crm_stage or "prospect",
        "outreach_status": b.outreach_status or "not_started",
        "outreach_step": b.outreach_step or 0,
        "outreach_sequence": b.outreach_sequence or [],
        "outreach_started_at": b.outreach_started_at,
        "last_outreach_at": b.last_outreach_at,
        "next_action_due_at": b.next_action_due_at,
        "prospecting_opt_out": bool(b.prospecting_opt_out),
    }


def _public_demo_url(business_id: str, request: Request) -> str:
    base = (os.getenv("PUBLIC_APP_URL") or str(request.base_url)).rstrip("/")
    return f"{base}/demo/{business_id}"


def _sync_next_action(b: Business) -> dict:
    action = derive_next_action(_sales_data(b))
    b.next_action = action.get("action")
    b.next_action_reason = action.get("reason")
    due = action.get("due_at")
    if due:
        try:
            b.next_action_due_at = datetime.datetime.fromisoformat(str(due).replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            pass
    elif action.get("action") == "none":
        b.next_action_due_at = None
    return action


@app.get("/businesses/{business_id}/sales-playbook")
async def get_sales_playbook(business_id: str, request: Request, db: Session = Depends(get_db)):
    """Retourne l'avant/après, la séquence et la prochaine action sans rien envoyer."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")

    data = _sales_data(b)
    snapshot = build_sales_snapshot(data)
    sequence = build_outreach_sequence(data, _public_demo_url(b.id, request))
    b.sales_snapshot = snapshot
    # On peut régénérer le texte tant que la séquence n'a pas démarré.
    if (b.outreach_status or "not_started") == "not_started":
        b.outreach_sequence = sequence
    action = _sync_next_action(b)
    db.commit()

    return {
        "id": b.id,
        "snapshot": snapshot,
        "sequence": b.outreach_sequence or sequence,
        "outreach_status": b.outreach_status or "not_started",
        "outreach_step": b.outreach_step or 0,
        "next_action": action,
        "prospecting_opt_out": bool(b.prospecting_opt_out),
    }


@app.post("/businesses/{business_id}/outreach/start")
async def start_outreach(business_id: str, request: Request, db: Session = Depends(get_db)):
    """Prépare et planifie la séquence. Aucun message n'est envoyé par cet endpoint."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    if b.prospecting_opt_out:
        raise HTTPException(status_code=409, detail="Prospect marked do-not-contact")

    data = _sales_data(b)
    if not b.generated_html:
        raise HTTPException(status_code=409, detail="Generate the demo before starting outreach")

    now = datetime.datetime.utcnow()
    b.sales_snapshot = build_sales_snapshot(data)
    b.outreach_sequence = build_outreach_sequence(data, _public_demo_url(b.id, request))
    b.outreach_status = "active"
    b.outreach_step = 0
    b.outreach_started_at = now
    b.next_action = "outreach_step"
    b.next_action_reason = b.outreach_sequence[0]["why"]
    b.next_action_due_at = now
    b.next_contact_at = now
    db.commit()
    return _crm_dict(b)


@app.post("/businesses/{business_id}/outreach/complete-step")
async def complete_outreach_step(business_id: str, data: dict, db: Session = Depends(get_db)):
    """Marque une étape effectuée après action humaine et programme la suivante."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    if b.prospecting_opt_out:
        raise HTTPException(status_code=409, detail="Prospect marked do-not-contact")
    sequence = b.outreach_sequence or []
    expected = int(b.outreach_step or 0)
    index = int(data.get("index", expected))
    if index != expected:
        raise HTTPException(status_code=409, detail=f"Expected outreach step {expected}")
    if index >= len(sequence):
        raise HTTPException(status_code=409, detail="Outreach sequence already completed")

    step = sequence[index]
    now = datetime.datetime.utcnow()
    activity_type = "call" if step.get("channel") == "phone" else "email"
    act = CrmActivity(
        business_id=b.id,
        type=activity_type,
        content=data.get("note") or f"{step.get('title', 'Étape commerciale')} — étape {index + 1}/{len(sequence)}",
    )
    db.add(act)

    b.last_contacted_at = now
    b.last_outreach_at = now
    b.outreach_step = index + 1
    if index == 0 and (b.crm_stage or "prospect") == "prospect":
        # Le premier email contient le lien de démo.
        b.crm_stage = "demo_sent"

    if b.outreach_step < len(sequence):
        next_step = sequence[b.outreach_step]
        started = b.outreach_started_at or now
        due = due_date(started, next_step.get("day_offset", 0))
        b.outreach_status = "active"
        b.next_action = "outreach_step"
        b.next_action_reason = next_step.get("why")
        b.next_action_due_at = due
        b.next_contact_at = due
    else:
        b.outreach_status = "completed"
        due = now + datetime.timedelta(days=7)
        b.next_action = "review"
        b.next_action_reason = "Séquence terminée : décider de négocier, prolonger ou classer."
        b.next_action_due_at = due
        b.next_contact_at = due

    db.commit()
    db.refresh(b)
    return _crm_dict(b)


@app.post("/businesses/{business_id}/outreach/opt-out")
async def mark_prospect_opt_out(business_id: str, db: Session = Depends(get_db)):
    """Bloque les futures relances automatiques de ce prospect."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    b.prospecting_opt_out = True
    b.outreach_status = "paused"
    b.next_action = "none"
    b.next_action_reason = "Prospect opposé à la prospection"
    b.next_action_due_at = None
    b.next_contact_at = None
    db.add(CrmActivity(
        business_id=b.id,
        type="note",
        content="Prospect marqué « ne pas contacter ».",
    ))
    db.commit()
    return _crm_dict(b)


@app.get("/crm/today")
async def get_crm_today(db: Session = Depends(get_db)):
    """File d'actions commerciale calculée pour aujourd'hui."""
    now = datetime.datetime.utcnow()
    rows = db.query(Business).all()
    actions = []
    for b in rows:
        if (b.crm_stage or "prospect") in ("won", "lost") or b.prospecting_opt_out:
            continue
        action = derive_next_action(_sales_data(b), now=now)
        due_raw = action.get("due_at")
        due = None
        if due_raw:
            try:
                due = datetime.datetime.fromisoformat(str(due_raw).replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                due = now
        is_due = due is None or due <= now
        if is_due:
            actions.append({
                "id": b.id,
                "name": b.name,
                "opportunity_score": b.opportunity_score or 0,
                "crm_stage": b.crm_stage or "prospect",
                "action": action,
                "owner_email": b.owner_email,
                "owner_phone": b.owner_phone or b.business_phone,
            })
    actions.sort(key=lambda x: x.get("opportunity_score") or 0, reverse=True)
    return {"date": now.date().isoformat(), "count": len(actions), "actions": actions}


# ──────────────────────────────────────────────────────────────────────────────
# CRM
# ──────────────────────────────────────────────────────────────────────────────

def _crm_dict(b: Business) -> dict:
    scores = calculate_scores(_business_score_input(b), b.website_audit)
    opportunity_breakdown = b.opportunity_breakdown or scores["opportunity"]
    dynamic_action = derive_next_action(_sales_data(b))
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
        "generated_html": bool(b.generated_html),
        "deployment_url": b.deployment_url,
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
        "sales_snapshot": b.sales_snapshot,
        "outreach_sequence": b.outreach_sequence or [],
        "outreach_status": b.outreach_status or "not_started",
        "outreach_step": b.outreach_step or 0,
        "outreach_started_at": b.outreach_started_at.isoformat() if b.outreach_started_at else None,
        "last_outreach_at": b.last_outreach_at.isoformat() if b.last_outreach_at else None,
        "next_action": b.next_action,
        "next_action_reason": b.next_action_reason,
        "next_action_due_at": b.next_action_due_at.isoformat() if b.next_action_due_at else None,
        "prospecting_opt_out": bool(b.prospecting_opt_out),
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
    now = datetime.datetime.utcnow()
    actions_due = 0
    for b in businesses:
        if (b.crm_stage or "prospect") in ("won", "lost") or b.prospecting_opt_out:
            continue
        action = derive_next_action(_sales_data(b), now=now)
        due_raw = action.get("due_at")
        if not due_raw:
            actions_due += 1
            continue
        try:
            due_dt = datetime.datetime.fromisoformat(str(due_raw).replace("Z", "+00:00")).replace(tzinfo=None)
            if due_dt <= now:
                actions_due += 1
        except Exception:
            actions_due += 1
    return {
        "pipeline": pipeline,
        "stats": {
            "total_prospects": len(businesses),
            "pipeline_value": total_pipeline_value,
            "won_clients": won_count,
            "conversion_rate": round(won_count / max(contacted_count, 1) * 100, 1),
            "actions_due": actions_due,
        }
    }

@app.patch("/businesses/{business_id}/crm")
async def update_crm(business_id: str, data: dict, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    for field in {"crm_stage", "crm_notes", "priority", "owner_email", "owner_phone", "deal_value", "tags", "prospecting_opt_out"}:
        if field in data:
            setattr(b, field, data[field])
    if "owner_email" in data or "owner_phone" in data:
        _refresh_scores(b)
    if "next_contact_at" in data:
        val = data["next_contact_at"]
        b.next_contact_at = datetime.datetime.fromisoformat(val) if val else None
    if data.get("crm_stage") in ["contacted", "demo_sent", "negotiating", "won"]:
        b.last_contacted_at = datetime.datetime.utcnow()
    _sync_next_action(b)
    db.commit()
    return _crm_dict(b)

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
    """Scrape website + Perplexity search + generate guesses to find the business owner's email."""
    import requests as _req
    from backend.services.enrichment import PerplexityService
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")

    found   = []
    guesses = []

    # 1. Scrape website for emails
    if b.website:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; LocalPulse/1.0)"}
        SPAM = {"noreply", "no-reply", "donotreply", "example", "test", "placeholder", "sentry"}
        email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

        pages_to_check = [b.website]
        for suffix in ["/contact", "/nous-contacter", "/contact-us", "/a-propos", "/about"]:
            pages_to_check.append(b.website.rstrip("/") + suffix)

        for url in pages_to_check[:4]:
            try:
                resp = _req.get(url, timeout=6, headers=headers)
                emails_on_page = email_re.findall(resp.text)
                for e in emails_on_page:
                    el = e.lower()
                    if not any(s in el for s in SPAM) and el not in found:
                        found.append(el)
                if found:
                    break
            except Exception:
                continue

    # 2. Perplexity web search fallback when website scraping found nothing
    if not found:
        try:
            perplexity = PerplexityService()
            web_data = await asyncio.to_thread(perplexity.find_contacts, b.name, b.address or "")
            contact_email = web_data.get("contact_email", "")
            if contact_email and "@" in contact_email:
                found.append(contact_email.lower())
                # Also save it back to the business record
                if not b.owner_email:
                    b.owner_email = contact_email.lower()
                    db.commit()
        except Exception as e:
            print(f"Perplexity find-email fallback error: {e}")

    # 3. Generate guesses from domain
    if b.website:
        parsed = urllib.parse.urlparse(b.website)
        domain = parsed.netloc.lstrip("www.")
        if domain:
            name_slug = re.sub(r'[^a-z]', '', (b.name or '').lower().split()[0])
            candidates = [f"contact@{domain}", f"info@{domain}", f"bonjour@{domain}"]
            if name_slug:
                candidates.insert(0, f"{name_slug}@{domain}")
            guesses = [g for g in candidates if g not in found][:3]

    return {
        "found": found[:5],
        "guesses": guesses,
        "website": b.website,
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
        data = await asyncio.to_thread(enrich_business, b.name, b.address or "")
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
