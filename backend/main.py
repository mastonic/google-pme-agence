from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
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
    # Initialize DB (if needed)
    Base.metadata.create_all(bind=engine)
    print("Local-Pulse Backend Ready")

@app.get("/status")
async def get_status():
    google_key = os.getenv("GOOGLE_MAPS_API_KEY")
    vercel_token = os.getenv("VERCEL_API_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    return {
        "status": "Ready",
        "api_verification": {
            "openai": bool(openai_key)
        }
    }

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
    
    db.commit()
    
    # Return fresh data from DB to ensure consistency
    saved_businesses = db.query(Business).filter(Business.id.in_([p["place_id"] for p in results])).all()
    return {
        "count": len(saved_businesses), 
        "businesses": [
            {
                "id": b.id,
                "name": b.name,
                "address": b.address,
                "latitude": b.latitude,
                "longitude": b.longitude,
                "rating": b.rating,
                "potential_score": b.potential_score,
                "status": b.status
            } for b in saved_businesses
        ]
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
            # We need to refresh the business object in the new session
            target_biz = new_db.query(Business).filter(Business.id == bid).first()
            
            # 1. Get Details from Maps (Internal Step)
            maps_service = GoogleMapsService()
            details = maps_service.get_business_details(bid)
            
            if not target_biz:
                # Create if missing (unlikely but safe)
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

            # 2. Start Manager
            business_data = {
                "name": target_biz.name,
                "address": target_biz.address,
                "rating": target_biz.rating,
                "business_id": bid,
                "types": target_biz.category
            }
            manager = LocalPulseManager(business_data, log_queue=active_logs.get(bid))
            
            # STEP 1: PREP
            if manager.redis_client:
                manager.redis_client.set(f"status:{bid}", "🔍 Étape 1/2 : Analyse & Design...")
            
            prep_result = await asyncio.to_thread(manager.run_prep_crew)
            
            # Intermediate save
            target_biz.generated_copy = prep_result
            new_db.commit()

            # STEP 2: DEPLOY
            if manager.redis_client:
                manager.redis_client.set(f"status:{bid}", "🚀 Étape 2/2 : Construction & Déploiement...")
            
            deploy_json = await asyncio.to_thread(manager.run_deploy_crew, prep_result)
            deploy_data = json.loads(deploy_json)
            
            # Final Save
            target_biz.generated_copy = deploy_data
            target_biz.status = "completed"
            new_db.commit()

            # Send end signal
            if bid in active_logs:
                await active_logs[bid].put({"type": "end"})
            
            if manager.redis_client:
                manager.redis_client.set(f"status:{bid}", "✅ Démo Prête !")
                
        except Exception as e:
            print(f"BACKGROUND ERROR for {bid}: {e}")
            try:
                err_db = SessionLocal()
                tbiz = err_db.query(Business).filter(Business.id == bid).first()
                if tbiz:
                    tbiz.status = "error"
                    err_db.commit()
                err_db.close()
            except: pass
            
            if bid in active_logs:
                await active_logs[bid].put({"type": "error", "message": str(e)})
        finally:
            new_db.close()

    background_tasks.add_task(run_orchestration_task, business_id)
    
    return {"status": "Processing Started", "message": "Orchestration running in background"}

@app.post("/deploy/{business_id}")
async def deploy_business(business_id: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business or business.status != "pending_validation":
        raise HTTPException(status_code=400, detail="Business not ready for deployment")

    business.status = "processing"
    db.commit()

    try:
        prep_data = business.generated_copy if business.generated_copy else {}
        business_data = {
            "name": business.name,
            "address": business.address,
            "rating": business.rating,
            "business_id": business_id
        }
        
        if business_id not in active_logs:
            active_logs[business_id] = asyncio.Queue()
            
        manager = LocalPulseManager(business_data, log_queue=active_logs[business_id])
        
        # Step 2: Deploy Crew
        final_result = await asyncio.to_thread(manager.run_deploy_crew, prep_data)
        
        business.generated_copy = final_result
        business.status = "completed"
        db.commit()
        
        active_logs[business_id].put_nowait({"type": "end"})
        
        return {
            "status": "Deployed", 
            "result": final_result
        }
    except Exception as e:
        business.status = "error"
        db.commit()
        if business_id in active_logs:
            active_logs[business_id].put_nowait({"type": "end"})
        print("ERROR IN DEPLOY:", e); raise HTTPException(status_code=500, detail=str(e))
