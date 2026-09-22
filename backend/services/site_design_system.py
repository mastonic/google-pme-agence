"""Local Pulse — sector-aware design system V2.

Keeps generated sites visually distinct by business category while preserving
one quality baseline. Variants are deterministic per business so regeneration
does not randomly redesign the whole site.
"""
from __future__ import annotations

import hashlib
import re
from typing import Iterable

BASE_RULES = [
    "mobile-first with fluid type and spacing",
    "rounded surfaces with a deliberate radius hierarchy",
    "asymmetric/editorial composition rather than repeated 3-card grids",
    "one or two meaningful motion ideas, never animation everywhere",
    "respect prefers-reduced-motion",
    "at least one human/local proof element",
    "every section must support understanding, trust, desire or action",
    "mobile must be intentionally composed, not only stacked desktop",
]

PROFILES = {
    "restaurant": {
        "label":"Restaurant / Brasserie","visual":"editorial gastronomy, cinematic warmth, tactile menu",
        "palette":"deep wine / warm ivory / burnt orange or olive","type":"display serif + clean grotesk",
        "radius":"22-28px","layouts":["editorial-split","menu-bento","cinematic-window"],
        "heroes":["asymmetric split with image window","bento with dish + atmosphere","editorial headline with offset image"],
        "signature":["signature dishes bento","menu tabs","chef/local story","review quote","reservation strip","hours + map"],
        "motion":["slow image scale","menu crossfade","scroll reveal"],"conversion":"reservation-first",
        "human":"chef/team, local produce, atmosphere, memorable review",
    },
    "cafe": {
        "label":"Café","visual":"cozy contemporary, morning light, tactile playful cards",
        "palette":"espresso / oat / cream / muted coral","type":"rounded grotesk + expressive serif accent",
        "radius":"24-30px","layouts":["cozy-bento","counter-story","editorial-collage"],
        "heroes":["compact coffee bento","split with opening-hours card","editorial collage with special of the day"],
        "signature":["today special","drinks bento","ambiance strip","neighborhood story","reviews","hours + map"],
        "motion":["steam accent","gentle marquee","hover zoom"],"conversion":"visit/order-first",
        "human":"ritual of the place, regulars, neighborhood atmosphere",
    },
    "bakery": {
        "label":"Boulangerie / Pâtisserie","visual":"artisan tactile, editorial products, handcrafted warmth",
        "palette":"flour white / wheat / butter / cocoa","type":"warm serif + utilitarian sans",
        "radius":"18-30px","layouts":["artisan-catalog","bakery-editorial","fresh-from-oven"],
        "heroes":["product-led bento","oversized type + product window","storefront + fresh products"],
        "signature":["fresh today","product categories","craft process","masonry gallery","review quote","hours + map"],
        "motion":["subtle steam","product lift","horizontal category rail"],"conversion":"visit/preorder-first",
        "human":"craft, early-morning work, ingredients, family/local know-how",
    },
    "bar": {
        "label":"Bar / Cocktail","visual":"night editorial, social energy, luminous accents",
        "palette":"ink black / electric amber / deep plum","type":"condensed display + modern sans",
        "radius":"12-22px","layouts":["night-editorial","event-poster","cocktail-bento"],
        "heroes":["poster hero","split with events card","cocktail bento"],
        "signature":["cocktail selection","events","ambiance gallery","social proof","location + hours"],
        "motion":["glow hover","ticker","image crossfade"],"conversion":"visit/event-first",
        "human":"music, bartender personality, community",
    },
    "medical": {
        "label":"Cabinet médical / Clinique","visual":"calm clinical, spacious, reassuring, precise",
        "palette":"warm white / sage / sky / graphite","type":"humanist sans + restrained serif",
        "radius":"14-22px","layouts":["calm-split","care-bento","trust-led"],
        "heroes":["split with appointment card","services + practitioner bento","editorial trust hero"],
        "signature":["specialties","care team","trust strip","patient journey","appointment","access + hours"],
        "motion":["gentle fade","number counters","micro hover only"],"conversion":"appointment-first",
        "human":"care philosophy, team faces, clear patient journey",
    },
    "dentist": {
        "label":"Cabinet dentaire","visual":"bright precision, premium care without coldness",
        "palette":"porcelain / aqua / navy / mint","type":"geometric sans + elegant serif",
        "radius":"16-26px","layouts":["precision-bento","smile-story","clinic-editorial"],
        "heroes":["portrait + appointment card","treatment bento","bright editorial split"],
        "signature":["treatments","technology","team","patient path","reviews","appointment"],
        "motion":["soft wipe","card highlight","subtle image pan"],"conversion":"appointment-first",
        "human":"comfort, fear reduction, team warmth, transparent process",
    },
    "pharmacy": {
        "label":"Pharmacie","visual":"clear utility, trusted neighborhood service",
        "palette":"white / pharmacy green / deep teal","type":"clean sans",
        "radius":"12-20px","layouts":["service-dashboard","local-care","utility-bento"],
        "heroes":["compact service hero","hours + services bento","storefront split"],
        "signature":["services","opening hours","health services","team","access map","contact"],
        "motion":["quick fade","open/closed pulse","subtle hover"],"conversion":"visit/call-first",
        "human":"local advice, familiar team, everyday usefulness",
    },
    "veterinary": {
        "label":"Clinique vétérinaire","visual":"warm medical, friendly imagery, approachable expertise",
        "palette":"cream / moss / teal / terracotta","type":"rounded sans + friendly serif",
        "radius":"24-30px","layouts":["friendly-bento","care-story","pet-editorial"],
        "heroes":["team + pet split","care bento","editorial hero with emergency info"],
        "signature":["care services","team","emergency info","pet tips","reviews","appointment"],
        "motion":["gentle icon float","image reveal","scroll fade"],"conversion":"appointment/call-first",
        "human":"empathy for owners, team personality, reassurance",
    },
    "beauty": {
        "label":"Institut beauté / Onglerie","visual":"soft editorial luxury, fashion composition, tactile close-ups",
        "palette":"nude / blush / burgundy / warm white","type":"high-contrast serif + minimal sans",
        "radius":"18-32px","layouts":["editorial-beauty","treatment-bento","lookbook"],
        "heroes":["vertical editorial split","lookbook bento","oversized type + service card"],
        "signature":["treatments","lookbook","before/after","team","reviews","booking"],
        "motion":["clip reveal","image zoom","soft marquee"],"conversion":"booking-first",
        "human":"self-care, practitioner personality, real transformations",
    },
    "hair": {
        "label":"Coiffeur / Barber","visual":"fashion studio, bold portraits, editorial rhythm",
        "palette":"charcoal / warm white / copper or cobalt","type":"bold grotesk + editorial serif",
        "radius":"16-24px","layouts":["fashion-editorial","lookbook-grid","barber-studio"],
        "heroes":["lookbook split","kinetic type + portrait","service + style bento"],
        "signature":["services + prices","lookbook","team","signature styles","reviews","booking"],
        "motion":["image reveal","horizontal lookbook","hover crop"],"conversion":"booking-first",
        "human":"stylist identity, signature style, client confidence",
    },
    "spa": {
        "label":"Spa / Bien-être","visual":"sensory minimalism, quiet luxury, organic shapes",
        "palette":"sand / stone / eucalyptus / charcoal","type":"elegant serif + calm sans",
        "radius":"28-36px","layouts":["quiet-luxury","ritual-story","wellness-bento"],
        "heroes":["quiet split","ritual cards","large type + floating treatment card"],
        "signature":["rituals","sensory gallery","benefits","practitioner","reviews","booking"],
        "motion":["slow fade","breathing accent","gentle parallax"],"conversion":"booking-first",
        "human":"ritual, calm, practitioner care, sensory experience",
    },
    "fitness": {
        "label":"Fitness / Salle de sport","visual":"energetic editorial, strong contrast, modular stats",
        "palette":"ink / acid green or orange / white","type":"condensed bold + utility sans",
        "radius":"16-20px","layouts":["kinetic-grid","performance-bento","coach-led"],
        "heroes":["kinetic type + action image","stats bento","coach split"],
        "signature":["programs","coaches","results stats","schedule","reviews","trial CTA"],
        "motion":["counters","ticker","image pan"],"conversion":"trial-first",
        "human":"coach relationships, progress, community",
    },
    "automotive": {
        "label":"Garage / Carrosserie","visual":"industrial modular, technical confidence, strong hierarchy",
        "palette":"graphite / steel / signal orange / white","type":"bold grotesk + monospace accent",
        "radius":"10-18px","layouts":["industrial-grid","service-dashboard","workshop-story"],
        "heroes":["service dashboard","workshop split","bold type + quote card"],
        "signature":["services","diagnostic process","trust proof","workshop gallery","reviews","estimate"],
        "motion":["grid hover","counters","line accents"],"conversion":"quote/call-first",
        "human":"mechanic expertise, transparency, before/after workmanship",
    },
    "car_dealer": {
        "label":"Concession automobile","visual":"premium product catalog, vehicle-first, polished",
        "palette":"black / silver / white / brand accent","type":"modern grotesk",
        "radius":"18-22px","layouts":["vehicle-showcase","inventory-bento","premium-dealer"],
        "heroes":["featured vehicle + stats","inventory bento","cinematic car split"],
        "signature":["featured inventory","services","finance/trade-in","reviews","location"],
        "motion":["image pan","carousel","hover details"],"conversion":"test-drive/call-first",
        "human":"advisor support, buying confidence, after-sales",
    },
    "professional": {
        "label":"Avocat / Expert-comptable / Conseil","visual":"editorial authority, restrained premium, clarity",
        "palette":"navy / parchment / brass / charcoal","type":"editorial serif + clean sans",
        "radius":"14-20px","layouts":["authority-editorial","expertise-bento","case-led"],
        "heroes":["text + expert portrait","expertise bento","case-led split"],
        "signature":["expertise","proof points","team","process","case examples","contact"],
        "motion":["line reveal","text mask","hover underline"],"conversion":"consultation-first",
        "human":"named experts, listening, process clarity, local understanding",
    },
    "real_estate": {
        "label":"Agence immobilière","visual":"architecture editorial, property-first, premium approachable",
        "palette":"warm white / charcoal / olive or cobalt","type":"editorial serif + geometric sans",
        "radius":"20-30px","layouts":["property-editorial","listing-bento","neighborhood-story"],
        "heroes":["featured property split","listing bento","neighborhood editorial"],
        "signature":["featured properties","services","neighborhoods","agents","proof stats","contact"],
        "motion":["property zoom","listing rail","counters"],"conversion":"valuation/contact-first",
        "human":"agents, neighborhoods, seller/buyer reassurance",
    },
    "retail": {
        "label":"Boutique / Commerce","visual":"product-led bento, curated local retail",
        "palette":"brand-led neutral base + one strong accent","type":"modern sans + display accent",
        "radius":"22-28px","layouts":["product-bento","editorial-shop","local-catalog"],
        "heroes":["product bento","promotion split","category-led hero"],
        "signature":["featured products","categories","story","reviews","visit store"],
        "motion":["product zoom","category rail","subtle marquee"],"conversion":"visit/shop-first",
        "human":"curation, local owner, product story",
    },
    "florist": {
        "label":"Fleuriste","visual":"organic editorial, botanical color, asymmetric composition",
        "palette":"cream / leaf green / petal accent / plum","type":"romantic serif + clean sans",
        "radius":"24-34px","layouts":["botanical-editorial","bouquet-bento","seasonal-story"],
        "heroes":["floral collage","bouquet bento","seasonal editorial"],
        "signature":["seasonal bouquets","occasions","gallery","story","delivery","contact"],
        "motion":["gentle drift","image reveal","seasonal marquee"],"conversion":"order/call-first",
        "human":"artisan florist, occasions, local sourcing",
    },
    "lodging": {
        "label":"Hôtel / Hébergement","visual":"immersive escape, editorial travel, destination-led",
        "palette":"destination-led natural tones","type":"warm editorial serif + modern sans",
        "radius":"20-30px","layouts":["immersive-escape","stay-bento","destination-story"],
        "heroes":["image window + booking card","stay bento","destination editorial"],
        "signature":["experience","rooms","amenities","destination","reviews","booking"],
        "motion":["slow parallax","gallery crossfade","sticky booking card"],"conversion":"booking-first",
        "human":"host story, destination feeling, guest moments",
    },
    "artisan_home": {
        "label":"Artisan / Dépannage / Bâtiment","visual":"practical premium, proof-first, local trust",
        "palette":"white / graphite / trade accent","type":"strong sans",
        "radius":"14-20px","layouts":["proof-first","service-bento","local-expert"],
        "heroes":["service + proof split","emergency/contact bento","project before/after"],
        "signature":["services","proof stats","before/after","service area","reviews","quote"],
        "motion":["before-after","counter","hover highlight"],"conversion":"call/quote-first",
        "human":"craftsperson identity, real projects, local area",
    },
    "generic": {
        "label":"Commerce local","visual":"crafted local modernism, warm utility",
        "palette":"business-led neutral + one strong accent","type":"modern sans + optional serif",
        "radius":"18-26px","layouts":["crafted-bento","editorial-split","local-story"],
        "heroes":["asymmetric split","service bento","story-first compact hero"],
        "signature":["services","proof","story","reviews","hours + map","contact"],
        "motion":["scroll reveal","hover lift","image zoom"],"conversion":"contact-first",
        "human":"owner/team, local roots, one real proof point",
    },
}

