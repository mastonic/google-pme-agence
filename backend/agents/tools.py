import os
import requests
from dotenv import load_dotenv
from crewai.tools import BaseTool
import fal_client

load_dotenv()

class VercelDeployTool(BaseTool):
    name: str = "Vercel Dynamic Deployer"
    description: str = "Déploie un site OnePage HTML/Tailwind sur Vercel et retourne l'URL publique."

    def _run(self, html_content: str, project_name: str) -> str:
        """
        Prend le code HTML généré par l'IA et le déploie instantanément.
        """
        # Nettoyer les balises markdown si l'IA en a généré
        html_content = html_content.strip()
        if html_content.startswith("```html"):
            html_content = html_content[7:]
        elif html_content.startswith("```"):
            html_content = html_content[3:]
        if html_content.endswith("```"):
            html_content = html_content[:-3]
        html_content = html_content.strip()

        VERCEL_TOKEN = os.environ.get("VERCEL_API_TOKEN") # Note: was VERCEL_TOKEN in user prompt, using existing dot env
        TEAM_ID = os.environ.get("VERCEL_TEAM_ID")
        
        url = "https://api.vercel.com/v13/deployments"
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}",
            "Content-Type": "application/json"
        }

        # Structure du déploiement (Fichiers du site)
        import re
        clean_name = re.sub(r'[^a-zA-Z0-9-]', '', project_name.replace(" ", "-")).lower()
        payload = {
            "name": clean_name,
            "files": [
                {
                    "file": "index.html",
                    "data": html_content
                }
            ],
            "projectSettings": {
                "framework": None # Simple HTML statique
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            deployment_url = f"https://{data['url']}"
            return f"Succès ! Le site est en ligne : {deployment_url}"
        else:
            return f"Erreur lors du déploiement : {response.text}"

class FalFluxTool(BaseTool):
    name: str = "Fal Flux Image Generator"
    description: str = "Génère des images ultra-réalistes pour le site web via Flux.1 sur Fal.ai."

    def _run(self, prompt: str) -> str:
        """
        Envoie le prompt à Fal.ai et retourne l'URL de l'image générée.
        """
        os.environ["FAL_KEY"] = os.environ.get("FAL_API_KEY", "")

        try:
            handler = fal_client.submit(
                "fal-ai/flux/schnell", # Version ultra-rapide et propre
                arguments={
                    "prompt": prompt,
                    "image_size": "landscape_4_3",
                    "num_inference_steps": 4,
                    "enable_safety_checker": True
                }
            )

            result = handler.get()
            if "images" in result and len(result["images"]) > 0:
                image_url = result["images"][0]["url"]
                return f"Image générée avec succès : {image_url}"
            else:
                return "Erreur lors de la génération de l'image (aucune image retournée)."
        except Exception as e:
            return f"Erreur lors de l'appel à Fal.ai : {str(e)}"

class GmailDraftTool(BaseTool):
    name: str = "Gmail Draft Creator"
    description: str = "Prépare un brouillon d'email dans Gmail pour la prospection. L'email ne sera jamais envoyé sans validation humaine."

    def _run(self, email_body: str, subject: str = "Votre nouveau site web") -> str:
        """
        Simule la création d'un draft Gmail. En production, cela utiliserait l'API Google Workspace.
        Ici, il prépare le payload final pour l'interface de validation.
        """
        import json
        draft_payload = {
            "subject": subject,
            "body": email_body,
            "status": "ready_for_review"
        }
        # Le retour indique que le draft est prêt
        return f"Gmail Draft Ready: {json.dumps(draft_payload)}"
