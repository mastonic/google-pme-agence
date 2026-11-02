"""Format des fichiers envoyés à l'API Vercel (texte ou binaire en base64)."""
import base64


def vercel_file(name: str, content) -> dict:
    if isinstance(content, bytes):
        return {"file": name, "data": base64.b64encode(content).decode("ascii"), "encoding": "base64"}
    return {"file": name, "data": content}
