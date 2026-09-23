"""Local Pulse Autopilot.

Nightly pipeline:
saved zones -> scan -> score -> generate -> deploy -> final sales email.
Email sending stays in human-approval mode by default.
"""
from __future__ import annotations

import asyncio
import datetime
import json
import os
import re
import urllib.parse
from typing import Any

from backend.agents.manager import LocalPulseManager
from backend.models.database import SessionLocal, Business, AutomationZone, AutomationRun
from backend.services.apify_maps import ApifyMapsService
from backend.services.google_maps import GoogleMapsService
from backend.services.plans import public_plan_catalog
from backend.services.scoring import calculate_scores


def _business_data(biz: Business, details: dict[str, Any]) -> dict[str, Any]:
    public_base = (os.getenv("PUBLIC_BASE_URL") or os.getenv("FRONTEND_URL") or "https://pme-local-pulse.web.app").rstrip("/")
    bid = urllib.parse.quote(str(biz.id), safe="")
    return {
        "name": biz.name,
        "address": biz.address,
        "rating": biz.rating,
        "phone": details.get("formatted_phone_number", "") or biz.business_phone or "",
        "user_ratings_total": details.get("user_ratings_total", 0) or biz.user_ratings_total or 0,
        "business_id": biz.id,
        "types": biz.category or [],
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
    }


async def _fetch_details(maps: GoogleMapsService, place: dict) -> tuple[str | None, dict]:
    place_id = (place or {}).get("place_id")
    if not place_id or str(place_id).startswith("apify_"):
        return place_id, {}
    try:
        details = await asyncio.wait_for(
            asyncio.to_thread(maps.get_business_details, place_id),
            timeout=10,
        )
        if not isinstance(details, dict) or "error" in details:
            details = {}
        return place_id, details
    except Exception:
        return place_id, {}


async def scan_zone(zone: AutomationZone, db) -> list[Business]:
    maps = GoogleMapsService()
    places = await asyncio.to_thread(
        maps.search_nearby_businesses,
        zone.latitude,
        zone.longitude,
        zone.radius,
    )

    using_apify = False
    if isinstance(places, dict) and "error" in places:
        apify = ApifyMapsService()
        if apify._available():
            places = await asyncio.to_thread(
                apify.search_nearby_businesses,
                zone.latitude,
                zone.longitude,
                zone.radius,
            )
            using_apify = True
    if isinstance(places, dict) and "error" in places:
        raise RuntimeError(places["error"])
    if not isinstance(places, list):
        return []

    details_map = {}
    if not using_apify:
        rows = await asyncio.gather(*[_fetch_details(maps, p) for p in places[:20]])
        details_map = {pid: details for pid, details in rows if pid}

    businesses = []
    now = datetime.datetime.utcnow()
    for place in places[:20]:
        pid = place.get("place_id")
        loc = ((place.get("geometry") or {}).get("location") or {})
        lat = loc.get("lat")
        lng = loc.get("lng")
        if not pid or lat is None or lng is None:
            continue

        details = details_map.get(pid, {})
        existing = db.query(Business).filter(Business.id == pid).first()
        is_new = existing is None
        biz = existing or Business(id=pid, discovered_at=now)

        biz.name = details.get("name") or place.get("name") or biz.name or "Commerce"
        biz.address = details.get("formatted_address") or place.get("vicinity") or biz.address or ""
        biz.latitude = float(lat)
        biz.longitude = float(lng)
        biz.rating = details.get("rating", place.get("rating", 0.0)) or 0.0
        biz.user_ratings_total = details.get("user_ratings_total", place.get("user_ratings_total", 0)) or 0
        biz.website = details.get("website") or place.get("website") or biz.website or ""
        biz.business_phone = details.get("formatted_phone_number") or biz.business_phone
        biz.photos = details.get("photos") or biz.photos or []
        biz.category = details.get("types") or place.get("types") or biz.category or []
        biz.automation_source = f"autopilot:{zone.id}"
        biz.automation_last_scanned_at = now

        score_data = {
            "name": biz.name,
            "address": biz.address,
            "rating": biz.rating,
            "user_ratings_total": biz.user_ratings_total,
            "website": biz.website,
            "business_phone": biz.business_phone,
            "photos": biz.photos,
            "category": biz.category,
            "owner_email": biz.owner_email,
            "owner_phone": biz.owner_phone,
        }
        scores = calculate_scores(score_data, biz.website_audit or None)
        biz.digital_health_score = scores["digital_health"]["score"]
        biz.opportunity_score = scores["opportunity"]["score"]
        biz.opportunity_breakdown = scores["opportunity"]
        if is_new:
            biz.status = "scanned"
            db.add(biz)
        businesses.append(biz)

    db.commit()
    return businesses


