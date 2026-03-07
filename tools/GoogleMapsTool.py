import os
import json
from crewai.tools import BaseTool
from backend.services.google_maps import GoogleMapsService

class GoogleMapsTool(BaseTool):
    name: str = "Google Maps Data Scraper"
    description: str = "Extraire les informations détaillées d'un commerce (adresse, note, avis, site web) à partir de son Place ID."

    def _run(self, place_id: str) -> str:
        """
        Récupère les détails d'un commerce via l'API Google Maps.
        """
        service = GoogleMapsService()
        details = service.get_business_details(place_id)
        
        if "error" in details:
            return f"Erreur lors de la récupération des données Google Maps : {details['error']}"
        
        return json.dumps(details, indent=2, ensure_ascii=False)
