import requests
import os
from dotenv import load_dotenv

load_dotenv()

class VercelService:
    def __init__(self):
        self.api_token = os.getenv("VERCEL_API_TOKEN")
        self.team_id = os.getenv("VERCEL_TEAM_ID") # Optional
        self.base_url = "https://api.vercel.com"

    def deploy_website(self, project_name, files_dict):
        """
        Deploy a project to Vercel. 
        files_dict should be mapping from filePath to content.
        """
        if not self.api_token:
            return {"error": "Vercel API Token not configured"}

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        # Simplified deployment logic (Note: Vercel deployment usually requires more steps/CLI)
        # This is a placeholder for the API orchestration logic
        payload = {
            "name": project_name,
            "files": [
                {"file": path, "data": content} for path, content in files_dict.items()
            ],
            "projectSettings": {
                "framework": None
            }
        }

        url = f"{self.base_url}/v13/deployments"
        if self.team_id:
            url += f"?teamId={self.team_id}"

        response = requests.post(url, headers=headers, json=payload)
        return response.json()