TYPE_MAP = [
    ("dentist","dentist"),("pharmacy","pharmacy"),("veterinary_care","veterinary"),
    ("doctor","medical"),("hospital","medical"),("physiotherapist","medical"),
    ("bakery","bakery"),("bar","bar"),("cafe","cafe"),
    ("restaurant","restaurant"),("meal_delivery","restaurant"),("meal_takeaway","restaurant"),
    ("hair_care","hair"),("barber_shop","hair"),("spa","spa"),
    ("beauty_salon","beauty"),("nail_salon","beauty"),
    ("gym","fitness"),("fitness_center","fitness"),
    ("car_dealer","car_dealer"),("car_repair","automotive"),("car_wash","automotive"),
    ("real_estate_agency","real_estate"),
    ("lawyer","professional"),("accountant","professional"),("insurance_agency","professional"),
    ("florist","florist"),
    ("lodging","lodging"),("hotel","lodging"),("motel","lodging"),("resort_hotel","lodging"),
    ("bed_and_breakfast","lodging"),("guest_house","lodging"),("campground","lodging"),
    ("plumber","artisan_home"),("electrician","artisan_home"),("general_contractor","artisan_home"),
    ("roofing_contractor","artisan_home"),("painter","artisan_home"),("locksmith","artisan_home"),
    ("store","retail"),("clothing_store","retail"),("shoe_store","retail"),
    ("jewelry_store","retail"),("electronics_store","retail"),("book_store","retail"),
    ("supermarket","retail"),("convenience_store","retail"),("hardware_store","retail"),
]

