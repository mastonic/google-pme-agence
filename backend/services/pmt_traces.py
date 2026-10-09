"""Traces de géolocalisation des boîtiers : import, kilométrage, rattachement.

Il n'existe pas de format public commun : le fichier de traces du cahier des
charges de l'Assurance maladie est réservé aux logiciels certifiés. Les
fournisseurs de boîtiers exportent surtout en GPX (standard), en CSV / Excel
(points ou courses déjà résumées) et parfois en KML. On lit les trois.

Chaque course détectée donne : véhicule, début, fin, km, trous dans la trace
(coupures réseau). Elle est rattachée au dossier de transport (véhicule, date,
heure de départ) et son kilométrage remplit le dossier : plus de saisie
manuelle, donc plus d'écart avec la trace contrôlée par la caisse.

Minimisation : on ne conserve pas les points GPS, seulement le résumé de chaque
course, et on l'efface après PMT_TRACE_RETENTION_DAYS (90 jours par défaut :
le projet de loi contre la fraude limite la conservation à trois mois).
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import math
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional

from backend.services import pmt

EARTH_RADIUS_KM = 6371.0088
MAX_SPEED_KMH = 200          # au-delà : point aberrant (saut GPS), ignoré
JITTER_KM = 0.005            # mouvements < 5 m : bruit GPS à l'arrêt
STOP_SPLIT_MINUTES = 15      # arrêt plus long : nouvelle course
GAP_MINUTES = 3              # silence plus long en roulant : trou dans la trace
GAP_MIN_KM = 0.5
MATCH_WINDOW_MINUTES = 60    # écart toléré entre l'heure de départ du dossier et la trace


def retention_days() -> int:
    try:
        return max(1, int(os.environ.get("PMT_TRACE_RETENTION_DAYS", "90")))
    except ValueError:
        return 90


@dataclass
class Point:
    lat: float
    lon: float
    time: Optional[dt.datetime] = None


@dataclass
class Trip:
    vehicule: str = ""
    reference: str = ""          # référence de mission notée par le boîtier, si présente
    start: Optional[dt.datetime] = None
    end: Optional[dt.datetime] = None
    km: float = 0.0
    points: int = 0
    trous: int = 0               # coupures détectées
    km_trous: float = 0.0        # distance à vol d'oiseau couverte par les trous
    start_coord: Optional[tuple] = None
    end_coord: Optional[tuple] = None
    source: str = ""
    km_declare: Optional[float] = None   # export « résumé de courses » : km fournis par le boîtier
    warnings: list = field(default_factory=list)

    @property
    def key(self) -> str:
        raw = f"{plate(self.vehicule)}|{self.start.isoformat() if self.start else ''}|" \
              f"{self.end.isoformat() if self.end else ''}|{self.km:.2f}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def as_dict(self) -> dict:
        return {
            "key": self.key, "vehicule": self.vehicule, "reference": self.reference,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "km": round(self.km, 2), "points": self.points, "trous": self.trous,
            "km_trous": round(self.km_trous, 2), "source": self.source, "warnings": self.warnings,
        }


def plate(value: str) -> str:
    """Identifiant de véhicule comparable : « AB-123-CD », « ab 123 cd » → « AB123CD »."""
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def haversine_km(a: Point, b: Point) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a.lat, a.lon, b.lat, b.lon))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))


def parse_time(value: str) -> Optional[dt.datetime]:
    """ISO 8601 (GPX), « JJ/MM/AAAA HH:MM(:SS) », époque Unix. Rendu en heure locale naïve."""
    s = (value or "").strip()
    if not s:
        return None
    if re.fullmatch(r"\d{10}(\.\d+)?", s):
        return dt.datetime.fromtimestamp(float(s), tz=dt.timezone.utc).astimezone(_local_tz()).replace(tzinfo=None)
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo:
            d = d.astimezone(_local_tz()).replace(tzinfo=None)
        return d
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%Y/%m/%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _local_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(os.environ.get("PMT_TIMEZONE", "Europe/Paris"))
    except Exception:
        return dt.timezone.utc


# ──────────────────────────────────────────────────────────────────────────────
# Découpage en courses et kilométrage
# ──────────────────────────────────────────────────────────────────────────────

def build_trips(points: list[Point], vehicule: str = "", reference: str = "", source: str = "",
                split_on_stops: bool = True) -> list[Trip]:
    """Points d'un même véhicule → courses, km nettoyés des sauts GPS et du bruit."""
    pts = [p for p in points if -90 <= p.lat <= 90 and -180 <= p.lon <= 180 and not (p.lat == 0 and p.lon == 0)]
    if any(p.time for p in pts):
        pts = sorted((p for p in pts if p.time), key=lambda p: p.time)
    trips: list[Trip] = []
    current: Optional[Trip] = None
    last: Optional[Point] = None
    outliers = 0

    def open_trip(p: Point) -> Trip:
        t = Trip(vehicule=vehicule, reference=reference, start=p.time, end=p.time, points=1,
                 start_coord=(round(p.lat, 5), round(p.lon, 5)), end_coord=(round(p.lat, 5), round(p.lon, 5)),
                 source=source)
        trips.append(t)
        return t

    for p in pts:
        if current is None:
            current, last = open_trip(p), p
            continue
        d = haversine_km(last, p)
        minutes = (p.time - last.time).total_seconds() / 60 if (p.time and last.time) else None
        if minutes is not None and minutes > 0 and d / (minutes / 60) > MAX_SPEED_KMH:
            outliers += 1          # saut GPS : on garde le point précédent comme référence
            continue
        if minutes is not None and minutes > STOP_SPLIT_MINUTES and d < GAP_MIN_KM and split_on_stops:
            current, last = open_trip(p), p   # long arrêt au même endroit : nouvelle course
            continue
        if minutes is not None and minutes > GAP_MINUTES and d >= GAP_MIN_KM:
            current.trous += 1     # silence en roulant : coupure réseau
            current.km_trous += d
        if d >= JITTER_KM:
            current.km += d
            last = p
        current.points += 1
        current.end = p.time or current.end
        current.end_coord = (round(p.lat, 5), round(p.lon, 5))
    for t in trips:
        if outliers:
            t.warnings.append(f"{outliers} point(s) GPS aberrant(s) ignoré(s)")
        if t.trous:
            t.warnings.append(f"{t.trous} trou(s) dans la trace ({t.km_trous:.1f} km sans points)")
    # Une « course » de moins de 300 m est un déplacement de parking, pas un transport.
    return [t for t in trips if t.km >= 0.3 or t.km_declare]


