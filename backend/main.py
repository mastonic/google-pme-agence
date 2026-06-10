from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.agents.manager import LocalPulseManager
from backend.services.google_maps import GoogleMapsService
from backend.models.database import engine, Base, get_db, Business, Plan, DesignPreset
from dotenv import load_dotenv
import os
import asyncio
import json
import re
import datetime
import redis

load_dotenv()

active_logs = {}

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
            "features_seo_blog_active": "INTEGER DEFAULT 0",
            "features_gmb_reviews_sync": "INTEGER DEFAULT 0",
            "seo_score": "REAL DEFAULT 0",
            "keywords_tracked": "TEXT",
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
    from backend.models.database import SessionLocal
    seed_if_empty(SessionLocal())

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
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "google_maps": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
            "vercel": bool(os.getenv("VERCEL_API_TOKEN")),
        }
    }


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


# ──────────────────────────────────────────────────────────────────────────────
# BUSINESSES (Prospection CRM)
# ──────────────────────────────────────────────────────────────────────────────

def calculate_potential_score(place_data: dict) -> float:
    score = 5.0
    if not place_data.get("website"): score += 3.0
    if 0 < place_data.get("rating", 0) < 4.0: score += 1.0
    if 0 < place_data.get("user_ratings_total", 0) < 10: score += 1.0
    return min(10.0, score)

def _biz_to_dict(b: Business) -> dict:
    return {
        "id": b.id, "name": b.name, "address": b.address,
        "latitude": b.latitude, "longitude": b.longitude,
        "rating": b.rating, "user_ratings_total": b.user_ratings_total,
        "status": b.status, "potential_score": b.potential_score,
        "website": b.website, "template": b.template,
        "email_status": b.email_status, "generated_copy": b.generated_copy,
        "deployment_url": b.deployment_url,
        # SaaS fields
        "plan_tier": b.plan_tier, "subscription_status": b.subscription_status,
        "mrr_value": b.mrr_value or 0,
        "custom_domain": b.custom_domain, "domain_ssl_active": b.domain_ssl_active,
        "features_booking_active": b.features_booking_active,
        "features_menu_active": b.features_menu_active,
        "features_seo_blog_active": b.features_seo_blog_active,
        "features_gmb_reviews_sync": b.features_gmb_reviews_sync,
        "seo_score": b.seo_score or 0, "keywords_tracked": b.keywords_tracked,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
        "client_signed_at": b.client_signed_at.isoformat() if b.client_signed_at else None,
    }

@app.post("/scan")
async def scan_local_businesses(lat: float, lng: float, radius: int = 500, db: Session = Depends(get_db)):
    maps_service = GoogleMapsService()
    results = maps_service.search_nearby_businesses(lat, lng, radius)
    if isinstance(results, dict) and "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])

    businesses = []
    for place in results:
        details = maps_service.get_business_details(place["place_id"])
        potential = 5.0 if (isinstance(details, dict) and "error" in details) else calculate_potential_score(details)
        b = db.query(Business).filter(Business.id == place["place_id"]).first()
        if not b:
            b = Business(
                id=place["place_id"], name=place["name"],
                address=place.get("vicinity"),
                latitude=place["geometry"]["location"]["lat"],
                longitude=place["geometry"]["location"]["lng"],
                rating=place.get("rating"), user_ratings_total=place.get("user_ratings_total"),
                website=details.get("website") if isinstance(details, dict) else None,
                potential_score=potential
            )
            db.add(b)
        else:
            b.potential_score = potential
            b.website = details.get("website") if isinstance(details, dict) else b.website
            b.latitude = place["geometry"]["location"]["lat"]
            b.longitude = place["geometry"]["location"]["lng"]
        businesses.append({"id": b.id, "name": b.name, "address": b.address,
                            "latitude": b.latitude, "longitude": b.longitude,
                            "rating": b.rating, "potential_score": b.potential_score, "status": b.status})
    db.commit()
    return {"count": len(businesses), "businesses": businesses}

@app.get("/businesses")
async def list_businesses(db: Session = Depends(get_db)):
    return [_biz_to_dict(b) for b in db.query(Business).order_by(Business.potential_score.desc()).all()]

@app.get("/businesses/{business_id}")
async def get_business_detail(business_id: str, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b: raise HTTPException(status_code=404, detail="Not found")
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
            else:
                biz.photos = details.get("photos", [])
                biz.website = details.get("website")
                biz.category = details.get("types", [])
            new_db.commit()

            business_data = {
                "name": biz.name, "address": biz.address, "rating": biz.rating,
                "phone": details.get("formatted_phone_number", ""),
                "user_ratings_total": details.get("user_ratings_total", 0),
                "business_id": bid, "types": biz.category or [], "photos": biz.photos or []
            }
            manager = LocalPulseManager(business_data, log_queue=active_logs.get(bid))

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
        finally:
            new_db.close()

    background_tasks.add_task(run_orchestration_task, business_id)
    return {"status": "Processing Started"}

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
        except Exception as e:
            try:
                err_db = SessionLocal(); tbiz = err_db.query(Business).filter(Business.id == bid).first()
                if tbiz: tbiz.status = "error"; err_db.commit(); err_db.close()
            except Exception: pass
            if bid in active_logs:
                await active_logs[bid].put({"type": "error", "message": str(e)})
                await active_logs[bid].put({"type": "end"})
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
        "features_seo_blog_active", "features_gmb_reviews_sync",
        "seo_score", "keywords_tracked"
    }
    for k, v in data.items():
        if k in ALLOWED: setattr(b, k, v)

    # Auto-set mrr_value from plan tier if not explicitly provided
    if "plan_tier" in data and "mrr_value" not in data:
        tier_prices = {"free": 0, "starter": 49, "pro": 149, "elite": 299}
        b.mrr_value = tier_prices.get(data["plan_tier"], 0)

    db.commit()
    return _biz_to_dict(b)
