import os
import requests
from dotenv import load_dotenv
from crewai.tools import BaseTool
import fal_client

load_dotenv()

class VercelDeployTool(BaseTool):
    name: str = "Vercel Dynamic Deployer"
    description: str = "Déploie un site statique HTML sur Vercel et retourne son URL publique."

    def _run(self, html_content: str, project_name: str) -> str:
        """Create/update a static Vercel project from a single index.html.

        Deployment failures raise an exception so Local Pulse never marks a
        failed deployment as completed.
        """
        import re
        import unicodedata

        html_content = (html_content or "").strip()
        if html_content.startswith("```html"):
            html_content = html_content[7:]
        elif html_content.startswith("```"):
            html_content = html_content[3:]
        if html_content.endswith("```"):
            html_content = html_content[:-3]
        html_content = html_content.strip()
        if not html_content:
            raise RuntimeError("Vercel: contenu HTML vide")

        token = (os.environ.get("VERCEL_API_TOKEN") or "").strip()
        team_id = (os.environ.get("VERCEL_TEAM_ID") or "").strip()
        if not token:
            raise RuntimeError(
                "Vercel: VERCEL_API_TOKEN absent du backend. "
                "Ajoutez le secret au service Cloud Run."
            )

        normalized = unicodedata.normalize("NFKD", project_name or "local-pulse-site")
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        clean_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", normalized).strip("-._").lower()
        clean_name = re.sub(r"-{2,}", "-", clean_name)[:90] or "local-pulse-site"

        url = "https://api.vercel.com/v13/deployments"
        params = {"teamId": team_id} if team_id else None
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "name": clean_name,
            "target": "production",
            "files": [{"file": "index.html", "data": html_content}],
            "projectSettings": {"framework": None},
        }

        try:
            response = requests.post(
                url,
                params=params,
                headers=headers,
                json=payload,
                timeout=45,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"Vercel: erreur réseau: {exc}") from exc

        try:
            data = response.json()
        except ValueError:
            data = {"message": response.text[:500]}

        if response.status_code not in (200, 201):
            message = (
                data.get("error", {}).get("message")
                if isinstance(data.get("error"), dict)
                else data.get("message") or data.get("error") or response.text
            )
            raise RuntimeError(
                f"Vercel API {response.status_code}: {str(message)[:500]}"
            )

        deployment_host = data.get("url")
        if not deployment_host:
            raise RuntimeError(
                f"Vercel: déploiement accepté mais aucune URL retournée ({data.get('id', 'sans id')})"
            )

        return f"https://{deployment_host}"


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
