import urllib.parse
import re
import os
import json
import time

# ─── Provider fallback chain ──────────────────────────────────────────────────
# Order: gemini-3.5-flash → gemini-3.1-flash-lite → gemini-2.5-flash → mistral-large → mistral-small
# A provider is skipped if its API key is missing OR if it returns a quota/rate error.

PROVIDERS = [
    {"name": "gemini-3.5-flash",     "type": "gemini",  "model": "gemini-3.5-flash"},
    {"name": "gemini-3.1-flash-lite", "type": "gemini",  "model": "gemini-3.1-flash-lite"},
    {"name": "gemini-2.5-flash",     "type": "gemini",  "model": "gemini-2.5-flash"},
    {"name": "mistral-large",        "type": "mistral", "model": "mistral-large-latest"},
    {"name": "mistral-small",        "type": "mistral", "model": "mistral-small-latest"},
]

PROVIDERS_TEXT = [
    {"name": "gemini-3.5-flash",     "type": "gemini",  "model": "gemini-3.5-flash"},
    {"name": "gemini-3.1-flash-lite", "type": "gemini",  "model": "gemini-3.1-flash-lite"},
    {"name": "gemini-2.5-flash",     "type": "gemini",  "model": "gemini-2.5-flash"},
    {"name": "mistral-large",        "type": "mistral", "model": "mistral-large-latest"},
    {"name": "mistral-small",        "type": "mistral", "model": "mistral-small-latest"},
]

# ─── Sections & design par secteur ────────────────────────────────────────────
SECTOR_PROFILES = {
    "restaurant": {
        "label": "Restaurant / Brasserie",
        "hint": "luxury-dining : ambiance chaleureuse, tons ambrés ou rouges profonds sur fond sombre, typographies serif élégantes",
        "sections": ["hero", "about", "menu", "gallery", "testimonials", "hours_map", "contact"],
        "special_instructions": """- Section MENU : 4 onglets (Entrées / Plats / Desserts / Boissons) avec prix.
- Bouton RÉSERVATION proéminent dans le hero.
- Section GALERIE grille 3 colonnes : plats + ambiance salle.""",
        "cta_primary": "Réserver une table",
        "cta_secondary": "Voir la carte",
    },
    "cafe": {
        "label": "Café / Boulangerie / Pâtisserie",
        "hint": "cozy-artisan : tons beige, moka, crème, chaleureux et artisanal. Pour une boulangerie : mise en valeur des pains artisanaux, viennoiseries et pâtisseries maison.",
        "sections": ["hero", "menu", "ambiance_gallery", "about", "testimonials", "hours_map", "contact"],
        "special_instructions": """- Si boulangerie/pâtisserie : Section CARTE avec catégories Pains, Viennoiseries, Pâtisseries, Sandwichs + prix.
- Si café : boissons chaudes, froides, snacks avec prix.
- Section AMBIANCE/GALERIE : 3 photos en mosaïque de l'intérieur et des produits.
- Bouton "Commander" ou "Réserver" visible dans le hero.""",
        "cta_primary": "Voir notre carte",
        "cta_secondary": "Nous trouver",
    },
    "medical": {
        "label": "Médecin / Dentiste / Pharmacie",
        "hint": "clean-medical : blanc pur, vert menthe ou bleu ciel, typo sans-serif, rassurant",
        "sections": ["hero", "services", "team", "certifications", "testimonials", "appointment", "hours_map"],
        "special_instructions": """- Section SERVICES : cartes avec icône médicale et description.
- Section ÉQUIPE : photo, nom, spécialité.
- Formulaire RENDEZ-VOUS : Nom, Tel, Date, Motif.""",
        "cta_primary": "Prendre rendez-vous",
        "cta_secondary": "Nos spécialités",
    },
    "automotive": {
        "label": "Garage / Carrosserie / Concessionnaire",
        "hint": "industrial-bold : gris acier, orange électrique, robustesse et expertise",
        "sections": ["hero", "services", "certifications", "gallery", "testimonials", "estimate_form", "hours_map"],
        "special_instructions": """- Section PRESTATIONS : services avec icône et fourchette de prix.
- Formulaire DEVIS : véhicule, prestation, coordonnées.""",
        "cta_primary": "Demander un devis",
        "cta_secondary": "Nos prestations",
    },
    "beauty": {
        "label": "Salon de beauté / Coiffeur / Spa",
        "hint": "modern-beauty : rose nude, beige doré, blanc cassé, élégance féminine et premium",
        "sections": ["hero", "services_menu", "gallery", "team", "testimonials", "booking", "hours_map"],
        "special_instructions": """- Section SOINS : tableau avec nom, durée et prix.
- Section GALERIE : grid 2×3 avec réalisations.
- Bouton RÉSERVATION très visible.""",
        "cta_primary": "Réserver ma séance",
        "cta_secondary": "Nos soins",
    },
    "professional": {
        "label": "Avocat / Expert-comptable / Agence",
        "hint": "executive-trust : marine foncé, blanc, touches dorées, sérieux et confiance",
        "sections": ["hero", "expertise", "team", "process", "testimonials", "contact", "hours_map"],
        "special_instructions": """- Section DOMAINES D'EXPERTISE : cartes avec icône et description.
- Section PROCESSUS : étapes numérotées (Consultation → Analyse → Solution → Suivi).""",
        "cta_primary": "Consultation gratuite",
        "cta_secondary": "Notre expertise",
    },
    "retail": {
        "label": "Commerce / Boutique / Fleuriste",
        "hint": "vibrant-local : couleurs vives, accessible, convivial, ancrage local",
        "sections": ["hero", "featured_products", "promotions", "about", "testimonials", "hours_map", "contact"],
        "special_instructions": """- Section PRODUITS PHARES : 6 cartes avec photo, nom et prix.
- Section PROMOTIONS : bandeau accrocheur avec offre du moment.""",
        "cta_primary": "Découvrir la boutique",
        "cta_secondary": "Nos promotions",
    },
    "generic": {
        "label": "Commerce local",
        "hint": "universal-modern : bleu professionnel, blanc, sobre et rassurant",
        "sections": ["hero", "about", "services", "testimonials", "hours_map", "contact"],
        "special_instructions": "Sections standards avec accent sur le savoir-faire local et la proximité.",
        "cta_primary": "Nous contacter",
        "cta_secondary": "Nos services",
    },
    "lodging": {
        "label": "Hébergement / Hôtel / Hébergement insolite",
        "hint": "immersive-getaway : tons naturels (vert forêt, terracotta, crème) ou nocturnes étoilés selon le concept, typographie chaleureuse, grandes photos pleine largeur qui vendent l'expérience plus que le bâtiment",
        "sections": ["hero", "experience", "gallery", "amenities", "testimonials", "hours_map", "contact"],
        "special_instructions": """- Section EXPÉRIENCE : décrire ce que vit le client (pas juste "une chambre") — s'appuyer sur le nom du commerce et les avis clients pour identifier le concept exact (bulle, cabane, yourte, chambre classique...).
- Section GALERIE : grande place aux photos immersives (extérieur + intérieur + vue).
- Section ÉQUIPEMENTS : wifi, parking, petit-déjeuner, animaux, etc. avec icônes.
- Bouton RÉSERVATION très visible dans le hero et en sticky mobile.""",
        "cta_primary": "Réserver mon séjour",
        "cta_secondary": "Découvrir l'expérience",
    },
}

SECTOR_UNSPLASH = {
    "restaurant": [
        "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1400&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1546833998-877b37c2e5c6?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1551632436-cbf8dd35adfa?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1559847844-5315695dadae?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1424847651672-bf20a4b0982b?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1600891964599-f61ba0e24092?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=900&auto=format&fit=crop",
    ],
    "cafe": [
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=1400&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1442512595331-e89e73853f31?w=900&auto=format&fit=crop",
    ],
    "medical": [
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1400&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1581056771107-24ca5f033842?w=900&auto=format&fit=crop",
    ],
    "automotive": [
        "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=1400&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=900&auto=format&fit=crop",
    ],
    "beauty": [
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1400&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=900&auto=format&fit=crop",
    ],
    "professional": [
        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=1400&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1497366216548-37526070297c?w=900&auto=format&fit=crop",
    ],
    "retail": [
        "https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=1400&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1567401893414-76b7b1e5a7a5?w=900&auto=format&fit=crop",
    ],
    "generic": [
        "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1400&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=900&auto=format&fit=crop",
    ],
}

