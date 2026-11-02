"""Voix off de la présentation vidéo (ElevenLabs) et calage des scènes sur la voix.

Une phrase par scène, écrite uniquement à partir des faits du storyboard (même règle que
motion_video : aucune note, aucun client, aucun chiffre inventés). Chaque phrase est
synthétisée séparément, sa durée réelle fixe la durée de sa scène : la vidéo reste
synchronisée quelle que soit la longueur du nom ou des textes.

Optionnelle : sans ELEVENLABS_API_KEY, ou en cas d'erreur, la vidéo sort sans voix.
"""
import os
import re
import subprocess

ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
# « Céline » : voix française féminine, douce et naturelle (validée sur la démo taxi).
DEFAULT_VOICE_ID = "jRlzLbW9YjWmOOOhVWv7"
DEFAULT_MODEL = "eleven_multilingual_v2"

VOICE_LEAD = 0.35   # la voix démarre 0,35 s après le début de la scène (le titre s'affiche d'abord)
VOICE_TAIL = 0.6    # respiration après la phrase avant la transition
MIN_SCENE = {"hook": 4.0, "fiche": 5.0, "avant": 5.0, "apres": 6.0,
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
        elif sid == "avant":
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
        elif sid == "cta":
            text = "Envie d'aller plus loin ? Répondez simplement à ce message."
        else:
            continue
        lines.append({"scene": sid, "text": text})
    return lines


def synthesize(text: str, api_key: str, voice_id: str = DEFAULT_VOICE_ID,
               previous_text: str = "", next_text: str = "", timeout: int = 60) -> bytes:
    """MP3 d'une phrase. previous/next_text gardent une intonation continue entre les phrases."""
    import requests

    payload = {"text": text, "model_id": DEFAULT_MODEL, "language_code": "fr",
               "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
    if previous_text:
        payload["previous_text"] = previous_text
    if next_text:
        payload["next_text"] = next_text
    resp = requests.post(ELEVEN_URL.format(voice_id=voice_id),
                         params={"output_format": "mp3_44100_128"},
                         headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                         json=payload, timeout=timeout)
    resp.raise_for_status()
    if not resp.content:
        raise RuntimeError("ElevenLabs a renvoyé un fichier vide")
    return resp.content


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
        duration = max(MIN_SCENE.get(s["id"], s["duration"]),
                       round(VOICE_LEAD + need + VOICE_TAIL, 2) if need else s["duration"])
        out.append(dict(s, start=round(start, 2), duration=duration))
        start += duration
    return out


def voice_cues(scenes: list[dict]) -> dict[str, float]:
    """Instant de départ de la voix pour chaque scène (après retime)."""
    return {s["id"]: s["start"] + VOICE_LEAD for s in scenes}


def generate_voiceover(scenes: list[dict], workdir: str, api_key: str | None = None,
                       voice_id: str | None = None) -> tuple[list[dict], list[tuple[float, str]]]:
    """Synthétise le script, recale le storyboard et renvoie (scènes recalées, [(départ, mp3)]).

    Lève une exception en cas d'échec : l'appelant décide de continuer sans voix.
    """
    api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY absente")
    voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID") or DEFAULT_VOICE_ID
    script = build_script(scenes)
    files, durations = {}, {}
    for i, line in enumerate(script):
        prev_text = script[i - 1]["text"] if i else ""
        next_text = script[i + 1]["text"] if i + 1 < len(script) else ""
        path = os.path.join(workdir, f"vo_{i:02d}_{line['scene']}.mp3")
        with open(path, "wb") as fh:
            fh.write(synthesize(line["text"], api_key, voice_id, prev_text, next_text))
        files[line["scene"]] = path
        durations[line["scene"]] = audio_duration(path)
    timed = retime(scenes, durations)
    cues = voice_cues(timed)
    return timed, [(cues[sid], path) for sid, path in files.items()]