NAME_HINTS = [
    (r"\b(barber|barbershop|coiffeur|coiffure)\b","hair"),
    (r"\b(spa|massage|bien[- ]être|wellness)\b","spa"),
    (r"\b(ongle|nail|esthétique|beaute|beauté)\b","beauty"),
    (r"\b(pâtisserie|patisserie|boulangerie|bakery)\b","bakery"),
    (r"\b(cocktail|lounge|bar)\b","bar"),
    (r"\b(dentaire|dentiste|orthodont)\b","dentist"),
    (r"\b(pharmacie)\b","pharmacy"),
    (r"\b(vétérinaire|veterinaire|vet)\b","veterinary"),
    (r"\b(immobilier|immo|real estate)\b","real_estate"),
    (r"\b(fleur|fleurs|fleuriste|florist)\b","florist"),
    (r"\b(hotel|hôtel|gîte|gite|lodge|villa|bungalow|cabane|bulle)\b","lodging"),
    (r"\b(plomb|électric|electric|toiture|serrurier|climatisation|artisan)\b","artisan_home"),
]

def detect_archetype(types: Iterable[str] | None, name: str = "") -> str:
    types_set={str(t).strip().lower() for t in (types or []) if t}
    lowered=(name or "").lower()
    for pattern,key in NAME_HINTS:
        if re.search(pattern, lowered):
            return key
    for google_type,key in TYPE_MAP:
        if google_type in types_set:
            return key
    return "generic"