# ──────────────────────────────────────────────────────────────────────────────
# Lecture des formats
# ──────────────────────────────────────────────────────────────────────────────

def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(el, name: str) -> str:
    for c in el:
        if _local(c.tag) == name:
            return (c.text or "").strip()
    return ""


def _safe_xml(content: bytes):
    text = content.decode("utf-8", errors="replace")
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise ValueError("Fichier XML refusé (DOCTYPE / entités non autorisés).")
    return ET.fromstring(text)


def parse_gpx(content: bytes, filename: str = "") -> list[Trip]:
    """GPX 1.0 / 1.1 : chaque <trk> (ou <rte>) est une mission ; le nom porte souvent véhicule et référence."""
    root = _safe_xml(content)
    meta_name = ""
    for el in root:
        if _local(el.tag) == "metadata":
            meta_name = _child_text(el, "name")
    trips: list[Trip] = []
    tracks = [el for el in root if _local(el.tag) in ("trk", "rte")]
    for trk in tracks:
        name = _child_text(trk, "name") or meta_name
        desc = " ".join(x for x in (_child_text(trk, "desc"), _child_text(trk, "cmt")) if x)
        points = []
        for el in trk.iter():
            if _local(el.tag) in ("trkpt", "rtept"):
                try:
                    points.append(Point(float(el.get("lat")), float(el.get("lon")), parse_time(_child_text(el, "time"))))
                except (TypeError, ValueError):
                    continue
        vehicule, reference = guess_vehicle_and_ref(f"{name} {desc}", filename)
        # Une piste nommée par le boîtier = une mission : on ne la redécoupe pas.
        trips += build_trips(points, vehicule, reference, "gpx", split_on_stops=not name)
    if not tracks:
        points = [Point(float(w.get("lat")), float(w.get("lon")), parse_time(_child_text(w, "time")))
                  for w in root.iter() if _local(w.tag) == "wpt" and w.get("lat") and w.get("lon")]
        vehicule, reference = guess_vehicle_and_ref(meta_name, filename)
        trips += build_trips(points, vehicule, reference, "gpx")
    return trips