async def generate_and_deploy(biz: Business, db, on_progress=None) -> dict[str, Any]:
    def progress(stage: str):
        if on_progress:
            on_progress(stage)
    maps = GoogleMapsService()
    details = await asyncio.to_thread(maps.get_business_details, biz.id)
    if not isinstance(details, dict) or "error" in details:
        details = {}

    biz.photos = details.get("photos", []) or biz.photos or []
    biz.website = details.get("website") or biz.website
    biz.business_phone = details.get("formatted_phone_number") or biz.business_phone
    biz.category = details.get("types", []) or biz.category or []
    biz.status = "processing"
    db.commit()

    data = _business_data(biz, details)
    manager = LocalPulseManager(data)

    progress("design")
    design = await asyncio.to_thread(manager.run_design_crew)
    biz.site_config = design
    db.commit()

    progress("contenu")
    prep = await asyncio.to_thread(manager.run_prep_crew)
    biz.generated_copy = {
        k: prep.get(k, "")
        for k in ["report", "copywriting", "ai_photos", "design"]
    }
    db.commit()

    progress("generation_html")
    build = await asyncio.to_thread(manager.run_build_crew, prep)
    biz.generated_html = build.get("html", "")
    if build.get("site_config"):
        biz.site_config = build["site_config"]
    biz.generated_copy = {
        **(biz.generated_copy or {}),
        "email": build.get("email", ""),
    }
    biz.generated_at = datetime.datetime.utcnow()
    biz.status = "pending_validation"
    db.commit()

    # Autopilot deploy can be disabled independently while keeping generated previews.
    if os.getenv("AUTOPILOT_AUTO_DEPLOY", "true").lower() != "true":
        return {"generated": True, "deployed": False, "email_ready": False}

    if not (os.getenv("VERCEL_API_TOKEN") or "").strip():
        raise RuntimeError("VERCEL_API_TOKEN absent : déploiement automatique impossible.")

    progress("deploiement_vercel")
    result = await asyncio.to_thread(manager.run_deploy_crew, biz.generated_html)
    match = re.search(r"https://[a-zA-Z0-9._\-]+\.vercel\.app", str(result))
    if not match:
        raise RuntimeError(f"Vercel n'a retourné aucune URL : {str(result)[:250]}")

    biz.deployment_url = match.group(0)
    biz.deployed_at = datetime.datetime.utcnow()
    biz.status = "completed"
    db.commit()

    # Regenerate after Vercel deployment so preview + Stripe links are real.
    data = _business_data(biz, details)
    email_manager = LocalPulseManager(data)
    copy_data = biz.generated_copy or {}
    progress("email_final")
    final_email = await asyncio.to_thread(
        email_manager.run_email_only,
        {
            "report": copy_data.get("report", ""),
            "copywriting": copy_data.get("copywriting", ""),
        },
    )
    copy_data["email"] = final_email
    biz.generated_copy = copy_data
    if final_email.strip():
        biz.email_ready_at = datetime.datetime.utcnow()
        biz.email_status = "ready"
    db.commit()

    return {
        "generated": True,
        "deployed": bool(biz.deployment_url),
        "email_ready": bool(final_email.strip()),
    }


