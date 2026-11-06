"""Voix off de la présentation vidéo (Google Cloud Text-to-Speech) et calage des scènes sur la voix.

Une phrase par scène, écrite uniquement à partir des faits du storyboard (même règle que
motion_video : aucune note, aucun client, aucun chiffre inventés). Chaque phrase est
synthétisée séparément, sa durée réelle fixe la durée de sa scène : la vidéo reste
synchronisée quelle que soit la longueur du nom ou des textes.

Authentification : sur Cloud Run, le compte de service du conteneur (aucune clé, il faut
seulement activer l'API « Cloud Text-to-Speech » dans le projet). En local, GOOGLE_TTS_API_KEY.
Voix : GOOGLE_TTS_VOICE (facultatif), voix féminine Chirp 3 HD par défaut.

Optionnelle : en cas d'erreur (API non activée, pas de credentials), la vidéo sort sans voix.
"""
import base64
import os
import re
import subprocess

TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
METADATA_TOKEN_URL = ("http://metadata.google.internal/computeMetadata/v1/"
                      "instance/service-accounts/default/token")
# Voix féminine française « Chirp 3 HD » (la gamme la plus naturelle de Google).
DEFAULT_VOICE = "fr-FR-Chirp3-HD-Aoede"

VOICE_LEAD = 0.35   # la voix démarre 0,35 s après le début de la scène (le titre s'affiche d'abord)
VOICE_TAIL = 0.6    # respiration après la phrase avant la transition
MIN_SCENE = {"galerie": 4.4, "hook": 4.0, "fiche": 5.0, "avant": 5.0, "apres": 6.0,
             "avantages": 5.0, "packs": 5.0, "cta": 4.0}