def parse_kml(content: bytes, filename: str = "") -> list[Trip]:
    """KML : <gx:Track> (when + gx:coord) ou <LineString> (sans heures)."""
    root = _safe_xml(content)
    trips: list[Trip] = []
    for pm in root.iter():
        if _local(pm.tag) != "Placemark":
            continue
        name = _child_text(pm, "name")
        vehicule, reference = guess_vehicle_and_ref(name, filename)
        points: list[Point] = []
        for el in pm.iter():
            tag = _local(el.tag)
            if tag == "Track":
                whens = [parse_time(c.text or "") for c in el if _local(c.tag) == "when"]
                coords = [(c.text or "").split() for c in el if _local(c.tag) == "coord"]
                for w, c in zip(whens, coords):
                    if len(c) >= 2:
                        points.append(Point(float(c[1]), float(c[0]), w))
            elif tag == "LineString":
                for chunk in (_child_text(el, "coordinates") or "").split():
                    parts = chunk.split(",")
                    if len(parts) >= 2:
                        points.append(Point(float(parts[1]), float(parts[0])))
        if points:
            trips += build_trips(points, vehicule, reference, "kml", split_on_stops=False)
    return trips


CSV_COLUMNS = {
    "vehicule": ("vehicule", "véhicule", "immatriculation", "immat", "plaque", "boitier", "boîtier", "device",
                 "vehicle", "unite", "unité", "nom vehicule", "véhicule / boîtier"),
    "time": ("date heure", "horodatage", "datetime", "timestamp", "date/heure", "heure gps", "date et heure", "time"),
    "date": ("date",),
    "heure": ("heure", "hour"),
    "lat": ("latitude", "lat"),
    "lon": ("longitude", "lon", "lng", "long"),
    "start": ("debut", "début", "depart", "départ", "heure depart", "heure départ", "date debut", "date début",
              "date depart", "date départ", "start"),
    "end": ("fin", "arrivee", "arrivée", "heure arrivee", "heure arrivée", "date fin", "date arrivée", "end"),
    "km": ("km", "distance", "distance km", "km parcourus", "kilometrage", "kilométrage", "distance (km)"),
    "reference": ("mission", "reference", "référence", "ref", "course", "n mission", "n° mission", "bon"),
}


def _norm_header(h: str) -> str:
    h = (h or "").strip().lower()
    h = h.replace("°", "").replace("_", " ")
    return re.sub(r"\s+", " ", h)


def _map_headers(headers: list[str]) -> dict:
    mapping = {}
    for i, h in enumerate(headers):
        n = _norm_header(h)
        for key, names in CSV_COLUMNS.items():
            if n in names and key not in mapping.values():
                mapping[i] = key
                break
    return mapping


