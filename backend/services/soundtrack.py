"""Bande-son de la présentation vidéo : musique générée + mixage avec la voix off.

La musique est synthétisée localement (128 BPM : kick, snare, charleston, basse, nappe,
« whoosh » sur chaque transition) : aucun droit d'auteur, aucune API. Le mixage passe par
le ffmpeg embarqué (imageio-ffmpeg) et baisse automatiquement la musique quand la voix
parle (sidechain).
"""
import array
import math
import os
import random
import subprocess
import wave

SAMPLE_RATE = 22050
BPM = 128


def music_bed(duration: float, transitions: list[float], sample_rate: int = SAMPLE_RATE) -> bytes:
    """WAV mono 16 bits de `duration` secondes, avec un souffle sur chaque transition."""
    n = int(duration * sample_rate)
    out = [0.0] * n
    beat = 60 / BPM

    def add(samples, at):
        i0 = int(at * sample_rate)
        for k, v in enumerate(samples):
            i = i0 + k
            if 0 <= i < n:
                out[i] += v

    sr = sample_rate
    kick = [math.sin(2 * math.pi * (50 + 120 * math.exp(-k / sr * 30)) * k / sr) * math.exp(-k / sr * 9)
            for k in range(int(0.35 * sr))]
    rng = random.Random(1)
    hat = [rng.uniform(-1, 1) * 0.22 * math.exp(-k / sr * 90) for k in range(int(0.05 * sr))]
    rng = random.Random(2)
    snare = [rng.uniform(-1, 1) * 0.4 * math.exp(-k / sr * 22) for k in range(int(0.2 * sr))]

    t, k = 0.0, 0
    while t < duration - 1.5:
        if t >= 1.0:
            add(kick, t)
        if t >= 3.0:
            if k % 2:
                add(snare, t)
            add(hat, t + beat / 2)
        t += beat
        k += 1

    notes = (55.0, 55.0, 65.4, 49.0)
    bar = int(beat * 4 * sr)
    for i in range(n):
        f = notes[(i // bar) % 4]
        seg = (i % bar) / sr
        bass = (1 if math.sin(2 * math.pi * f * seg) >= 0 else -1) * 0.11 * min(1.0, seg * 20)
        ts = i / sr
        pad = (math.sin(2 * math.pi * 220 * ts) + math.sin(2 * math.pi * 277.2 * ts)
               + math.sin(2 * math.pi * 329.6 * ts)) * 0.035
        out[i] += bass * min(1.0, ts) + pad

    rng = random.Random(3)
    whoosh_len = int(0.6 * sr)
    for at in transitions:
        add([rng.uniform(-1, 1) * 0.12 * math.sin(math.pi * j / whoosh_len) for j in range(whoosh_len)],
            max(0.0, at - 0.3))

    fade = 1.5 * sr
    peak = max(1e-9, max(abs(v) for v in out))
    pcm = array.array("h", (int(32767 * 0.9 * v / peak * min(1.0, (n - i) / fade)) for i, v in enumerate(out)))
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def mix_into_video(video_path: str, music_wav: str, voice: list[tuple[float, str]], out_path: str,
                   music_volume: float = 0.22) -> None:
    """Ajoute musique (+ voix si fournie) à la vidéo, sans ré-encoder l'image."""
    import imageio_ffmpeg

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", video_path, "-i", music_wav]
    for _, path in voice:
        cmd += ["-i", path]
    parts = [f"[1:a]volume={music_volume},aresample=44100[music]"]
    if voice:
        for i, (start, _) in enumerate(voice):
            ms = int(start * 1000)
            parts.append(f"[{i + 2}:a]aresample=44100,adelay={ms}|{ms}[v{i}]")
        labels = "".join(f"[v{i}]" for i in range(len(voice)))
        parts.append(f"{labels}amix=inputs={len(voice)}:normalize=0,volume=1.5,asplit[voice][key]")
        parts.append("[music][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[ducked]")
        parts.append("[ducked][voice]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]")
    else:
        parts.append("[music]anull[a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not os.path.exists(out_path):
        raise RuntimeError(f"mixage audio impossible : {proc.stderr.strip()[-300:]}")