def _rating_fr(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")


def build_script(scenes: list[dict]) -> list[dict]:
    """Une phrase par scène, à partir des seuls champs du storyboard."""
    lines = []
    for s in scenes:
        sid = s["id"]
        if sid == "hook":
            name = s.get("name") or "votre commerce"
            first = (s.get("first") or "").strip()
            text = f"{first + ', v' if first else 'V'}oici ce que nous avons préparé pour {name}."
        elif sid == "fiche":
            if s.get("rating") and s.get("reviews"):
                text = (f"Votre fiche Google affiche {_rating_fr(float(s['rating']))} sur 5, "
                        f"avec {int(s['reviews'])} avis.")
            else:
                text = "Aujourd'hui, votre fiche Google reste discrète."
        elif sid == "avant" and "bullets" in s:
            if s.get("bullets") and s["bullets"][0].startswith("Aucun site"):
                text = "Sans site web, vous passez à côté des clients qui vous cherchent sur Google."
            else:
                text = "Votre site actuel peut faire beaucoup plus pour vous."
        elif sid == "apres":
            text = "Voici votre nouveau site : moderne, rapide, et prêt à recevoir vos clients."
        elif sid == "avantages":
            text = ("Vous êtes visible sur Google, vos clients vous contactent en un clic, "
                    "et vos avis sont mis en valeur.")
        elif sid == "packs":
            prices = [int(p["price"]) for p in s.get("packs", []) if p.get("price")]
            text = (f"Trois formules, à partir de {min(prices)} euros par mois." if prices
                    else "Choisissez la formule qui vous ressemble.")
        elif sid == "cta" and "min_price" in s:  # showreel avant/après
            text = "Vous voulez aller plus loin ? " + (
                f"Nos formules commencent à {s['min_price']} euros par mois. " if s["min_price"] else "") \
                + "Répondez simplement à ce message."
        elif sid == "cta":
            text = "Envie d'aller plus loin ? Répondez simplement à ce message."
        # ── Scènes du showreel avant/après (showreel.py) ──
        elif sid == "avant":  # showreel (l'« avant » Pillow porte « bullets », géré plus haut)
            name = s.get("name") or "votre commerce"
            lead = f"{s['first']}, " if s.get("first") else ""
            text = (f"{lead}voici le site actuel de {name}." if s.get("website")
                    else f"{lead}aujourd'hui, {name} n'a pas encore de site web.")
            text = text[0].upper() + text[1:]
        elif sid == "cout":
            text = ("Un site daté, ce sont des clients qui hésitent, et qui appellent ailleurs." if s.get("website")
                    else "Vos clients vous cherchent sur Google, mais ne trouvent aucun site pour vous contacter.")
            if s.get("reviews"):
                text += f" Et vos {int(s['reviews'])} avis restent cachés."
        elif sid == "refonte":
            text = "Alors… on a tout refait."
        elif sid == "parcours":
            text = {"artisan": "Une urgence ? Vos clients vous appellent ou demandent un devis en un clic.",
                    "automotive": "Vos clients prennent rendez-vous et demandent un devis en quelques secondes.",
                    "transport": "Vos clients réservent leur course en trente secondes, même la nuit.",
                    }.get(s.get("sector"), "Vos clients vous contactent en un clic, depuis leur téléphone.")
        elif sid == "galerie":
            text = ("Vos propres photos sont mises en valeur, pour donner envie dès le premier regard."
                    if s.get("count") else "Vos photos sont mises en valeur.")
        elif sid == "comparatif":
            text = "Avant… après. La différence saute aux yeux."
        elif sid == "pourquoi":
            text = (f"Avec {s.get('brand') or 'nous'}, tout est clé en main : le site, Google, "
                    "les demandes de vos clients, et le suivi.")
        else:
            continue
        lines.append({"scene": sid, "text": text})
    return lines


def _access_token(timeout: int = 5) -> str:
    """Jeton OAuth du compte de service Cloud Run (serveur de métadonnées), sans dépendance."""
    import requests

    resp = requests.get(METADATA_TOKEN_URL, headers={"Metadata-Flavor": "Google"}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["access_token"]


def synthesize(text: str, voice: str = DEFAULT_VOICE, api_key: str = "", token: str = "",
               timeout: int = 60) -> bytes:
    """MP3 d'une phrase via Google Cloud Text-to-Speech.

    Authentification : clé `api_key` si fournie (usage local), sinon jeton OAuth `token`.
    """
    import requests

    payload = {
        "input": {"text": text},
        "voice": {"languageCode": voice[:5], "name": voice},
        "audioConfig": {"audioEncoding": "MP3", "sampleRateHertz": 44100},
    }
    headers = {"Content-Type": "application/json"}
    params = {}
    if api_key:
        params["key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.post(TTS_URL, params=params, headers=headers, json=payload, timeout=timeout)
    if resp.status_code >= 400:
        raise RuntimeError(f"Google Text-to-Speech {resp.status_code} : {resp.text[:300]}")
    audio = resp.json().get("audioContent", "")
    if not audio:
        raise RuntimeError("Google Text-to-Speech a renvoyé un fichier vide")
    return base64.b64decode(audio)


def audio_duration(path: str) -> float:
    """Durée d'un fichier audio, lue par le ffmpeg embarqué (pas de ffprobe dans imageio-ffmpeg)."""
    import imageio_ffmpeg

    proc = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", path],
                          capture_output=True, text=True)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not match:
        raise RuntimeError(f"durée illisible pour {os.path.basename(path)}")
    h, m, s = match.groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def retime(scenes: list[dict], voice_durations: dict[str, float]) -> list[dict]:
    """Recalcule start/duration : chaque scène dure au moins sa phrase + respirations.

    Les animations sont exprimées en proportion de la scène (p = t/durée), un étirement
    ne casse donc rien. Retourne une nouvelle liste ; les starts restent contigus.
    """
    out, start = [], 0.0
    for s in scenes:
        need = voice_durations.get(s["id"], 0.0)
        duration = max(s.get("min") or MIN_SCENE.get(s["id"], s["duration"]),
                       round(VOICE_LEAD + need + VOICE_TAIL, 2) if need else s["duration"])
        out.append(dict(s, start=round(start, 2), duration=duration))
        start += duration
    return out


def voice_cues(scenes: list[dict]) -> dict[str, float]:
    """Instant de départ de la voix pour chaque scène (après retime)."""
    return {s["id"]: s["start"] + VOICE_LEAD for s in scenes}


def generate_voiceover(scenes: list[dict], workdir: str, api_key: str | None = None,
                       voice: str | None = None) -> tuple[list[dict], list[tuple[float, str]]]:
    """Synthétise le script, recale le storyboard et renvoie (scènes recalées, [(départ, mp3)]).

    Lève une exception en cas d'échec : l'appelant décide de continuer sans voix.
    """
    api_key = api_key if api_key is not None else os.environ.get("GOOGLE_TTS_API_KEY", "").strip()
    token = "" if api_key else _access_token()
    voice = voice or os.environ.get("GOOGLE_TTS_VOICE", "").strip() or DEFAULT_VOICE
    script = build_script(scenes)
    files, durations = {}, {}
    for i, line in enumerate(script):
        path = os.path.join(workdir, f"vo_{i:02d}_{line['scene']}.mp3")
        with open(path, "wb") as fh:
            fh.write(synthesize(line["text"], voice, api_key=api_key, token=token))
        files[line["scene"]] = path
        durations[line["scene"]] = audio_duration(path)
    timed = retime(scenes, durations)
    cues = voice_cues(timed)
    return timed, [(cues[sid], path) for sid, path in files.items()]
