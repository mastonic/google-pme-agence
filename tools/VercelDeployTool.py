import requests
import os
from crewai.tools import BaseTool

class VercelDeployTool(BaseTool):
    name: str = "Vercel Deploy Tool"
    description: str = "Déploie un site OnePage HTML/Tailwind sur Vercel et retourne l'URL publique."

    def _run(self, html_content: str, project_name: str = "local-pulse-demo") -> str:
        # Nettoyer les balises markdown si l'IA en a généré
        html_content = html_content.strip()
        if html_content.startswith("```html"):
            html_content = html_content[7:]
        elif html_content.startswith("```"):
            html_content = html_content[3:]
        if html_content.endswith("```"):
            html_content = html_content[:-3]
        html_content = html_content.strip()

        VERCEL_TOKEN = os.environ.get("VERCEL_API_TOKEN")
        TEAM_ID = os.environ.get("VERCEL_TEAM_ID")
        
        url = "https://api.vercel.com/v13/deployments"
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "name": project_name.replace(" ", "-").lower(),
            "files": [
                {
                    "file": "index.html",
                    "data": html_content
                }
            ],
            "projectSettings": {
                "framework": None
            }
        }

        if TEAM_ID:
            url += f"?teamId={TEAM_ID}"

        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            deployment_url = f"https://{data['url']}"
            return f"Succès ! Le site est en ligne : {deployment_url}"
        else:
            return f"Erreur lors du déploiement : {response.text}"
