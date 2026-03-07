import os
import fal_client
from crewai.tools import BaseTool

class FalFluxTool(BaseTool):
    name: str = "Fal Flux Image Generator"
    description: str = "Génère des images ultra-réalistes pour le site web via Flux.1 sur Fal.ai."

    def _run(self, prompt: str) -> str:
        # S'assurer que la clé API est définie
        if not os.environ.get("FAL_KEY"):
            os.environ["FAL_KEY"] = os.environ.get("FAL_API_KEY", "")

        try:
            handler = fal_client.submit(
                "fal-ai/flux/schnell",
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