SECTOR_FAL_PROMPTS = {
    "restaurant": [
        "Professional commercial photography of a warm Antillean restaurant dining room, round tables with white tablecloths, tropical flowers centerpiece, warm Caribbean evening light through wooden shutters, bois créole architecture details, photorealistic, 8k, professional DSLR, Martinique Caribbean atmosphere, no people, no text",
        "High-end food photography of an elegantly plated Creole gourmet main course, grilled fish with court-bouillon sauce, tropical vegetable garnish, restaurant plate, warm Caribbean sunlight from side window, shallow depth of field, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a Caribbean restaurant exterior at golden hour, colorful painted wooden facade, tropical plants framing the entrance, warm Antilles sunlight, inviting entrance, photorealistic, 8k, Martinique Caribbean atmosphere, no people, no text",
        "High-end food photography of a traditional Creole spread, accras de morue, boudin antillais, colombo, vibrant tropical colors, rustic wooden table, natural Caribbean daylight, sharp focus, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a French Caribbean bar counter, rum bottles display, tropical cocktails, colorful local decor, warm ambient lighting, photorealistic, 8k, Martinique Caribbean atmosphere, no people, no text",
        "High-end food photography of fresh tropical fruits and local produce display at a Caribbean restaurant, mangoes pineapples passion fruits, vibrant colors, natural daylight, photorealistic, 8k, no people, no text",
    ],
    "cafe": [
        "Professional commercial photography of a charming Caribbean café-boulangerie interior, colorful painted walls, local pastries display, warm morning tropical light through louvered windows, photorealistic, 8k, Martinique Caribbean atmosphere, no people, no text",
        "High-end food photography of a café au lait and coconut pastry on a colorful ceramic plate, tropical flowers beside, soft Caribbean morning light, shallow depth of field, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a French Caribbean bakery display window, golden croissants pain au chocolat coconut brioche, warm golden tropical light, mouth-watering presentation, photorealistic, 8k, no people, no text",
        "High-end product photography of artisan bread loaves and local sweet pastries on wooden Caribbean bakery shelves, warm rustic atmosphere, photorealistic, 8k, no people, no text",
    ],
    "medical": [
        "Professional commercial photography of a modern clean medical consultation office in Martinique, ergonomic desk, tropical plant in corner, soft natural Caribbean daylight through jalousie windows, reassuring professional atmosphere, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a bright modern Caribbean clinic waiting room, comfortable chairs, tropical plant, natural light, clean white walls, calming atmosphere, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a friendly Afro-Caribbean French doctor in white coat standing in a modern clinic corridor, professional smile, natural Caribbean light, photorealistic, 8k, no text",
    ],
    "automotive": [
        "Professional commercial photography of a modern automotive garage workshop in the French Caribbean, organized tool wall, clean epoxy floor, hydraulic lift, bright industrial LED lighting, photorealistic, 8k, Martinique Caribbean atmosphere, no people, no text",
        "Professional commercial photography of a Caribbean auto service center exterior, clean modern facade, tropical vegetation in background, sunny Caribbean day, photorealistic, 8k, no people, no text",
        "High-end commercial photography of professional automotive tools arranged on a pegboard in a Caribbean garage, orange and grey tones, sharp focus, photorealistic, 8k, no people, no text",
    ],
    "beauty": [
        "Professional commercial photography of a modern Caribbean beauty salon interior, colorful accents, styling stations with large mirrors, tropical flowers arrangement, warm flattering lighting, photorealistic, 8k, Martinique Caribbean atmosphere, no people, no text",
        "Professional commercial photography of an Afro-Caribbean French hairstylist working in an elegant salon, natural hair care products, warm professional lighting, photorealistic, 8k, no text",
        "High-end commercial photography of luxury natural hair care products and professional tools on a marble counter in a Caribbean salon, tropical flower decoration, soft natural light, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a spa treatment room in Martinique, white massage table, tropical orchids, bamboo accents, candles, soft diffused Caribbean light, zen atmosphere, photorealistic, 8k, no people, no text",
    ],
    "professional": [
        "Professional commercial photography of a modern Caribbean law office interior, dark wood bookshelves, leather chair, tropical plant, natural Caribbean daylight through jalousie windows, executive atmosphere, photorealistic, 8k, no people, no text",
        "Professional commercial photography of an Afro-Caribbean French professional in a business suit at a modern office desk in Martinique, confident posture, natural light, photorealistic, 8k, no text",
        "High-end commercial photography of professional business documents and fountain pen on a dark wood desk in a Caribbean office, leather agenda, warm focused light, photorealistic, 8k, no people, no text",
    ],
    "retail": [
        "Professional commercial photography of a bright Caribbean boutique interior, colorful wooden shelves with local products, warm tropical ambient lighting, vibrant Antillean decor, photorealistic, 8k, Martinique Caribbean atmosphere, no people, no text",
        "High-end product photography of local Caribbean products neatly arranged on a wooden shelf, natural tropical daylight from the side, shallow depth of field, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a welcoming French Caribbean local shop storefront, colorful painted facade, tropical plants framing entrance, sunny Caribbean day, photorealistic, 8k, no people, no text",
    ],
    "generic": [
        "Professional commercial photography of a modern professional local business interior in Martinique, clean organized space, warm Caribbean ambient light, tropical plant in corner, welcoming atmosphere, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a Caribbean local business storefront, colorful painted facade, tropical vegetation, sunny Caribbean day, welcoming entrance, photorealistic, 8k, no people, no text",
        "High-end commercial photography of a professional workspace in the French Antilles, modern furniture, natural Caribbean daylight through louvered windows, organized desk, photorealistic, 8k, no people, no text",
    ],
    "lodging": [
        "Professional commercial photography of a unique eco-lodge exterior in Martinique at golden hour, tropical vegetation, wooden deck, fairy lights, lush Caribbean nature, magical atmosphere, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a cozy Caribbean accommodation interior, premium bedding, warm amber lighting, tropical nature view through large open window, photorealistic, 8k, no people, no text",
        "High-end commercial photography of a private terrace at a boutique hotel in Martinique at dusk, comfortable rattan outdoor seating, tropical landscape and sea view, string lights, photorealistic, 8k, no people, no text",
        "Professional commercial photography of a tropical breakfast setup on a wooden deck in Martinique, local fruits mangoes passion fruit pineapple, fresh pastries, morning golden Caribbean light, lush garden view, photorealistic, 8k, no people, no text",
    ],
}

SECTOR_TYPE_MAP = {
    "restaurant": "restaurant", "meal_delivery": "restaurant",
    "meal_takeaway": "restaurant", "food": "restaurant",
    "bakery": "cafe", "cafe": "cafe", "bar": "cafe",           # bakery → café/boulangerie
    "pharmacy": "medical", "doctor": "medical", "hospital": "medical",
    "dentist": "medical", "physiotherapist": "medical", "veterinary_care": "medical",
    "car_repair": "automotive", "car_dealer": "automotive", "car_wash": "automotive",
    "beauty_salon": "beauty", "hair_care": "beauty", "spa": "beauty", "nail_salon": "beauty",
    "gym": "beauty", "fitness_center": "beauty",
    "real_estate_agency": "professional", "lawyer": "professional",
    "accountant": "professional", "insurance_agency": "professional",
    "store": "retail", "clothing_store": "retail", "shoe_store": "retail",
    "florist": "retail", "jewelry_store": "retail", "electronics_store": "retail",
    "supermarket": "retail", "convenience_store": "retail",
    "tobacco_store": "retail", "newsagent": "retail", "book_store": "retail",
    "hardware_store": "retail", "pet_store": "retail", "toy_store": "retail",
    "gift_shop": "retail", "stationery": "retail",
    # hébergement (hôtels, B&B, campings, hébergements insolites type bulles/dômes)
    "lodging": "lodging", "hotel": "lodging", "motel": "lodging",
    "resort_hotel": "lodging", "extended_stay_hotel": "lodging",
    "guest_house": "lodging", "bed_and_breakfast": "lodging",
    "campground": "lodging", "rv_park": "lodging", "hostel": "lodging",
    "cottage": "lodging", "farmstay": "lodging", "inn": "lodging",
}


def _sanitize_json_strings(s: str) -> str:
    """Fix common LLM JSON issues: unescaped control chars inside string values."""
    result = []
    in_string = False
    escape_next = False
    for ch in s:
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == '\\':
            result.append(ch)
            escape_next = True
        elif ch == '"':
            in_string = not in_string
            result.append(ch)
        elif in_string and ord(ch) < 0x20:
            # Escape ALL control characters inside strings (newline, tab, CR, etc.)
            if ch == '\n':
                result.append('\\n')
            elif ch == '\r':
                result.append('\\r')
            elif ch == '\t':
                result.append('\\t')
            else:
                result.append(f'\\u{ord(ch):04x}')
        else:
            result.append(ch)
    return ''.join(result)
    return ''.join(result)


