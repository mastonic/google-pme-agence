import os
import requests
import hashlib
from dotenv import load_dotenv

load_dotenv()

ACTOR_ID = "nwua9Gu5YkAT1ZZIHantLQ"  # Apify Google Maps Scraper


class ApifyMapsService:
    def __init__(self):
        self.token = os.getenv("APIFY_TOKEN")

    def _available(self) -> bool:
        return bool(self.token)

    def search_nearby_businesses(self, lat: float, lng: float, radius: int = 500) -> list | dict:
        if not self._available():
            return {"error": "APIFY_TOKEN non configuré"}

        print(f"🕷️  Apify Maps : scan à ({lat}, {lng}) rayon {radius}m")

        # Radius in km for Apify (min 0.5 km)
        radius_km = max(0.5, round(radius / 1000, 2))

        payload = {
            "searchStringsArray": ["commerce local"],
            "lat": lat,
            "lng": lng,
            "zoom": 15,
            "radius": radius_km,
            "maxCrawledPlaces": 20,
            "language": "fr",
            "exportPlaceUrls": False,
            "includeHistogram": False,
            "includeOpeningHours": False,
            "includePeopleAlsoSearch": False,
        }

        url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
        params = {"token": self.token, "timeout": 120, "memory": 512}

        try:
            response = requests.post(url, json=payload, params=params, timeout=130)
            if response.status_code != 200:
                print(f"❌ Apify erreur {response.status_code}: {response.text[:200]}")
                return {"error": f"Apify error {response.status_code}"}

            places = response.json()
            print(f"✅ Apify : {len(places)} résultats")
            return [self._normalize(p) for p in places if p.get("title")]

        except requests.Timeout:
            print("⏱️  Apify timeout (> 130s)")
            return {"error": "Apify timeout — réessayez ou configurez une clé Google Maps"}
        except Exception as e:
            print(f"💥 Apify erreur inattendue : {e}")
            return {"error": str(e)}

    def get_business_details(self, place_id: str) -> dict:
        """Apify ne supporte pas le lookup par place_id — retourne un dict vide compatible."""
        return {}

    @staticmethod
    def _normalize(p: dict) -> dict:
        """Convert Apify Google Maps result to the same shape as Google Places API."""
        title = p.get("title", "")
        # Build a stable pseudo place_id from the Google Maps URL if present
        url = p.get("url", "") or p.get("website", "") or title
        place_id = "apify_" + hashlib.md5(url.encode()).hexdigest()[:16]

        return {
            "place_id": place_id,
            "name": title,
            "vicinity": p.get("address", ""),
            "geometry": {
                "location": {
                    "lat": p.get("location", {}).get("lat") or p.get("lat"),
                    "lng": p.get("location", {}).get("lng") or p.get("lng"),
                }
            },
            "rating": p.get("totalScore") or p.get("rating") or 0.0,
            "user_ratings_total": p.get("reviewsCount") or 0,
            "website": p.get("website", ""),
        }
