from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.agents.manager import LocalPulseManager
from backend.services.google_maps import GoogleMapsService
from backend.services.vercel_deploy import VercelService
from backend.models.database import engine, Base, get_db, Business
from dotenv import load_dotenv
import os
import asyncio
import json
import redis

load_dotenv()

# Global dict to store asyncio.Queue for each active orchestration
active_logs = {}

# Initialize Redis client for caching assets (with in-memory fallback)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("Backend : Connecté à Redis (localhost:6379)")
except Exception:
    print("Redis server not found. Using in-memory fallback cache.")
    class DummyRedis:
        def __init__(self):
            self.store = {}
        def set(self, k, v, ex=None):
            self.store[k] = v
        def get(self, k):
            return self.store.get(k)
    redis_client = DummyRedis()

app = FastAPI(title="Local-Pulse SaaS Orchestrator")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for debugging CORS issues
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Local-Pulse API is running",
        "endpoints": {
            "status": "/status",
            "businesses": "/businesses",
            "scan": "/scan (POST)"
        }
    }

# Startup
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

    # Add generated_html column if it doesn't exist (SQLite migration)
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(engine)
        cols = [c["name"] for c in inspector.get_columns("businesses")]
        if "generated_html" not in cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE businesses ADD COLUMN generated_html TEXT"))
                conn.commit()
            print("Migration: added column generated_html")
    except Exception as e:
        print(f"Migration check skipped: {e}")

    print("Local-Pulse Backend Ready")

@app.get("/status")
async def get_status():
    return {
        "status": "Ready",
        "api_verification": {
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "google_maps": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
            "vercel": bool(os.getenv("VERCEL_API_TOKEN")),
        }
    }