def _pick(key: str, values: list[str]) -> str:
    digest=hashlib.sha256((key or "local-pulse").encode("utf-8")).digest()
    return values[int.from_bytes(digest[:4],"big") % len(values)]

def resolve_site_design(types=None, name: str = "", business_id: str = "") -> dict:
    key=detect_archetype(types,name)
    cfg=dict(PROFILES[key])
    stable=business_id or name or key
    cfg["key"]=key
    cfg["layout_variant"]=_pick(stable+":layout",cfg["layouts"])
    cfg["hero_variant"]=_pick(stable+":hero",cfg["heroes"])
    cfg["motion_variant"]=_pick(stable+":motion",cfg["motion"])
    cfg["base_rules"]=BASE_RULES
    return cfg

def build_design_prompt_directive(d: dict) -> str:
    return f"""
LOCAL PULSE — DESIGN ARCHETYPE
Category: {d['label']} ({d['key']})
Visual language: {d['visual']}
Palette direction: {d['palette']}
Typography: {d['type']}
Radius system: {d['radius']}
Layout variant: {d['layout_variant']}
Hero variant: {d['hero_variant']}
Signature components: {', '.join(d['signature'])}
Motion: {', '.join(d['motion'])}; preferred = {d['motion_variant']}
Conversion: {d['conversion']}
Human/emotional angle: {d['human']}

NON-NEGOTIABLE:
- Do NOT default to a full-screen dark background-image hero.
- First viewport must show a useful action or proof, not only headline + buttons.
- Use asymmetric/editorial composition and a clear radius hierarchy.
- Include at least one category-signature component.
- Do not repeat identical 3-column card grids in consecutive sections.
- Mix rhythms: bento, split, editorial, horizontal rail, masonry, sticky utility.
- Motion supports hierarchy; respect prefers-reduced-motion.
- Make the business feel human and local.
- Every section needs a commercial purpose.
- Mobile must feel deliberately designed.
"""