class LocalPulseManager:
    def __init__(self, business_data: dict, log_queue=None):
        self.business_data = business_data
        self.log_queue     = log_queue
        self.log_buffer    = None   # attached by orchestration task for polling
        self.business_id   = business_data.get("business_id")

        # Lazy-init providers only if keys are present
        self._gemini_ready = False
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                self._genai = genai
                self._gemini_ready = True
            except Exception:
                self._genai = None
        else:
            self._genai = None

        self.mistral_client = None
        mistral_key = os.environ.get("MISTRAL_API_KEY", "")
        if mistral_key:
            try:
                from mistralai import Mistral
                self.mistral_client = Mistral(api_key=mistral_key)
            except Exception:
                pass

        import asyncio
        try:
            self.loop = asyncio.get_running_loop()
        except Exception:
            self.loop = None

        try:
            import redis
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
        except Exception:
            self.redis_client = None

        self.sector         = self._detect_sector(business_data.get("types", []))
        self.sector_profile = SECTOR_PROFILES[self.sector]
        self.design_brief   = None

    # ──────────────────────────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────────────────────────

    def _detect_sector(self, types: list) -> str:
        for t in types:
            if t in SECTOR_TYPE_MAP:
                return SECTOR_TYPE_MAP[t]
        return "generic"

    def _push_log(self, agent: str, message: str, msg_type: str = "chat"):
        entry = {"agent": agent, "message": message, "type": msg_type}
        if self.log_queue and self.loop:
            self.loop.call_soon_threadsafe(self.log_queue.put_nowait, entry)
        if msg_type != "stream_token" and self.log_buffer is not None:
            self.log_buffer.append(entry)
        if self.redis_client and self.business_id:
            try:
                self.redis_client.rpush(f"logs:{self.business_id}", json.dumps(entry))
                self.redis_client.expire(f"logs:{self.business_id}", 3600)
            except Exception:
                pass

    def _build_dynamic_fal_prompts(self, needed: int) -> list:
        """Demande au LLM des prompts Flux SUR MESURE pour ce commerce précis,
        en s'appuyant sur son nom + ses avis Google réels — plutôt que des
        prompts génériques par secteur qui ratent les concepts spécifiques
        (ex: hébergement en bulle transparente, thème particulier, etc.).
        Fallback silencieux sur SECTOR_FAL_PROMPTS si l'appel échoue."""
        biz = self.business_data
        reviews = [r.get("text", "") for r in (biz.get("reviews") or []) if r.get("text")]
        review_snippets = " | ".join(r[:150] for r in reviews[:5]) or "aucun avis disponible"

        prompt = f"""Tu es directeur artistique spécialisé en photographie commerciale pour sites web professionnels en Martinique et Guadeloupe (Caraïbes françaises).
Tu prépares des prompts pour Flux Dev (génération d'images photoréalistes) pour le site web de CE commerce précis :

Nom : {biz.get('name')}
Secteur détecté : {self.sector_profile['label']}
Extraits d'avis clients Google (utilise-les pour identifier le CONCEPT RÉEL, la spécialité, l'ambiance, les produits phares) : {review_snippets}

RÈGLES STRICTES pour chaque prompt :
1. Commence TOUJOURS par "Professional commercial photography of"
2. Décris précisément CE QU'ON VOIT : les produits/services spécifiques à ce commerce (pas génériques)
3. CONTEXTE CARIBÉEN OBLIGATOIRE : intègre des marqueurs visuels Caraïbes françaises — végétation tropicale visible, bois créole, couleurs vives antillaises, lumière caraïbe intense, architecture locale
4. DIVERSITÉ ETHNIQUE ANTILLAISE : quand des personnes sont pertinentes (section équipe, accueil client), décris explicitement "Afro-Caribbean French professionals" ou "mixed-heritage Caribbean people" — jamais de personnages européens génériques
5. Précise l'ambiance lumineuse : "warm Caribbean sunlight" / "golden tropical hour" / "soft diffused tropical daylight"
6. Ajoute des détails photo : "shallow depth of field" / "sharp focus" / "bokeh background"
7. Termine CHAQUE prompt par : "photorealistic, 8k, professional DSLR, Martinique Caribbean atmosphere, no text"
8. Varie les sujets sur les {needed} prompts : 1 photo extérieure/devanture locale, 1-2 photos produits ou services en gros plan, 1 photo intérieure ambiance
9. Les photos de produits/intérieurs sans personnes : termine par "no people, no text"
10. JAMAIS de style illustratif, cartoon ou artistique — UNIQUEMENT photoréaliste

Génère exactement {needed} prompts en ANGLAIS, adaptés à CE commerce précis en contexte antillais.

Réponds UNIQUEMENT avec un tableau JSON de {needed} strings, sans markdown, sans explication. Exemple : ["Professional commercial photography of...", "Professional commercial photography of..."]"""

        try:
            raw = self._call(prompt, max_tokens=900)
            clean = raw.replace("```json", "").replace("```", "").strip()
            generated = json.loads(clean)
            if isinstance(generated, list) and generated and all(isinstance(p, str) and p.strip() for p in generated):
                self._push_log("Visions Artist", "✨ Prompts photo personnalisés générés pour ce commerce.", "chat")
                return generated[:needed]
        except Exception as e:
            self._push_log("Visions Artist", f"⚠️ Prompts sur mesure indisponibles, secteur générique utilisé : {e}", "system")

        return SECTOR_FAL_PROMPTS.get(self.sector, SECTOR_FAL_PROMPTS["generic"])[:needed]

    def _generate_images_fal(self, needed: int = 4) -> list:
        """Generate photos with fal.ai Flux Schnell. Returns list of image URLs."""
        fal_key = os.environ.get("FAL_KEY", "")
        if not fal_key:
            return []
        try:
            import fal_client
        except ImportError:
            return []

        os.environ["FAL_KEY"] = fal_key
        prompts = self._build_dynamic_fal_prompts(needed)
        urls = []

        for i, prompt_text in enumerate(prompts[:needed]):
            try:
                self._push_log("Visions Artist",
                    f"🎨 Génération photo {i+1}/{min(needed, len(prompts))} avec Flux AI...", "chat")
                for model_id, steps in [("fal-ai/flux/dev", 28), ("fal-ai/flux/schnell", 8)]:
                    try:
                        handler = fal_client.submit(
                            model_id,
                            arguments={
                                "prompt": prompt_text,
                                "image_size": "landscape_4_3",
                                "num_inference_steps": steps,
                                "guidance_scale": 3.5,
                                "enable_safety_checker": True,
                                "num_images": 1,
                            }
                        )
                        result = handler.get()
                        if result.get("images"):
                            url = result["images"][0]["url"]
                            urls.append(url)
                            self._push_log("Visions Artist", f"✅ Photo {i+1} prête ({model_id.split('/')[-1]})", "chat")
                            break
                    except Exception as model_err:
                        if "schnell" in model_id:
                            raise model_err
                        self._push_log("Visions Artist", f"⚠️ {model_id} indisponible, fallback schnell...", "system")
                        continue
            except Exception as e:
                self._push_log("Visions Artist", f"⚠️ Photo {i+1} ignorée : {e}", "chat")

        return urls

    def _build_image_search_keywords(self, needed: int) -> list:
        """Demande au LLM de courtes requêtes de recherche (3-6 mots, EN)
        décrivant les photos qui illustreraient fidèlement CE commerce —
        utilisé pour chercher sur Pexels quand Fal n'est pas dispo/échoue.
        Couvre les niches absentes des secteurs codés en dur (poissonnerie,
        hébergement insolite, etc.) car basé sur le commerce réel, pas un secteur figé."""
        biz = self.business_data
        reviews = [r.get("text", "") for r in (biz.get("reviews") or []) if r.get("text")]
        review_snippets = " | ".join(r[:150] for r in reviews[:5]) or "aucun avis disponible"

        prompt = f"""Commerce : {biz.get('name')}
Secteur détecté : {self.sector_profile['label']}
Extraits d'avis clients : {review_snippets}

Génère exactement {needed} requêtes de recherche d'images en ANGLAIS (3-5 mots chacune) pour trouver des photos professionnelles sur Pexels représentant CE commerce en contexte caribéen.

RÈGLES :
- Termes visuels concrets et spécifiques : "grilled fresh fish Caribbean plate" pas "local restaurant food"
- Intègre des marqueurs caribéens quand pertinent : "tropical", "Caribbean", "Antilles"
- Varie les angles : produit gros plan, intérieur ambiance, devanture extérieure
- Jamais de termes génériques comme "small business" ou "local shop"

Réponds UNIQUEMENT avec un tableau JSON de {needed} strings, sans markdown, sans explication."""

        try:
            raw = self._call(prompt, max_tokens=400)
            clean = raw.replace("```json", "").replace("```", "").strip()
            keywords = json.loads(clean)
            if isinstance(keywords, list) and keywords and all(isinstance(k, str) and k.strip() for k in keywords):
                return keywords[:needed]
        except Exception as e:
            self._push_log("Visions Artist", f"⚠️ Mots-clés Pexels indisponibles : {e}", "system")

        # Filet ultime si le LLM échoue aussi : secteur + nom du commerce
        return [f"{self.sector_profile['label']} {biz.get('name', '')}"] * needed

    def _search_pexels_images(self, query: str) -> str:
        pexels_key = os.environ.get("PEXELS_API_KEY", "")
        if not pexels_key:
            return None

        def _fetch(q: str):
            try:
                import requests
                resp = requests.get(
                    "https://api.pexels.com/v1/search",
                    headers={"Authorization": pexels_key},
                    params={"query": q, "per_page": 5, "orientation": "landscape", "size": "large"},
                    timeout=8,
                )
                resp.raise_for_status()
                photos = resp.json().get("photos", [])
                if photos:
                    best = max(photos, key=lambda p: p.get("liked", 0) or 0)
                    return best["src"].get("large2x") or best["src"]["large"]
            except Exception:
                pass
            return None

        url = _fetch(query)
        if url:
            return url

        short_query = " ".join(query.split()[:2])
        if short_query != query:
            url = _fetch(short_query)
            if url:
                self._push_log("Visions Artist", f"ℹ️ Pexels fallback query : « {short_query} »", "system")
                return url

        return None

    def _generate_images_pexels(self, needed: int = 4) -> list:
        """Fallback gratuit si Fal est absent/échoue : recherche d'images
        libres de droits sur Pexels via des mots-clés générés pour CE commerce."""
        if not os.environ.get("PEXELS_API_KEY"):
            return []
        keywords = self._build_image_search_keywords(needed)
        urls = []
        for i, kw in enumerate(keywords[:needed]):
            self._push_log("Visions Artist", f"🔎 Recherche Pexels {i+1}/{len(keywords[:needed])} : « {kw} »...", "chat")
            url = self._search_pexels_images(kw)
            if url:
                urls.append(url)
                self._push_log("Visions Artist", f"✅ Photo {i+1} trouvée", "chat")
            else:
                self._push_log("Visions Artist", f"⚠️ Aucun résultat Pexels pour « {kw} »", "chat")
        return urls

    def _call(self, prompt: str, max_tokens: int = 2048, system: str = "") -> str:
        """Call with provider fallback chain: gemini-3.5 → gemini-3.1 → gemini-2.5 → mistral-large → mistral-small."""
        last_error = None
        for provider in PROVIDERS_TEXT:
            try:
                result = self._call_provider(provider, prompt, max_tokens, system)
                return result
            except Exception as e:
                msg = str(e).lower()
                is_quota = any(k in msg for k in ['429', 'quota', 'resource_exhausted', 'rate_limit', 'retry_delay', 'limit exceeded', 'too many', 'prepayment'])
                if is_quota:
                    self._push_log("Système", f"⏭️ {provider['name']} quota atteint → provider suivant...", "system")
                    last_error = e
                    time.sleep(2)  # court délai pour éviter de saturer le provider suivant
                    continue
                raise  # Non-quota errors bubble up immediately
        raise last_error or RuntimeError("Tous les providers ont échoué")

    def _call_provider(self, provider: dict, prompt: str, max_tokens: int, system: str) -> str:
        """Single provider call — raises on any error."""
        if provider["type"] == "gemini":
            if not self._genai:
                raise Exception("429 no key")
            model = self._genai.GenerativeModel(
                provider["model"],
                system_instruction=system if system else None
            )
            resp = model.generate_content(
                prompt,
                generation_config=self._genai.GenerationConfig(max_output_tokens=max_tokens)
            )
            return resp.text

        elif provider["type"] == "mistral":
            if not self.mistral_client:
                raise Exception("429 no key")
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = self.mistral_client.chat.complete(
                model=provider["model"],
                messages=messages,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content

    def _stream_provider(self, provider: dict, prompt: str, system: str):
        """Returns a generator of text chunks for streaming HTML generation."""
        if provider["type"] == "gemini":
            if not self._genai:
                raise Exception("429 no key")
            model = self._genai.GenerativeModel(
                provider["model"],
                system_instruction=system if system else None
            )
            response = model.generate_content(
                prompt,
                generation_config=self._genai.GenerationConfig(max_output_tokens=65536),
                stream=True
            )
            for chunk in response:
                try:
                    yield chunk.text or ""
                except Exception:
                    yield ""

        elif provider["type"] == "mistral":
            if not self.mistral_client:
                raise Exception("429 no key")
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            with self.mistral_client.chat.stream(
                model=provider["model"],
                messages=messages,
                max_tokens=16384,
            ) as stream:
                for event in stream:
                    delta = event.data.choices[0].delta.content
                    yield delta or ""

    # ──────────────────────────────────────────────────────────────
    #  PHASE 0 — DESIGN BRIEF
    # ──────────────────────────────────────────────────────────────

    def run_design_crew(self) -> dict:
        """Phase 0 : Gemini call for design brief."""
        biz     = self.business_data
        profile = self.sector_profile

        self._push_log("Le Designer",
            f"🎨 Analyse du secteur **{profile['label']}** pour **{biz.get('name')}**...", "chat")

        prompt = f"""Tu es un Lead Designer expert en sites web PME françaises.

Crée le brief design complet pour **{biz.get('name')}** ({biz.get('address', '')}).
Secteur : {profile['label']}
Style de base : {profile['hint']}
Note Google : {biz.get('rating', 'N/A')}/5
Sections du site : {' > '.join(profile['sections'])}

Réponds UNIQUEMENT avec un JSON valide (aucun texte avant ou après) :
{{
  "template": "nom-du-concept-design",
  "sector": "{self.sector}",
  "colors": {{
    "primary": "#hex", "secondary": "#hex", "accent": "#hex",
    "background": "#hex", "surface": "#hex", "text": "#hex", "text_muted": "#hex"
  }},
  "fonts": {{"heading": "Nom Google Font", "body": "Nom Google Font"}},
  "hero": {{"style": "fullscreen-dark", "overlay_opacity": 0.6, "text_align": "center"}},
  "cards": {{"style": "glass", "border_radius": "rounded-xl"}},
  "buttons": {{"primary_style": "filled", "border_radius": "rounded-full"}},
  "mood": "3-5 adjectifs décrivant l'ambiance",
  "unique_angle": "Proposition de valeur unique pour ce commerce",
  "sections_order": {json.dumps(profile['sections'])},
  "animations": "elegant",
  "css_variables": {{
    "--color-primary": "#hex", "--color-secondary": "#hex", "--color-accent": "#hex",
    "--color-bg": "#hex", "--color-surface": "#hex", "--color-text": "#hex",
    "--font-heading": "'Nom', serif", "--font-body": "'Nom', sans-serif",
    "--radius-card": "1rem", "--radius-btn": "9999px"
  }}
}}"""

        try:
            raw = self._call(prompt, max_tokens=2000)
            raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
            raw = re.sub(r'\s*```$', '', raw.strip())
            m = re.search(r'\{[\s\S]*\}', raw)
            json_str = m.group(0) if m else raw
            # Remove trailing commas and sanitize control chars
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            json_str = _sanitize_json_strings(json_str)
            self.design_brief = json.loads(json_str)
        except Exception as e:
            self._push_log("Le Designer", f"⚠️ Brief simplifié (fallback) : {e}", "chat")
            self.design_brief = {
                "template": "universal-modern", "sector": self.sector,
                "colors": {"primary": "#0071E3", "secondary": "#1A1A2E",
                           "background": "#FFFFFF", "text": "#1A1A1A"},
                "fonts": {"heading": "Playfair Display", "body": "Inter"},
                "mood": "moderne, professionnel", "unique_angle": biz.get('name', ''),
                "sections_order": profile['sections'],
                "css_variables": {"--color-primary": "#0071E3"},
            }

        self._push_log("Le Designer",
            f"✅ Concept : **{self.design_brief.get('template', 'moderne')}** — {self.design_brief.get('mood', '')}",
            "chat")
        return self.design_brief

    # ──────────────────────────────────────────────────────────────
    #  PHASE 1 — INVESTIGATION + COPYWRITING
    # ──────────────────────────────────────────────────────────────

    def run_prep_crew(self) -> dict:
        """Phase 1 : Gemini calls for investigation + copywriting."""
        biz     = self.business_data
        profile = self.sector_profile
        design_summary = f"Concept : {self.design_brief.get('template')} | Mood : {self.design_brief.get('mood')}" \
                         if self.design_brief else ""

        # ── Investigation ──
        self._push_log("L'Éclaireur",
            f"🔍 Investigation de **{biz.get('name')}** ({biz.get('address', '')})...", "chat")

        invest_prompt = f"""Tu es un consultant senior spécialisé dans la transformation digitale des PME françaises.
Tu analyses ce commerce pour préparer un commercial à une prise de contact. Le rapport doit être exhaustif et actionnable.

════ DONNÉES DU COMMERCE ════
Nom : {biz.get('name')}
Adresse : {biz.get('address', '')}
Secteur : {profile['label']}
Note Google : {biz.get('rating', 'N/A')}/5 ({biz.get('user_ratings_total', 0)} avis)
Téléphone : {biz.get('phone', 'non communiqué')}
Site web connu : {biz.get('website', 'non renseigné')}

Rédige un rapport complet structuré en 7 sections :

## 1. 📊 FICHE IDENTITÉ
Présentation du commerce, type d'établissement, clientèle cible probable, positionnement marché estimé, ancienneté supposée et taille (TPE/PME).

## 2. 🔍 DIAGNOSTIC DIGITAL ACTUEL
Analyse détaillée de la présence en ligne :
- Site web : existence, qualité supposée, responsive/mobile, SEO visible
- Fiche Google My Business : complétude, photos, réponses aux avis
- Réseaux sociaux : présence estimée (Facebook, Instagram, TikTok)
- Note et avis : analyse qualitative des {biz.get('user_ratings_total', 0)} avis (points récurrents positifs/négatifs)
- Visibilité locale vs concurrents
Score Digital Gap : X/10 (10 = totalement absent du digital)

## 3. ⚡ OPPORTUNITÉS IDENTIFIÉES
Liste des 5 opportunités prioritaires avec impact estimé (CA, clients, visibilité) :
1. [Opportunité] → Impact estimé : ...
2. ...

## 4. 💡 RECOMMANDATIONS SERVICES
Solutions concrètes à proposer au propriétaire, par ordre de priorité :
1. Site vitrine professionnel → Pourquoi c'est urgent, ROI attendu
2. Référencement local SEO → Mots-clés cibles, visibilité estimée
3. Gestion avis Google → Impact sur le chiffre d'affaires
4. Présence réseaux sociaux → Quel réseau, quelle fréquence
5. [Autres selon le secteur]

## 5. 🎯 SCRIPT COMMERCIAL (pour le commercial)
Arguments clés pour convaincre le propriétaire :
- Accroche d'entrée (phrase d'ouverture percutante)
- 3 douleurs à mentionner (ce qu'il perd sans présence digitale)
- 3 bénéfices concrets à projeter (chiffres, exemples secteur)
- Réponses aux 3 objections classiques (prix, temps, "je n'en ai pas besoin")
- Proposition de valeur finale (closing)

## 6. 📈 PROJECTION ROI 12 MOIS
Estimation de l'impact d'une transformation digitale complète :
- Nouveaux clients mensuels estimés : +X
- Augmentation CA estimée : +X%
- Valeur client annuelle : X€
- ROI investissement digital : Xx en 12 mois"""

        try:
            report = self._call(invest_prompt, max_tokens=4000)
            self._push_log("L'Éclaireur", "✅ Rapport d'investigation terminé.", "chat")
        except Exception as e:
            report = f"Analyse de {biz.get('name')} — Commerce local secteur {profile['label']}."
            self._push_log("L'Éclaireur", f"⚠️ Analyse simplifiée : {e}", "chat")

        # ── Copywriting ──
        self._push_log("Le Stratège",
            f"✍️ Rédaction du copywriting pour **{biz.get('name')}**...", "chat")

        copy_prompt = f"""Tu es un copywriter senior spécialisé en PME françaises et conversion web.

════ CONTEXTE ════
Commerce : {biz.get('name')} | Secteur : {profile['label']}
Adresse : {biz.get('address', '')} | Note : {biz.get('rating', 'N/A')}/5
{f"Brief design : {design_summary}" if design_summary else ""}

Rapport d'analyse :
{report[:2000]}

════ PRODUCTION COPYWRITING COMPLÈTE ════

## ACCROCHE & SLOGAN
- Slogan principal (5-8 mots, mémorable, français)
- Sous-titre hero (15-20 mots, bénéfice client immédiat)
- Tagline secondaire (variante pour A/B test)

## SECTION HERO
Texte principal du hero (2-3 phrases percutantes, orientées bénéfice client, en français)

## À PROPOS
2 paragraphes (120 mots chacun) :
- Paragraphe 1 : histoire, fondateur, ancrage local, passion du métier
- Paragraphe 2 : valeurs, engagement qualité, clientèle fidèle, différence

## SERVICES / PRODUITS PHARES
{profile['special_instructions']}
Pour chaque service/produit : Nom accrocheur | Description 30 mots | Prix estimé | Bénéfice client

## ARGUMENTS DIFFÉRENCIANTS
3 arguments forts vs la concurrence (format : Titre court + explication 20 mots)

## PREUVES SOCIALES
5 témoignages clients fictifs mais ultra-réalistes :
- Prénom + initiale nom + ville + note (/5) + texte 40 mots
- Varier les profils (âge, situation, raison de visite)

## APPELS À L'ACTION
- CTA principal : "{profile['cta_primary']}" (contexte d'utilisation)
- CTA secondaire : "{profile['cta_secondary']}" (contexte)
- CTA urgence : offre limitée ou promotion type

## SEO LOCAL
5 mots-clés prioritaires pour le référencement local de {biz.get('name')}"""

        try:
            copywriting = self._call(copy_prompt, max_tokens=3500)
            self._push_log("Le Stratège", "✅ Copywriting terminé.", "chat")
        except Exception as e:
            copywriting = f"Bienvenue chez {biz.get('name')} — votre expert {profile['label']} local."
            self._push_log("Le Stratège", f"⚠️ Copy simplifié : {e}", "chat")

        return {
            "report": report,
            "copywriting": copywriting,
            "ai_photos": "",
            "design": json.dumps(self.design_brief) if self.design_brief else "",
        }

    # ──────────────────────────────────────────────────────────────
    #  HTML GENERATION (streaming)
    # ──────────────────────────────────────────────────────────────

    def _generate_html_streaming(self, prep_data: dict, all_photos: list = None) -> str:
        biz     = self.business_data
        profile = self.sector_profile
        design  = self.design_brief or {}

        name    = biz.get("name", "Mon Commerce")
        address = biz.get("address", "")
        phone   = biz.get("phone", "")
        rating  = biz.get("rating", 0)

        whatsapp = re.sub(r'[\s\-\.]', '', phone)
        if whatsapp.startswith("0"):
            whatsapp = "+33" + whatsapp[1:]

        encoded_address = urllib.parse.quote(address)
        report      = prep_data.get("report", "")[:3000]
        copywriting = prep_data.get("copywriting", "")[:2000]

        # Proxy Google Places photo URLs through backend to avoid CORS / API-key referrer issues
        def _proxify(url: str) -> str:
            if "places.googleapis.com" in url or "maps.googleapis.com" in url:
                return f"/photo?url={urllib.parse.quote(url, safe='')}"
            return url

        if all_photos is None:
            # Appelé sans liste pré-calculée (ex: appel direct hors run_build_crew)
            # → on construit ici, en dernier recours. Sinon on réutilise celle
            # déjà générée par run_build_crew pour éviter un 2e appel Fal payant.
            biz_photos = [p for p in (self.business_data.get("photos") or [])
                          if isinstance(p, str) and p.startswith("http")]
            fallbacks  = SECTOR_UNSPLASH.get(self.sector, SECTOR_UNSPLASH["generic"])
            fal_photos = []
            if len(biz_photos) < 3 and os.environ.get("FAL_KEY"):
                needed = max(0, 6 - len(biz_photos))
                self._push_log("Visions Artist",
                    f"📸 Pas assez de photos Google ({len(biz_photos)}) — génération de {needed} images avec Flux AI...", "chat")
                fal_photos = self._generate_images_fal(needed)
            pexels_photos = []
            if len(biz_photos) + len(fal_photos) < 3 and os.environ.get("PEXELS_API_KEY"):
                needed2 = max(0, 6 - len(biz_photos) - len(fal_photos))
                pexels_photos = self._generate_images_pexels(needed2)
            _seen2: set = set()
            _unique2: list = []
            for _p in (biz_photos + fal_photos + pexels_photos):
                if _p not in _seen2:
                    _seen2.add(_p)
                    _unique2.append(_p)
            for _p in fallbacks:
                if len(_unique2) >= 10:
                    break
                if _p not in _seen2:
                    _seen2.add(_p)
                    _unique2.append(_p)
            all_photos = _unique2[:10]

        all_photos     = [_proxify(p) for p in all_photos]
        hero_photo     = all_photos[0]
        gallery_photos = all_photos[:8]

        colors      = design.get("colors", {})
        fonts       = design.get("fonts", {})
        css_vars    = design.get("css_variables", {})
        hero_cfg    = design.get("hero", {})
        cta_primary = profile.get("cta_primary", "Nous contacter")
        cta_secondary = profile.get("cta_secondary", "En savoir plus")
        mood        = design.get("mood", "moderne et professionnel")
        template_name = design.get("template", "universal-modern")
        sections_order = design.get("sections_order", profile["sections"])

        css_vars_block = "\n".join(f"        {k}: {v};" for k, v in css_vars.items())

        prompt = f"""Tu es un développeur web senior expert HTML/CSS/Tailwind. Génère le site web complet et professionnel pour cette PME française.

════ BRIEF DESIGN — "{template_name.upper()}" ════
Secteur : {profile['label']} | Ambiance : {mood}
Primary : {colors.get('primary', '#0071E3')} | Secondary : {colors.get('secondary', '#1A1A2E')}
Accent : {colors.get('accent', '#FF6B35')} | Background : {colors.get('background', '#FFFFFF')}
Titres : {fonts.get('heading', 'Playfair Display')} | Corps : {fonts.get('body', 'Inter')}
Hero style : {hero_cfg.get('style', 'fullscreen-dark')}

════ COMMERCE ════
Nom : {name} | Adresse : {address} | Tél : {phone}
Note Google : {rating}/5 | Photo hero : {hero_photo}

════ RAPPORT & COPYWRITING ════
{report}

{copywriting}

════ SECTIONS : {' → '.join(sections_order)} ════
{profile['special_instructions']}

════ PHOTOS À UTILISER (URLs exactes — n'en invente AUCUNE autre) ════
{chr(10).join(f"Photo {i+1} : {url}" for i, url in enumerate(gallery_photos))}

Règle absolue : chaque <img> doit avoir src= pointant vers une de ces URLs. JAMAIS de src inventé, JAMAIS de chemin local, JAMAIS de placeholder.com. Si tu as besoin de plus de photos, réutilise celles de la liste ci-dessus.

════ EXIGENCES TECHNIQUES ════
HEAD :
- <script src="https://cdn.tailwindcss.com"></script>
- Google Fonts pour {fonts.get('heading', 'Playfair Display')} et {fonts.get('body', 'Inter')}
- AOS : CDN + AOS.init({{duration:800, once:true}})
- CSS :root avec variables :
  :root {{ {css_vars_block or f'--color-primary: {colors.get("primary","#0071E3")};'} }}

NAV : position:fixed; top:0; left:0; right:0; z-index:9999; transition:background 0.3s ease;
Ajouter ce JavaScript en fin de <body> pour le scroll (OBLIGATOIRE) :
<script>
const nav = document.querySelector('nav');
window.addEventListener('scroll', () => {{
  if (window.scrollY > 60) {{
    nav.style.background = 'rgba(10,10,20,0.97)';
    nav.style.backdropFilter = 'blur(20px)';
    nav.style.boxShadow = '0 2px 30px rgba(0,0,0,0.5)';
  }} else {{
    nav.style.background = 'rgba(10,10,20,0.15)';
    nav.style.backdropFilter = 'blur(10px)';
    nav.style.boxShadow = 'none';
  }}
}});
</script>
Logo texte + liens smooth-scroll vers les sections + bouton CTA "{cta_primary}"
HERO (COPIE EXACTEMENT CE CODE — NE CHANGE PAS L'URL) :
<section style="background-image: url('{hero_photo}'); min-height:100vh; background-size:cover; background-position:center; position:relative;">
  <div style="position:absolute;inset:0;background:rgba(0,0,0,0.55)"></div>
  <div style="position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:2rem;padding-top:calc(80px + 2rem);">
    <!-- H1 percutant, sous-titre, 2 boutons CTA, badge ⭐{rating}/5 -->
  </div>
</section>
⚠️ L'URL hero est : {hero_photo} — copie-la EXACTEMENT dans background-image, ne la remplace pas.
⚠️ Le padding-top:calc(80px + 2rem) est OBLIGATOIRE pour que le contenu ne soit pas masqué par la nav fixe.
SECTIONS : générer CHAQUE section dans l'ordre {' → '.join(sections_order)}
IMAGES : pour chaque <img>, utilise les URLs de la liste ci-dessus. Photo 1 = hero/principal, Photos 2-4 = about/ambiance, Photos 3-8 = galerie.
MAPS : <iframe src="https://maps.google.com/maps?q={encoded_address}&output=embed" width="100%" height="300" style="border:0;border-radius:1rem;" loading="lazy"></iframe>
WHATSAPP : bouton fixe bas-droite → https://wa.me/{whatsapp or '+33600000000'}
FOOTER : fond sombre, logo, adresse, tél, liens, © {name} 2026

QUALITÉ : mobile-first, data-aos sur chaque section, hover sur tous les éléments, textes en français.

COMMENCE DIRECTEMENT par <!DOCTYPE html>"""

        self._push_log("L'Ingénieur",
            f"🏗️ Génération HTML **{template_name}** pour **{name}**...", "chat")

        html_chunks = []
        token_batch = []
        token_count = 0

        system_html = "Tu génères uniquement du HTML valide. Commence par <!DOCTYPE html>. Aucun markdown, aucun commentaire."

        # Try providers in order for HTML generation
        stream_iter = None
        for provider in PROVIDERS:
            try:
                stream_iter = self._stream_provider(provider, prompt, system_html)
                break
            except Exception as e:
                msg = str(e).lower()
                is_quota = any(k in msg for k in ['429', 'quota', 'resource_exhausted', 'rate_limit', 'retry_delay', 'limit exceeded', 'too many', 'prepayment'])
                if is_quota:
                    self._push_log("Système", f"⏭️ HTML: {provider['name']} quota → suivant...", "system")
                    time.sleep(2)
                    continue
                raise

        if stream_iter is None:
            raise RuntimeError("Tous les providers ont échoué pour la génération HTML")

        for text in stream_iter:
            if text:
                html_chunks.append(text)
                token_batch.append(text)
                token_count += 1
                if token_count % 8 == 0:
                    self._push_log("L'Ingénieur", "".join(token_batch), "stream_token")
                    token_batch = []

        if token_batch:
            self._push_log("L'Ingénieur", "".join(token_batch), "stream_token")

        full_html = "".join(html_chunks)

        # Strip markdown fences if Gemini wraps output
        full_html = re.sub(r'^```(?:html)?\s*', '', full_html.strip())
        full_html = re.sub(r'\s*```$', '', full_html.strip())

        self._push_log("L'Ingénieur",
            f"✅ Site généré ! {len(full_html):,} caractères.", "chat")
        return full_html

    # ──────────────────────────────────────────────────────────────
    #  TEMPLATE ENGINE — structured slot extraction + Jinja2 render
    # ──────────────────────────────────────────────────────────────

    SECTOR_TEMPLATE = {
        "cafe":         "artisan_warmth",
        "restaurant":   "gastro_noir",
        "beauty":       "beauty_nude",
        "automotive":   "garage_bold",
        "professional": "pro_trust",
        "medical":      "sante_zen",
        # retail + generic fall back to LLM generation
    }

    def _extract_content_slots(self, prep_data: dict) -> dict:
        """LLM call to produce structured content slots from real business data."""
        biz = self.business_data
        profile = self.sector_profile
        report = prep_data.get("report", "")[:2000]
        reviews_raw = biz.get("reviews", [])

        # Build reviews block for the prompt
        positive = [r for r in reviews_raw if (r.get("rating") or 0) >= 4]
        if positive:
            reviews_block = "\n".join(
                f'- {r["author"]} ({r["rating"]}★, {r.get("date","récemment")}): "{r["text"][:300]}"'
                for r in positive[:10]
            )
        else:
            reviews_block = "Aucun avis dispo — génère 4 témoignages 5★ réalistes et variés en français."

        prompt = f"""Tu es un expert copywriter marketing local. Génère le contenu structuré pour le site de ce commerce.

COMMERCE : {biz.get("name")} | {biz.get("address", "")}
SECTEUR : {profile["label"]}
NOTE GOOGLE : {biz.get("rating", 4.0)}/5 ({biz.get("user_ratings_total", 0)} avis)
SITE WEB EXISTANT : {biz.get("website", "aucun")}
RAPPORT : {report}

AVIS GOOGLE POSITIFS (utilise-les TOUS comme témoignages) :
{reviews_block}

Réponds UNIQUEMENT avec du JSON valide (pas de markdown, pas de texte avant/après) :
{{
  "hero": {{
    "tagline": "Accroche max 8 mots, percutante et mémorable",
    "subtitle": "Phrase descriptive 12-15 mots qui explique la valeur unique"
  }},
  "about": {{
    "text": "Paragraphe 3-4 phrases chaleureux sur le savoir-faire, l'histoire, l'ancrage local",
    "highlight": "1 chiffre ou fait fort (ex: Artisan depuis 1987 · 500 clients fidèles)"
  }},
  "offerings": [
    {{
      "category": "Nom de catégorie",
      "emoji": "emoji pertinent",
      "items": [
        {{"name": "Nom précis", "price": "X.XX€", "desc": "Description courte appétissante"}}
      ]
    }}
  ],
  "testimonials": [
    {{"text": "Texte verbatim ou synthèse fidèle", "author": "Prénom N.", "rating": 5, "date": "Il y a X semaines"}}
  ],
  "stats": [
    {{"value": "4.5★", "label": "Note Google"}},
    {{"value": "523", "label": "Avis clients"}},
    {{"value": "Depuis 1987", "label": "Savoir-faire"}}
  ]
}}

RÈGLES OBLIGATOIRES :
- offerings : {profile["special_instructions"]}
- Génère TOUTES les catégories pertinentes pour ce secteur avec des prix typiques France
- testimonials : reprends TOUS les avis positifs réels. S'il n'y en a pas, invente-en 4 réalistes
- stats[2] : déduis l'ancienneté du nom ou du rapport, sinon mets "Qualité · Proximité"
- Tout en FRANÇAIS sauf les noms propres"""

        self._push_log("Le Rédacteur", f"✍️ Extraction du contenu structuré pour **{biz.get('name')}**...", "chat")
        try:
            raw = self._call(prompt, max_tokens=3000)
            # Strip markdown code fences
            raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
            raw = re.sub(r'\s*```$', '', raw.strip())
            # Extract the outermost JSON object
            m = re.search(r'\{[\s\S]*\}', raw)
            json_str = m.group(0) if m else raw
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            json_str = _sanitize_json_strings(json_str)
            slots = json.loads(json_str)
            self._push_log("Le Rédacteur", f"✅ Contenu extrait : {len(slots.get('offerings', []))} catégories · {len(slots.get('testimonials', []))} témoignages", "chat")
            return slots
        except Exception as e:
            self._push_log("Le Rédacteur", f"⚠️ Fallback contenu : {e}", "system")
            return {
                "hero": {"tagline": biz.get("name", ""), "subtitle": biz.get("address", "")},
                "about": {"text": f"Bienvenue chez {biz.get('name')}.", "highlight": ""},
                "offerings": [], "testimonials": [],
                "stats": [{"value": str(biz.get("rating", 4.0)), "label": "Note Google"},
                          {"value": str(biz.get("user_ratings_total", 0)), "label": "Avis"}],
            }

    def _render_from_template(self, content_slots: dict, all_photos: list) -> str:
        """Render a Jinja2 sector template with the extracted content."""
        import os as _os
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        template_name = self.SECTOR_TEMPLATE.get(self.sector)
        if not template_name:
            return ""

        template_dir = _os.path.join(_os.path.dirname(__file__), "..", "templates", "sectors")
        template_dir = _os.path.abspath(template_dir)
        tpl_path = _os.path.join(template_dir, f"{template_name}.html")
        if not _os.path.exists(tpl_path):
            self._push_log("L'Ingénieur", f"⚠️ Template {template_name}.html introuvable — génération LLM", "system")
            return ""

        biz = self.business_data
        phone = biz.get("phone", "")
        whatsapp = re.sub(r'[\s\-\.]', '', phone)
        if whatsapp.startswith("0"):
            whatsapp = "+33" + whatsapp[1:]

        encoded_address = urllib.parse.quote(biz.get("address", ""))
        maps_embed = f"https://maps.google.com/maps?q={encoded_address}&output=embed"

        biz_ctx = {
            "name": biz.get("name", "Mon Commerce"),
            "address": biz.get("address", ""),
            "phone": phone,
            "whatsapp": whatsapp or "+33600000000",
            "rating": biz.get("rating", 0),
            "ratings_total": biz.get("user_ratings_total", 0),
            "website": biz.get("website", ""),
            "maps_embed": maps_embed,
        }

        env = Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html"]))
        tpl = env.get_template(f"{template_name}.html")
        html = tpl.render(biz=biz_ctx, photos=all_photos, content=content_slots)
        self._push_log("L'Ingénieur", f"✅ Template **{template_name}** rendu : {len(html):,} caractères.", "chat")
        return html

    # ──────────────────────────────────────────────────────────────
    #  PHASE 2 — BUILD (HTML + email)
    # ──────────────────────────────────────────────────────────────

    def run_build_crew(self, prep_data: dict) -> dict:
        # ── Build photo list (shared between template & LLM paths) ──
        biz_photos = [p for p in (self.business_data.get("photos") or [])
                      if isinstance(p, str) and p.startswith("http")]
        fallbacks  = SECTOR_UNSPLASH.get(self.sector, SECTOR_UNSPLASH["generic"])
        fal_photos = []
        if len(biz_photos) < 3 and os.environ.get("FAL_KEY"):
            needed = max(0, 6 - len(biz_photos))
            self._push_log("Visions Artist",
                f"📸 {len(biz_photos)} photos Google — génération de {needed} images Flux AI...", "chat")
            fal_photos = self._generate_images_fal(needed)

        # Fallback gratuit si Fal absent/échoue : recherche Pexels par mots-clés
        # propres à CE commerce (couvre les niches hors des 8 secteurs codés en dur).
        pexels_photos = []
        if len(biz_photos) + len(fal_photos) < 3 and os.environ.get("PEXELS_API_KEY"):
            needed2 = max(0, 6 - len(biz_photos) - len(fal_photos))
            self._push_log("Visions Artist",
                f"🔎 Toujours pas assez de photos — recherche Pexels de {needed2} images...", "chat")
            pexels_photos = self._generate_images_pexels(needed2)

        def _proxify(url: str) -> str:
            if "places.googleapis.com" in url or "maps.googleapis.com" in url:
                return f"/photo?url={urllib.parse.quote(url, safe='')}"
            return url

        # Deduplicate while preserving order, then pad with fallbacks if still short
        _seen: set = set()
        _unique: list = []
        for _p in (biz_photos + fal_photos + pexels_photos):
            if _p not in _seen:
                _seen.add(_p)
                _unique.append(_p)
        for _p in fallbacks:
            if len(_unique) >= 10:
                break
            if _p not in _seen:
                _seen.add(_p)
                _unique.append(_p)
        raw_photos = _unique[:10]

        # ── Try template-based generation first ──
        html = ""
        if self.sector in self.SECTOR_TEMPLATE:
            content_slots = self._extract_content_slots(prep_data)
            proxified = [_proxify(p) for p in raw_photos]
            html = self._render_from_template(content_slots, proxified)

        # ── Fallback: full LLM generation (proxification faite à l'intérieur) ──
        if not html:
            html = self._generate_html_streaming(prep_data, all_photos=raw_photos)

        self._push_log("Le Closer",
            f"📧 Rédaction de l'email de prospection...", "chat")

        biz        = self.business_data
        report     = prep_data.get("report", "")[:1200]
        copywrite  = prep_data.get("copywriting", "")[:500]

        has_website = bool(biz.get("website"))
        website_line = f"Site web actuel : {biz.get('website')}" if has_website \
                       else "Site web actuel : aucun site détecté"

        owner_first = biz.get("owner_first_name", "") or ""
        owner_last  = biz.get("owner_last_name", "")  or ""
        owner_name  = (owner_first + " " + owner_last).strip()
        salutation  = owner_first.strip() if owner_first else ""
        salut_line  = (f'Commence OBLIGATOIREMENT par "Bonjour {salutation}," seul sur la première ligne.'
                       if salutation else
                       'Commence OBLIGATOIREMENT par "Bonjour," seul sur la première ligne (prénom indisponible — ne mets pas le nom du commerce).')
        has_reviews = biz.get('user_ratings_total', 0) > 0
        rating_line = f"avec {biz.get('rating')}/5 ({biz.get('user_ratings_total')} avis Google)" if has_reviews else "sans visibilité en ligne"
        score       = biz.get("potential_score", 0)

        email_prompt = f"""Tu es Ludovic, fondateur de Pulse-PME. Tu as DÉJÀ créé un site web de démonstration personnalisé pour ce commerce — il est en ligne maintenant.
Tu écris un email de prospection court, percutant, personnalisé. Objectif unique : que le gérant accepte 15 minutes pour voir la démo en live.

════ DONNÉES DU COMMERCE ════
Nom : {biz.get('name')}
Secteur : {self.sector_profile['label']}
Adresse : {biz.get('address', '')}
Présence Google : {rating_line}
Score présence digitale : {score:.1f}/10 (plus c'est bas = plus de clients perdus chaque jour)
{website_line}

Rapport d'analyse (utilise CES insights concrets — chiffres, lacunes, concurrents) :
{report}

Copywriting du site démo (inspire-toi du ton et des arguments pour personnaliser) :
{copywrite}

════ STRUCTURE EN 3 BLOCS OBLIGATOIRES ════

{salut_line}

BLOC 1 — ACCROCHE + POINTS DE DOULEUR (5-6 lignes, vouvoiement)
- Phrase 1 : observation ultra-spécifique sur CE commerce (leur note Google, leur secteur, leur rue, ce que leurs clients disent) — quelque chose qu'on ne pourrait dire qu'à EUX.
- Phrase 2-3 : le problème-douleur concret. Aujourd'hui, leurs clients potentiels cherchent sur Google avant de se déplacer. Sans site professionnel, sans fiche Google optimisée, sans avis récents — ces clients CHOISISSENT un concurrent qui a pris le virage digital. Chaque semaine sans présence en ligne = des clients perdus qui ne reviendront pas.
- Phrase 4 : appuie sur le manque d'identité numérique complète — pas seulement l'absence de site, mais aussi : pas de SEO local, pas d'avis gérés, pas de visibilité sur Maps. Leurs concurrents qui font ça capturent des clients qui auraient dû venir chez eux.

BLOC 2 — QUI EST PULSE-PME + PREUVE + OFFRE CLÉ EN MAIN (5-6 lignes, vouvoiement)
- Phrase 1 : te présenter brièvement — "Je m'appelle Ludovic, je dirige Pulse-PME : j'aide les commerces locaux comme le vôtre à exister en ligne sans qu'ils aient à s'en occuper. J'ai déjà analysé votre présence et créé votre site de démonstration — il vous attend."
- Phrase 2 — INSISTER explicitement sur le zéro-effort, c'est le cœur de l'offre : vous ne faites RIEN. Pulse-PME s'occupe de TOUT de A à Z — création du site, hébergement, mises à jour, gestion de la fiche Google et des avis clients, visibilité locale. Le gérant garde 100% de son temps pour son métier ; Pulse-PME devient son service digital externalisé, clé en main. Formuler ça de façon concrète et chaleureuse, pas comme une liste.
- Phrase 3-4 : 2 bénéfices ultra-concrets spécifiques à leur secteur (basés sur le copywriting et le rapport). Ex pour un restaurant : "Vos menus en ligne avec photos, et vos avis Google affichés en temps réel — vos clients réservent directement depuis le site." Adapter au secteur {self.sector_profile['label']}.
- Phrase 5 : "Pour démarrer : 49€/mois, sans engagement, résiliable à tout moment. Aucun frais caché — et aucune action technique de votre part, jamais."

BLOC 3 — CTA + MICRO-URGENCE (3-4 lignes, vouvoiement)
- "Je vous propose 15 minutes ensemble pour vous montrer votre démo en live — vous verrez exactement ce que vos clients verront."
- Micro-urgence : "La démonstration personnalisée que j'ai créée pour vous ne restera pas disponible indéfiniment. Si vous voulez la voir avant qu'elle soit supprimée, répondez à cet email."
- Dernière ligne : invitation directe à répondre.

Signature :
Ludovic
Fondateur — Pulse-PME

════ RÈGLES ABSOLUES ════
- VOUVOIEMENT OBLIGATOIRE partout : "vous", "votre", "vos", "vous-même". JAMAIS "tu", "ton", "ta", "tes".
- Jamais "Je me permets", "Dans le cadre de", "Madame/Monsieur", "Cordialement", "synergies"
- Les points de douleur doivent être CONCRETS et SPÉCIFIQUES à leur situation réelle (utilise le rapport)
- Ton : direct, chaleureux, professionnel — expert qui a fait le travail, pas commercial qui démarchent
- Les données du rapport doivent apparaître dans les blocs (chiffres précis, pas de généralités)
- Longueur totale : 22-28 lignes. Email complet et impactant.
- Tout en français

Écris l'email complet, directement, sans objet ni balise HTML."""

        def _is_truncated(text: str) -> bool:
            if not text:
                return True
            too_short   = len(text.split()) < 80
            missing_sig = not any(s in text for s in ["Ludovic", "Pulse-PME", "Bonne journée"])
            mid_sentence = text.rstrip()[-1] not in '.!?\n"\'…'
            return mid_sentence or (too_short and missing_sig)

        retry_email_prompt = f"""Tu es Ludovic, fondateur de Pulse-PME. Écris un email de prospection COMPLET (22-28 lignes) en français pour {biz.get('name')} ({self.sector_profile['label']}).

L'email doit :
1. {salut_line}
2. Mentionner leur note Google ({rating_line}) et score digital ({score:.1f}/10)
3. Expliquer que tu as déjà créé leur site de démo
4. Proposer 15 minutes pour la voir en live
5. Se terminer par : "Bonne journée,\nLudovic\nFondateur — Pulse-PME"

VOUVOIEMENT OBLIGATOIRE. Email complet, sans objet ni balise HTML."""

        try:
            email_text = self._call(email_prompt, max_tokens=3500)
            email_text = re.sub(r'---\s*EMAIL CONTENT (START|END)\s*---', '', email_text).strip()
            if _is_truncated(email_text):
                self._push_log("Le Closer", "⚠️ Email tronqué — nouvelle tentative avec prompt simplifié...", "system")
                email_text = self._call(retry_email_prompt, max_tokens=2000)
                email_text = re.sub(r'---\s*EMAIL CONTENT (START|END)\s*---', '', email_text).strip()
            if _is_truncated(email_text):
                email_text = email_text.rstrip() + "\n\nBonne journée,\nLudovic | Pulse-PME"
                self._push_log("Le Closer", "⚠️ Email toujours court — signature forcée.", "system")
            else:
                self._push_log("Le Closer", "✅ Email de prospection personnalisé prêt.", "chat")
        except Exception as e:
            email_text = (f"Bonjour,\n\nJe viens de créer un site de démonstration spécialement pour "
                          f"{biz.get('name')}. Seriez-vous disponible 5 minutes pour le découvrir ?\n\n"
                          f"Bonne journée,\nLudovic | Pulse-PME")
            self._push_log("Le Closer", f"⚠️ Email simplifié : {e}", "chat")

        return {"html": html, "email": email_text}

    # ──────────────────────────────────────────────────────────────
    #  PHASE 3 — DEPLOY
    # ──────────────────────────────────────────────────────────────

    def run_deploy_crew(self, html_content: str) -> str:
        from backend.agents.tools import VercelDeployTool
        tool = VercelDeployTool()
        return tool._run(html_content, self.business_id)