def _num(value) -> Optional[float]:
    try:
        return float(str(value).replace(" ", "").replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def parse_csv(content: bytes, filename: str = "") -> list[Trip]:
    """Deux exports courants : un point par ligne, ou une course par ligne (début, fin, km)."""
    from backend.services.pmt_rejets import _decode, _rows_from_csv, _rows_from_xlsx
    rows = _rows_from_xlsx(content) if content[:2] == b"PK" else _rows_from_csv(_decode(content))
    if not rows:
        return []
    header_idx, mapping = 0, {}
    for i, row in enumerate(rows[:10]):
        m = _map_headers([str(c or "") for c in row])
        if len(m) > len(mapping):
            header_idx, mapping = i, m
    keys = set(mapping.values())
    data = rows[header_idx + 1:]

    def get(row, key):
        for col, k in mapping.items():
            if k == key and col < len(row):
                return row[col]
        return None

    def when(row, key_dt, key_date="date", key_time="heure"):
        v = get(row, key_dt)
        if v not in (None, ""):
            return parse_time(str(v))
        d, h = get(row, key_date), get(row, key_time)
        return parse_time(f"{pmt._fr(d) if d else ''} {h or ''}".strip()) if d else None

    trips: list[Trip] = []
    if {"lat", "lon"} <= keys:
        by_vehicle: dict[str, list[Point]] = {}
        names: dict[str, str] = {}
        for row in data:
            lat, lon = _num(get(row, "lat")), _num(get(row, "lon"))
            if lat is None or lon is None:
                continue
            veh = str(get(row, "vehicule") or guess_vehicle_and_ref("", filename)[0] or "")
            by_vehicle.setdefault(plate(veh), []).append(Point(lat, lon, when(row, "time")))
            names[plate(veh)] = veh
        for k, pts in by_vehicle.items():
            trips += build_trips(pts, names[k], "", "csv")
        return trips
    if {"start", "km"} <= keys or {"date", "km"} <= keys:
        for row in data:
            km = _num(get(row, "km"))
            if km is None:
                continue
            start = parse_time(str(get(row, "start") or "")) or when(row, "start")
            if start and start.hour == 0 and start.minute == 0 and get(row, "heure"):
                start = when(row, "_", "date", "heure")
            end = parse_time(str(get(row, "end") or ""))
            t = Trip(vehicule=str(get(row, "vehicule") or ""), reference=str(get(row, "reference") or ""),
                     start=start, end=end, km=km, km_declare=km, source="csv-courses", points=0)
            trips.append(t)
        return trips
    raise ValueError("Colonnes non reconnues : il faut latitude/longitude (points) ou début + km (courses).")


def guess_vehicle_and_ref(text: str, filename: str = "") -> tuple[str, str]:
    """Plaque d'immatriculation (AA-123-AA) ou identifiant type « AMB-12 », et référence de mission."""
    hay = re.sub(r"[_.]", " ", f"{text} {filename}")
    m = re.search(r"\b([A-Z]{2})[- ]?(\d{3})[- ]?([A-Z]{2})\b", hay.upper())
    vehicule = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
    if not vehicule:
        m = re.search(r"\b((?:AMB|VSL|TAXI|VEH|V)[- ]?\d{1,4})\b", hay.upper())
        vehicule = m.group(1) if m else ""
    r = re.search(r"(?:mission|course|bon|ref|réf)[\s:#n°-]*([A-Za-z0-9-]{3,})", text, re.IGNORECASE)
    return vehicule, (r.group(1) if r else "")


def parse_file(content: bytes, filename: str) -> list[Trip]:
    name = (filename or "").lower()
    head = content[:400].lstrip().lower()
    if name.endswith(".gpx") or b"<gpx" in head:
        return parse_gpx(content, filename)
    if name.endswith(".kml") or b"<kml" in head:
        return parse_kml(content, filename)
    return parse_csv(content, filename)


# ──────────────────────────────────────────────────────────────────────────────
# Rattachement aux dossiers
# ──────────────────────────────────────────────────────────────────────────────

def trip_score(trip: dict, voucher: dict) -> int:
    """0-100 : même jour obligatoire, puis véhicule, heure de départ, référence."""
    t = pmt.normalize_transport(voucher.get("transport"))
    start = dt.datetime.fromisoformat(trip["start"]) if trip.get("start") else None
    day = pmt.parse_date(t.date_transport)
    if not start or not day or start.date() != day:
        return 0
    score = 40
    vp, tp = plate(t.vehicule), plate(trip.get("vehicule", ""))
    if vp and tp:
        if vp != tp:
            return 0
        score += 30
    ref = str(voucher.get("id", ""))[:8].lower()
    if ref and ref in (trip.get("reference") or "").lower():
        score += 40
    if t.heure_depart:
        try:
            h, m = map(int, t.heure_depart.split(":")[:2])
            gap = abs((start - start.replace(hour=h, minute=m, second=0)).total_seconds()) / 60
            if gap <= MATCH_WINDOW_MINUTES:
                score += 30 - int(gap / 3)
            else:
                score -= 30
        except ValueError:
            pass
    return max(0, min(100, score))


def assign(trips: list[dict], vouchers: list[dict], threshold: int = 70) -> dict:
    """Associe chaque dossier à sa meilleure trace (aller), une trace ne servant qu'une fois.

    Seuil élevé : sans véhicule ni heure de départ, deux courses le même jour
    restent ambiguës et sont laissées à l'utilisateur.
    """
    pairs = sorted(((trip_score(tr, v), tr["key"], v["id"]) for tr in trips for v in vouchers),
                   reverse=True)
    used_trips, used_vouchers, result = set(), set(), {}
    for score, tkey, vid in pairs:
        if score < threshold:
            break
        if tkey in used_trips or vid in used_vouchers:
            continue
        # Ambiguïté : une autre trace a exactement le même score pour ce dossier.
        rivals = [s for s, tk, v in pairs if v == vid and tk != tkey and tk not in used_trips and s == score]
        if rivals:
            continue
        used_trips.add(tkey)
        used_vouchers.add(vid)
        result[vid] = (tkey, score)
    return result


def apply_to_transport(transport: dict, trip: dict) -> dict:
    """Le km de la trace remplit le dossier ; s'il n'y avait pas de km facturés, on les pré-remplit."""
    t = dict(transport or {})
    km = round(trip["km"], 1)
    t["km_geoloc"] = km
    if t.get("km_aller") in (None, ""):
        t["km_aller"] = km
    if not t.get("vehicule") and trip.get("vehicule"):
        t["vehicule"] = trip["vehicule"]
    if not t.get("heure_depart") and trip.get("start"):
        t["heure_depart"] = trip["start"][11:16]
    t["trace"] = {"key": trip["key"], "start": trip.get("start"), "end": trip.get("end"), "km": km,
                  "trous": trip.get("trous", 0), "source": trip.get("source", "")}
    return t