def build_runtime_effects(d: dict) -> str:
    return """
<style id="lp-design-v2">
[data-lp-card]{transition:transform .35s cubic-bezier(.2,.75,.25,1),box-shadow .35s cubic-bezier(.2,.75,.25,1)}
.lp-media{overflow:hidden}.lp-media img{transition:transform .65s cubic-bezier(.2,.75,.25,1)}
.lp-bento{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:clamp(12px,1.5vw,22px)}
.lp-rail{display:flex;gap:16px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none}
.lp-rail>*{scroll-snap-align:start;flex:0 0 min(82vw,420px)}
@media(hover:hover) and (pointer:fine){[data-lp-card]:hover{transform:translateY(-6px);box-shadow:0 24px 70px rgba(0,0,0,.14)}.lp-media:hover img{transform:scale(1.045)}}
@media(max-width:760px){.lp-bento{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;scroll-behavior:auto!important}}
</style>
<script id="lp-design-v2-js">
(function(){if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;var els=document.querySelectorAll('[data-lp-reveal]');var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.animate([{opacity:0,transform:'translateY(22px)'},{opacity:1,transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.2,.75,.25,1)',fill:'both'});io.unobserve(e.target)}})},{threshold:.12});els.forEach(function(x){io.observe(x)})})();
</script>
"""