async def run_autopilot(trigger: str = "scheduled") -> dict[str, Any]:
    db = SessionLocal()
    run = AutomationRun(
        trigger=trigger,
        status="running",
        started_at=datetime.datetime.utcnow(),
        heartbeat_at=datetime.datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    summary = {
        "run_id": run.id,
        "trigger": trigger,
        "zones": [],
        "selected": [],
        "errors": [],
    }

    try:
        zones = db.query(AutomationZone).filter(AutomationZone.enabled == True).order_by(AutomationZone.id).all()
        run.zones_processed = len(zones)
        db.commit()

        if not zones:
            run.status = "partial"
            run.finished_at = datetime.datetime.utcnow()
            run.summary = {**summary, "message": "Aucune zone de prospection activée."}
            db.commit()
            return run.summary

        already_selected = set()
        for zone in zones:
            zone_info = {"id": zone.id, "name": zone.name, "scanned": 0, "selected": 0}
            summary["zones"].append(zone_info)
            try:
                found = await scan_zone(zone, db)
                zone_info["scanned"] = len(found)
                run.businesses_scanned += len(found)

                candidates = [
                    b for b in found
                    if (b.opportunity_score or 0) >= (zone.min_opportunity_score or 62)
                    and not b.generated_html
                    and b.id not in already_selected
                    and b.status not in ("processing",)
                ]
                candidates.sort(key=lambda b: b.opportunity_score or 0, reverse=True)
                candidates = candidates[: max(0, zone.max_sites_per_run or 0)]
                zone_info["selected"] = len(candidates)
                run.opportunities_selected += len(candidates)
                run.total_selected += len(candidates)
                for candidate in candidates:
                    candidate.automation_selected_at = datetime.datetime.utcnow()
                db.commit()

                for biz in candidates:
                    already_selected.add(biz.id)
                    run.current_index += 1
                    run.current_business_id = biz.id
                    run.current_business_name = biz.name
                    run.current_stage = "demarrage"
                    run.heartbeat_at = datetime.datetime.utcnow()
                    db.commit()

                    def _progress(stage):
                        run.current_stage = stage
                        run.heartbeat_at = datetime.datetime.utcnow()
                        db.commit()

                    try:
                        result = await generate_and_deploy(biz, db, on_progress=_progress)
                        if result["generated"]:
                            run.sites_generated += 1
                        if result["deployed"]:
                            run.sites_deployed += 1
                        if result["email_ready"]:
                            run.emails_ready += 1
                        run.current_stage = "termine"
                        run.heartbeat_at = datetime.datetime.utcnow()
                        db.commit()
                        summary["selected"].append({
                            "id": biz.id,
                            "name": biz.name,
                            "score": biz.opportunity_score,
                            "deployment_url": biz.deployment_url,
                            "email_ready": bool(result["email_ready"]),
                        })
                    except Exception as exc:
                        run.errors_count += 1
                        biz.status = "error"
                        biz.automation_error_at = datetime.datetime.utcnow()
                        run.current_stage = "erreur"
                        run.heartbeat_at = datetime.datetime.utcnow()
                        db.commit()
                        summary["errors"].append({
                            "business_id": biz.id,
                            "name": biz.name,
                            "error": str(exc)[:500],
                        })
            except Exception as exc:
                run.errors_count += 1
                summary["errors"].append({
                    "zone_id": zone.id,
                    "zone": zone.name,
                    "error": str(exc)[:500],
                })

        run.status = "completed" if run.errors_count == 0 else "partial"
        run.current_stage = "termine"
        run.heartbeat_at = datetime.datetime.utcnow()
        run.finished_at = datetime.datetime.utcnow()
        run.summary = summary
        db.commit()
        return {
            **summary,
            "status": run.status,
            "businesses_scanned": run.businesses_scanned,
            "opportunities_selected": run.opportunities_selected,
            "sites_generated": run.sites_generated,
            "sites_deployed": run.sites_deployed,
            "emails_ready": run.emails_ready,
            "errors_count": run.errors_count,
        }
    except Exception as exc:
        run.status = "error"
        run.error = str(exc)[:2000]
        run.finished_at = datetime.datetime.utcnow()
        run.errors_count += 1
        db.commit()
        raise
    finally:
        db.close()
