import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GoogleMapsService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    def search_nearby_businesses(self, lat, lng, radius=500, type="establishment"):
        """
        Search for businesses around a specific location using Places API (New).
        """
        if not self.api_key:
            return {"error": "Google Maps API Key not configured"}

        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.name,places.id,places.displayName,places.location,places.shortFormattedAddress,places.rating,places.userRatingCount"
        }
        body = {
            # Let's include some generic business types if type is establishment
            "includedTypes": ["store", "restaurant", "cafe", "beauty_salon", "hair_care", "real_estate_agency", "lawyer", "dentist", "doctor"] if type == "establishment" else [type],
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": float(lat),
                        "longitude": float(lng)
                    },
                    "radius": float(radius)
                }
            }
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            data = response.json()
            
            if response.status_code != 200:
                print("Google API Error:", data)
                return {"error": data.get("error", {}).get("message", "API Error")}
                
            places = data.get("places", [])
            mapped_results = []
            
            for p in places:
                # Map back to legacy format for main.py compatibility
                mapped_results.append({
                    "place_id": p.get("id"),
                    "name": p.get("displayName", {}).get("text", ""),
                    "vicinity": p.get("shortFormattedAddress", ""),
                    "geometry": {
                        "location": {
                            "lat": p.get("location", {}).get("latitude"),
                            "lng": p.get("location", {}).get("longitude")
                        }
                    },
                    "rating": p.get("rating", 0.0),
                    "user_ratings_total": p.get("userRatingCount", 0)
                })
                
            return mapped_results

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def get_business_details(self, place_id):
        """
        Get detailed info for a specific business using Places API (New).
        """
        if not self.api_key:
            return {"error": "Google Maps API Key not configured"}

        # Format is slightly different for details: GET https://places.googleapis.com/v1/places/{placeId}
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,rating,userRatingCount,websiteUri,reviews,photos,types"
        }

        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if response.status_code != 200:
                print("Google API Error:", data)
                return {"error": data.get("error", {}).get("message", "API Error")}
                
            # Build photo URLs
            photos = []
            for photo in data.get("photos", [])[:5]:
                name = photo.get("name")
                if name:
                    photo_url = f"https://places.googleapis.com/v1/{name}/media?maxHeightPx=800&maxWidthPx=1200&key={self.api_key}"
                    photos.append(photo_url)

            # Map back to legacy format for main.py compatibility
            return {
                "name": data.get("displayName", {}).get("text", ""),
                "formatted_address": data.get("formattedAddress", ""),
                "rating": data.get("rating", 0.0),
                "user_ratings_total": data.get("userRatingCount", 0),
                "website": data.get("websiteUri", ""),
                "photos": photos,
                "types": data.get("types", [])
            }

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    def geocode(self, address):
        """
        Convert an address or zip code into lat/lng.
        """
        if not self.api_key:
            return {"error": "Google Maps API Key not configured"}

        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if response.status_code != 200 or data.get("status") != "OK":
                print("Google Geocoding Error:", data)
                return {"error": data.get("error_message", "Geocoding failed")}

            location = data["results"][0]["geometry"]["location"]
            return {
                "lat": location["lat"],
                "lng": location["lng"]
            }

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