@app.get("/preview/{business_id}")
async def preview_business(business_id: str, db: Session = Depends(get_db)):
    """Return the generated HTML as a renderable page for iframe preview."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not business.generated_html:
        return HTMLResponse(
            content="<html><body style='font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;background:#0f172a;color:#94a3b8;'>"
                    "<p>⏳ Le site est en cours de génération...</p></body></html>",
            status_code=200
        )
    return HTMLResponse(content=business.generated_html)

@app.get("/stream/{business_id}")
async def stream_logs(business_id: str, request: Request):
    """
    SSE Endpoint for real-time agent chat.
    """
    if business_id not in active_logs:
        active_logs[business_id] = asyncio.Queue()

    async def event_generator():
        q = active_logs[business_id]
        try:
            while True:
                # If client closes connection, request.is_disconnected() might be true
                if await request.is_disconnected():
                    break
                
                # Wait for a new message from the orchestration thread
                msg = await q.get()
                
                yield f"data: {json.dumps(msg)}\n\n"
                
                if msg.get("type") == "end":
                    break
        except asyncio.CancelledError:
            pass
        finally:
            if business_id in active_logs:
                # Cleanup logic if needed, but usually we just let it finish
                pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")

def calculate_potential_score(place_data: dict) -> float:
    """
    Heuristique pour le score de potentiel digital (1-10).
    """
    score = 5.0
    # Pas de site web = Cible prioritaire
    if not place_data.get("website"):
        score += 3.0
    
    # Note basse = Besoin d'amélioration
    rating = place_data.get("rating", 0)
    if 0 < rating < 4.0:
        score += 1.0
    
    # Peu d'avis = Manque de preuve sociale
    user_ratings = place_data.get("user_ratings_total", 0)
    if 0 < user_ratings < 10:
        score += 1.0
        
    return min(10.0, score)

@app.post("/scan")
async def scan_local_businesses(lat: float, lng: float, radius: int = 500, db: Session = Depends(get_db)):
    maps_service = GoogleMapsService()
    print(f"🔍 DEBUG Scan : Lancement recherche nearby (Lat: {lat}, Lng: {lng}, Radius: {radius})")
    results = maps_service.search_nearby_businesses(lat, lng, radius)
    
    if isinstance(results, dict) and "error" in results:
        print(f"❌ ERROR Scan : {results['error']}")
        raise HTTPException(status_code=400, detail=results["error"])

    print(f"✅ DEBUG Scan : {len(results)} commerces trouvés par Google Maps.")
    businesses = []
    for place in results:
        # Get more details for website check
        details = maps_service.get_business_details(place["place_id"])
        
        if isinstance(details, dict) and "error" in details:
            print(f"Error fetching details for {place['place_id']}: {details['error']}")
            potential = 5.0 # Default score if details fail
        else:
            potential = calculate_potential_score(details)
            
        # Save or update in DB
        business = db.query(Business).filter(Business.id == place["place_id"]).first()
        if not business:
            business = Business(
                id=place["place_id"],
                name=place["name"],
                address=place.get("vicinity"),
                latitude=place["geometry"]["location"]["lat"],
                longitude=place["geometry"]["location"]["lng"],
                rating=place.get("rating"),
                user_ratings_total=place.get("user_ratings_total"),
                website=details.get("website"),
                potential_score=potential
            )
            db.add(business)
        else:
            business.potential_score = potential
            business.website = details.get("website")
            business.latitude = place["geometry"]["location"]["lat"]
            business.longitude = place["geometry"]["location"]["lng"]
        
        businesses.append({
            "id": business.id,
            "name": business.name,
            "address": business.address,
            "latitude": business.latitude,
            "longitude": business.longitude,
            "rating": business.rating,
            "potential_score": business.potential_score,
            "status": business.status
        })
    
    db.commit()
    
    # Return collected data immediately for speed and reliability
    return {
        "count": len(businesses), 
        "businesses": businesses
    }

@app.get("/businesses")
async def list_businesses(db: Session = Depends(get_db)):
    businesses = db.query(Business).order_by(Business.potential_score.desc()).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "address": b.address,
            "latitude": b.latitude,
            "longitude": b.longitude,
            "rating": b.rating,
            "user_ratings_total": b.user_ratings_total,
            "status": b.status,
            "potential_score": b.potential_score,
            "website": b.website,
            "template": b.template,
            "email_status": b.email_status,
            "generated_copy": b.generated_copy,
            "updated_at": b.updated_at.isoformat() if b.updated_at else None
        } for b in businesses
    ]

@app.get("/businesses/{business_id}")
async def get_business_detail(business_id: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

@app.patch("/businesses/{business_id}")
async def update_business(business_id: str, data: dict, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    for key, value in data.items():
        if hasattr(business, key):
            setattr(business, key, value)
    
    db.commit()
    return business

@app.post("/orchestrate/{business_id}")
async def start_orchestration(business_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if already processing
    business = db.query(Business).filter(Business.id == business_id).first()
    if business and business.status == "processing":
        return {"status": "Already Processing"}

    # Set status immediately to avoid double clicks
    if business:
        business.status = "processing"
        db.commit()
    
    # Initialize queue for this run
    active_logs[business_id] = asyncio.Queue()
    
    # Define background worker with its own DB session
    async def run_orchestration_task(bid: str):
        from .models.database import SessionLocal
        new_db = SessionLocal()
        try:
            target_biz = new_db.query(Business).filter(Business.id == bid).first()

            # 1. Enrich with Maps details
            maps_service = GoogleMapsService()
            details = maps_service.get_business_details(bid)

            if not target_biz:
                target_biz = Business(
                    id=bid,
                    name=details.get("name", "Nouveau Commerce"),
                    address=details.get("formatted_address", ""),
                    rating=details.get("rating", 0.0),
                    potential_score=calculate_potential_score(details),
                    status="processing"
                )
                new_db.add(target_biz)
            else:
                target_biz.photos = details.get("photos", [])
                target_biz.website = details.get("website")
                target_biz.category = details.get("types", [])

            new_db.commit()

            business_data = {
                "name": target_biz.name,
                "address": target_biz.address,
                "rating": target_biz.rating,
                "phone": details.get("formatted_phone_number", ""),
                "user_ratings_total": details.get("user_ratings_total", 0),
                "business_id": bid,
                "types": target_biz.category or [],
                "photos": target_biz.photos or []
            }
            manager = LocalPulseManager(business_data, log_queue=active_logs.get(bid))

            # STEP 1: PREP — investigation + design
            prep_result = await asyncio.to_thread(manager.run_prep_crew)
            target_biz.generated_copy = {
                "report": prep_result.get("report", ""),
                "copywriting": prep_result.get("copywriting", ""),
                "ai_photos": prep_result.get("ai_photos", ""),
                "design": prep_result.get("design", "")
            }
            new_db.commit()

            # STEP 2: BUILD — HTML streaming + email draft
            build_result = await asyncio.to_thread(manager.run_build_crew, prep_result)

            # Store HTML and mark as pending validation (waiting for user preview)
            target_biz.generated_html = build_result.get("html", "")
            target_biz.generated_copy = {
                **target_biz.generated_copy,
                "email": build_result.get("email", "")
            }
            target_biz.status = "pending_validation"
            new_db.commit()

            if bid in active_logs:
                await active_logs[bid].put({
                    "type": "chat",
                    "agent": "Système",
                    "message": "✅ Site généré ! Cliquez sur l'onglet **Aperçu du Site** pour valider avant déploiement."
                })
                await active_logs[bid].put({"type": "end"})

            if manager.redis_client:
                manager.redis_client.set(f"status:{bid}", "👀 En attente de validation...")

        except Exception as e:
            print(f"BACKGROUND ERROR for {bid}: {e}")
            import traceback; traceback.print_exc()
            try:
                err_db = SessionLocal()
                tbiz = err_db.query(Business).filter(Business.id == bid).first()
                if tbiz:
                    tbiz.status = "error"
                    err_db.commit()
                err_db.close()
            except Exception:
                pass
            if bid in active_logs:
                await active_logs[bid].put({"type": "error", "message": str(e)})
                await active_logs[bid].put({"type": "end"})
        finally:
            new_db.close()

    background_tasks.add_task(run_orchestration_task, business_id)
    
    return {"status": "Processing Started", "message": "Orchestration running in background"}

@app.post("/deploy/{business_id}")
async def deploy_business(business_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Deploy the pre-validated HTML to Vercel."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not business.generated_html:
        raise HTTPException(status_code=400, detail="No HTML generated yet. Run orchestration first.")
    if business.status == "completed":
        return {"status": "Already deployed", "url": business.deployment_url}

    business.status = "processing"
    db.commit()

    async def do_deploy(bid: str):
        from .models.database import SessionLocal
        new_db = SessionLocal()
        try:
            biz = new_db.query(Business).filter(Business.id == bid).first()
            business_data = {
                "name": biz.name,
                "address": biz.address or "",
                "rating": biz.rating or 0,
                "business_id": bid
            }
            if bid not in active_logs:
                active_logs[bid] = asyncio.Queue()

            manager = LocalPulseManager(business_data, log_queue=active_logs.get(bid))
            manager._push_log("L'Ingénieur", f"🚀 Déploiement de **{biz.name}** sur Vercel...", "chat")

            result = await asyncio.to_thread(manager.run_deploy_crew, biz.generated_html)

            import re
            url_match = re.search(r'https://[a-zA-Z0-9\-]+\.vercel\.app', result)
            if url_match:
                biz.deployment_url = url_match.group(0)

            biz.status = "completed"
            new_db.commit()

            url_display = biz.deployment_url or "URL en cours..."
            if bid in active_logs:
                await active_logs[bid].put({"type": "chat", "agent": "L'Ingénieur",
                                             "message": f"✅ Déployé ! {url_display}"})
                await active_logs[bid].put({"type": "end"})

            if manager.redis_client:
                manager.redis_client.set(f"status:{bid}", "✅ En ligne sur Vercel !")

        except Exception as e:
            print(f"DEPLOY ERROR for {bid}: {e}")
            try:
                err_db = SessionLocal()
                tbiz = err_db.query(Business).filter(Business.id == bid).first()
                if tbiz:
                    tbiz.status = "error"
                    err_db.commit()
                err_db.close()
            except Exception:
                pass
            if bid in active_logs:
                await active_logs[bid].put({"type": "error", "message": str(e)})
                await active_logs[bid].put({"type": "end"})
        finally:
            new_db.close()

    background_tasks.add_task(do_deploy, business_id)
    return {"status": "Deployment started"}
