#!/usr/bin/env python3
"""Collect evidence (transcripts, frames, metadata) for a batch of videos.

Sources can be: video URLs, playlist/channel URLs (expanded with yt-dlp),
local video files, folders of videos, or .txt files listing any of these
(one per line, '#' for comments).

For every video this runs the bundled `watch` skill and stores its report in
<workspace>/raw/NNN-<slug>.md, then writes <workspace>/index.json with a
status per video so the run can be resumed (already-collected videos are
skipped unless --force).

Usage:
  collect.py WORKSPACE SOURCE [SOURCE ...] [--detail transcript|efficient|balanced]
             [--limit N] [--sub-lang fr] [--force] [--engine auto|local|gemini]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
HERE = Path(__file__).resolve().parent
WATCH = HERE.parent.parent / "watch" / "scripts" / "watch.py"

GEMINI_QUESTION = (
    "Extract ALL the knowledge taught in this video so it can be turned into a "
    "reference guide. Give, with timestamps: the main thesis; every framework, "
    "method or step-by-step process (keep the steps); concrete numbers, "
    "benchmarks and examples; tools mentioned; mistakes to avoid; and what is "
    "shown on screen (slides, diagrams, dashboards, text) that is not said aloud."
)


def slugify(text: str, maxlen: int = 50) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return (text[:maxlen].strip("-")) or "video"


def is_url(s: str) -> bool:
    return bool(re.match(r"^https?://", s.strip(), re.I))


def expand_url(url: str) -> list[dict]:
    """Expand playlists/channels into individual video entries."""
    looks_multi = any(k in url for k in ("list=", "/playlist", "/channel/", "/@", "/c/", "/user/"))
    if not looks_multi:
        return [{"source": url, "title": None}]
    try:
        out = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-single-json", "--no-warnings", url],
            capture_output=True, text=True, timeout=300, check=True,
        ).stdout
        data = json.loads(out)
    except (subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"[collect] could not expand {url}: {exc}; treating as one video", file=sys.stderr)
        return [{"source": url, "title": None}]
    entries = []
    for e in data.get("entries") or []:
        if not e:
            continue
        vurl = e.get("url") or e.get("webpage_url")
        if vurl and not is_url(vurl) and e.get("id"):
            vurl = f"https://www.youtube.com/watch?v={e['id']}"
        if vurl:
            entries.append({"source": vurl, "title": e.get("title")})
    print(f"[collect] {url} -> {len(entries)} videos", file=sys.stderr)
    return entries or [{"source": url, "title": None}]


def expand(sources: list[str]) -> list[dict]:
    items: list[dict] = []
    for s in sources:
        s = s.strip()
        if not s or s.startswith("#"):
            continue
        p = Path(s).expanduser()
        if is_url(s):
            items.extend(expand_url(s))
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.suffix.lower() in VIDEO_EXT:
                    items.append({"source": str(f.resolve()), "title": f.stem})
        elif p.is_file() and p.suffix.lower() == ".txt":
            items.extend(expand(p.read_text(encoding="utf-8").splitlines()))
        elif p.is_file():
            items.append({"source": str(p.resolve()), "title": p.stem})
        else:
            print(f"[collect] skipped (not found): {s}", file=sys.stderr)
    seen, unique = set(), []
    for it in items:
        if it["source"] not in seen:
            seen.add(it["source"])
            unique.append(it)
    return unique


def report_title(report: str) -> str | None:
    m = re.search(r"^#\s+(.+)$", report, re.M)
    return m.group(1).strip() if m else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace")
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--detail", default="transcript", choices=["transcript", "efficient", "balanced"])
    ap.add_argument("--engine", default="auto", choices=["auto", "local", "gemini"])
    ap.add_argument("--sub-lang", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--timeout", type=int, default=1200, help="seconds per video")
    args = ap.parse_args()

    if not WATCH.exists():
        print(f"[collect] watch skill not found at {WATCH}", file=sys.stderr)
        return 2

    ws = Path(args.workspace).expanduser().resolve()
    raw, work = ws / "raw", ws / "work"
    raw.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    index_path = ws / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {"videos": []}
    by_source = {v["source"]: v for v in index["videos"]}

    items = expand(args.sources)
    if args.limit:
        items = items[: args.limit]
    print(f"[collect] {len(items)} video(s) to process", file=sys.stderr)

    for it in items:
        entry = by_source.get(it["source"])
        if entry and entry.get("status") == "ok" and not args.force:
            print(f"[collect] skip (done): {entry['file']}", file=sys.stderr)
            continue
        if not entry:
            n = len(index["videos"]) + 1
            entry = {"n": n, "source": it["source"], "title": it.get("title"), "status": "pending"}
            index["videos"].append(entry)
            by_source[it["source"]] = entry

        cmd = [sys.executable, str(WATCH), it["source"], "--detail", args.detail,
               "--engine", args.engine, "--out-dir", str(work), "--question", GEMINI_QUESTION]
        if args.sub_lang:
            cmd += ["--sub-lang", args.sub_lang]
        print(f"[collect] [{entry['n']}] {it['source']}", file=sys.stderr)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
            report, stderr = res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            report, stderr = "", "timeout"
            res = None

        title = report_title(report) or entry.get("title") or "video"
        entry["title"] = title
        fname = f"{entry['n']:03d}-{slugify(title)}.md"
        if entry.get("file") and entry["file"] != fname:
            (raw / entry["file"]).unlink(missing_ok=True)
        entry["file"] = fname

        has_transcript = bool(re.search(r"\*\*Transcript:\*\*\s+\d+ segments", report))
        has_frames = bool(re.search(r"\*\*Frames:\*\*\s+[1-9]\d* selected", report))
        has_gemini = "## Answer (from Gemini)" in report
        entry["evidence"] = {"transcript": has_transcript, "frames": has_frames, "gemini": has_gemini}
        if report.strip() and (has_transcript or has_frames or has_gemini):
            entry["status"] = "ok"
        else:
            entry["status"] = "failed"
            entry["error"] = (stderr or "no evidence")[-800:]
        (raw / fname).write_text(
            f"<!-- source: {it['source']} -->\n" + (report or f"# {title}\n\n_No report._\n\n```\n{stderr[-2000:]}\n```\n"),
            encoding="utf-8",
        )
        index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[collect]   -> {entry['status']} {entry['evidence']}", file=sys.stderr)

    # Frames are kept only for visual runs; transcript-only work dirs are dropped.
    if args.detail == "transcript":
        shutil.rmtree(work, ignore_errors=True)

    ok = sum(v["status"] == "ok" for v in index["videos"])
    failed = [v for v in index["videos"] if v["status"] != "ok"]
    print(json.dumps({"workspace": str(ws), "ok": ok, "failed": len(failed),
                      "failed_sources": [v["source"] for v in failed]}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
