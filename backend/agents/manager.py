import urllib.parse
import re
import os
import json
import time

# ─── Provider fallback chain ──────────────────────────────────────────────────
# Order: mistral-large → gemini-3.5-flash → gemini-3.1-flash-lite → gemini-2.5-flash
# Mistral en premier pendant activation du billing Gemini (peut prendre 24-48h).
# A provider is skipped if its API key is missing OR if it returns a quota/rate error.

PROVIDERS = [
    {"name": "mistral-large",        "type": "mistral", "model": "mistral-large-latest"},
    {"name": "gemini-3.5-flash",     "type": "gemini",  "model": "gemini-3.5-flash"},
    {"name": "gemini-3.1-flash-lite", "type": "gemini",  "model": "gemini-3.1-flash-lite"},
    {"name": "gemini-2.5-flash",     "type": "gemini",  "model": "gemini-2.5-flash"},
]

PROVIDERS_TEXT = [
    {"name": "mistral-large",        "type": "mistral", "model": "mistral-large-latest"},
    {"name": "gemini-3.5-flash",     "type": "gemini",  "model": "gemini-3.5-flash"},
    {"name": "gemini-3.1-flash-lite", "type": "gemini",  "model": "gemini-3.1-flash-lite"},
    {"name": "gemini-2.5-flash",     "type": "gemini",  "model": "gemini-2.5-flash"},
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
        "Professional interior photography of a warm French brasserie restaurant, amber lighting, elegant table settings, white tablecloths, wine glasses, bokeh, photorealistic 8k",
        "Close-up food photography of elegantly plated French gourmet main course, warm tones, professional restaurant lighting, shallow depth of field, 8k",
        "Cozy French restaurant dining room, intimate candlelight, wooden furniture, couples dining, photorealistic",
        "Beautiful French dessert presentation, chocolate fondant caramel sauce vanilla ice cream, professional food photography",
        "Fresh artisan bread basket and charcuterie platter in French bistro, rustic wooden table",
        "Wine cellar and sommelier at French restaurant, warm amber lighting, vintage atmosphere, photorealistic",
    ],
    "cafe": [
        "Cozy French café interior, wooden bar, vintage espresso machine, morning steam from coffee cup, photorealistic",
        "Perfect latte art coffee close-up in French café, warm tones, barista professional photography",
        "French boulangerie display with fresh croissants pain au chocolat brioche, morning golden light, artisan bakery",
        "Artisan sourdough bread on wooden shelves in a French bakery, warm rustic atmosphere",
    ],
    "medical": [
        "Modern clean medical consultation office, professional French clinic interior, white walls, reassuring atmosphere, 8k",
        "Friendly professional doctors team in modern French medical center, white coats, smiling, photorealistic",
        "Modern medical equipment in clean professional clinic, high-tech healthcare environment",
    ],
    "automotive": [
        "Professional automotive garage workshop, clean organized tools, mechanic working on car, industrial lighting, photorealistic",
        "Modern car service center, luxury vehicle on hydraulic lift, professional mechanics in uniform",
    ],
    "beauty": [
        "Modern French luxury beauty salon interior, elegant styling chairs, mirrors, professional warm lighting, white and gold decor, 8k",
        "Professional hair styling in luxury salon, elegant atmosphere, warm tones, photorealistic",
        "Spa beauty treatment room, relaxing atmosphere, candles, white towels, luxury skincare products",
        "Close-up of perfect hair coloring and styling result, shiny healthy hair, professional salon",
    ],
    "professional": [
        "Modern elegant French professional office interior, clean desk, law bookshelves, natural light, photorealistic",
        "Professional business consultation meeting in elegant French office, suits, confidence",
    ],
    "retail": [
        "Elegant French boutique interior, wooden shelves with carefully arranged products, warm lighting, photorealistic",
        "French local shop interior, colorful products display, welcoming atmosphere, professional photography",
    ],
    "generic": [
        "Modern French local business welcoming interior, professional organized space, warm lighting, photorealistic",
        "Professional small business storefront France, sunny day, welcoming entrance, quality establishment",
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
}


def _sanitize_json_strings(s: str) -> str:
    """Fix common LLM JSON issues: unescaped newlines/CR inside string values."""
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
        elif in_string and ch == '\n':
            result.append('\\n')
        elif in_string and ch == '\r':
            result.append('\\r')
        else:
            result.append(ch)
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
        prompts = SECTOR_FAL_PROMPTS.get(self.sector, SECTOR_FAL_PROMPTS["generic"])
        urls = []

        for i, prompt_text in enumerate(prompts[:needed]):
            try:
                self._push_log("Visions Artist",
                    f"🎨 Génération photo {i+1}/{min(needed, len(prompts))} avec Flux AI...", "chat")
                handler = fal_client.submit(
                    "fal-ai/flux/schnell",
                    arguments={
                        "prompt": prompt_text,
                        "image_size": "landscape_4_3",
                        "num_inference_steps": 4,
                        "enable_safety_checker": True,
                        "num_images": 1,
                    }
                )
                result = handler.get()
                if result.get("images"):
                    url = result["images"][0]["url"]
                    urls.append(url)
                    self._push_log("Visions Artist", f"✅ Photo {i+1} prête", "chat")
            except Exception as e:
                self._push_log("Visions Artist", f"⚠️ Photo {i+1} ignorée : {e}", "chat")

        return urls

    def _call(self, prompt: str, max_tokens: int = 2048, system: str = "") -> str:
        """Call with provider fallback chain: gemini-2.5 → gemini-2.0 → mistral."""
        last_error = None
        for provider in PROVIDERS_TEXT:
            try:
                result = self._call_provider(provider, prompt, max_tokens, system)
                return result
            except Exception as e:
                msg = str(e).lower()
                is_quota = any(k in msg for k in ['429', 'quota', 'resource_exhausted', 'rate_limit', 'retry_delay', 'limit exceeded', 'too many'])
                if is_quota:
                    self._push_log("Système", f"⏭️ {provider['name']} quota atteint → provider suivant...", "system")
                    last_error = e
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
            raw = self._call(prompt, max_tokens=1500)
            raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
            raw = re.sub(r'\s*```$', '', raw.strip())
            m = re.search(r'\{[\s\S]*\}', raw)
            json_str = m.group(0) if m else raw
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

## 4. 🏆 ANALYSE CONCURRENTIELLE
- 3 concurrents directs probables dans la zone (noms fictifs crédibles avec leurs forces)
- Avantages compétitifs exploitables pour {biz.get('name')}
- Parts de marché local estimées

## 5. 💡 RECOMMANDATIONS SERVICES
Solutions concrètes à proposer au propriétaire, par ordre de priorité :
1. Site vitrine professionnel → Pourquoi c'est urgent, ROI attendu
2. Référencement local SEO → Mots-clés cibles, visibilité estimée
3. Gestion avis Google → Impact sur le chiffre d'affaires
4. Présence réseaux sociaux → Quel réseau, quelle fréquence
5. [Autres selon le secteur]

## 6. 🎯 SCRIPT COMMERCIAL (pour le commercial)
Arguments clés pour convaincre le propriétaire :
- Accroche d'entrée (phrase d'ouverture percutante)
- 3 douleurs à mentionner (ce qu'il perd sans présence digitale)
- 3 bénéfices concrets à projeter (chiffres, exemples secteur)
- Réponses aux 3 objections classiques (prix, temps, "je n'en ai pas besoin")
- Proposition de valeur finale (closing)

## 7. 📈 PROJECTION ROI 12 MOIS
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

    def _generate_html_streaming(self, prep_data: dict) -> str:
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

        # ── Build photo list: Google Photos → fal.ai → Unsplash ──
        biz_photos = [p for p in (self.business_data.get("photos") or [])
                      if isinstance(p, str) and p.startswith("http")]
        fallbacks  = SECTOR_UNSPLASH.get(self.sector, SECTOR_UNSPLASH["generic"])

        # Generate with fal.ai if fewer than 3 real photos
        fal_photos = []
        if len(biz_photos) < 3 and os.environ.get("FAL_KEY"):
            needed    = max(0, 6 - len(biz_photos))
            self._push_log("Visions Artist",
                f"📸 Pas assez de photos Google ({len(biz_photos)}) — génération de {needed} images avec Flux AI...", "chat")
            fal_photos = self._generate_images_fal(needed)

        all_photos = (biz_photos + fal_photos + fallbacks * 3)[:10]

        # Proxy Google Places photo URLs through backend to avoid CORS / API-key referrer issues
        def _proxify(url: str) -> str:
            if "places.googleapis.com" in url or "maps.googleapis.com" in url:
                return f"/photo?url={urllib.parse.quote(url, safe='')}"
            return url

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
                is_quota = any(k in msg for k in ['429', 'quota', 'resource_exhausted', 'rate_limit', 'retry_delay', 'limit exceeded', 'too many'])
                if is_quota:
                    self._push_log("Système", f"⏭️ HTML: {provider['name']} quota → suivant...", "system")
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

        def _proxify(url: str) -> str:
            if "places.googleapis.com" in url or "maps.googleapis.com" in url:
                return f"/photo?url={urllib.parse.quote(url, safe='')}"
            return url

        all_photos = [_proxify(p) for p in (biz_photos + fal_photos + fallbacks * 3)[:10]]

        # ── Try template-based generation first ──
        html = ""
        if self.sector in self.SECTOR_TEMPLATE:
            content_slots = self._extract_content_slots(prep_data)
            html = self._render_from_template(content_slots, all_photos)

        # ── Fallback: full LLM generation ──
        if not html:
            html = self._generate_html_streaming(prep_data)

        self._push_log("Le Closer",
            f"📧 Rédaction de l'email de prospection...", "chat")

        biz        = self.business_data
        report     = prep_data.get("report", "")[:2000]
        copywrite  = prep_data.get("copywriting", "")[:1000]

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

        email_prompt = f"""Tu es Ludovic, fondateur de Pulse-PME. Tu as DÉJÀ créé un site web de démonstration personnalisé pour ce commerce — il est en ligne et disponible pendant 24h seulement.
Tu écris un email de prospection qui doit faire une seule chose : convaincre le gérant de cliquer sur son lien démo et de choisir son pack dans les 24h.

════ DONNÉES DU COMMERCE ════
Nom : {biz.get('name')}
Secteur : {self.sector_profile['label']}
Adresse : {biz.get('address', '')}
Présence Google : {rating_line}
Score présence digitale : {score:.1f}/10 (plus c'est bas = plus de potentiel à gagner)
{website_line}

Rapport d'analyse de leur situation (utilise CES insights concrets dans l'email) :
{report}

Copywriting de leur site démo (utilise le ton et les arguments pour personnaliser) :
{copywrite}

════ STRUCTURE EN 3 BLOCS OBLIGATOIRES ════

BLOC 1 — ACCROCHE + VISION DIGITALE (4-5 lignes)
{salut_line}
Phrase 2 : une observation ultra-spécifique sur CE commerce basée sur le rapport (leur note, leur secteur, leur rue, ce que leurs clients disent — quelque chose qu'on ne pourrait dire qu'à EUX).
Phrases 3-4 : explique que dans le monde d'aujourd'hui, un commerce sans présence digitale complète perd des clients chaque jour. Ce n'est pas qu'un site web — c'est une identité numérique complète : site professionnel + référencement Google (SEO) + publicités ciblées (Ads) + gestion des avis. Pulse-PME s'occupe de TOUT ça pour eux pendant qu'ils se concentrent sur leur vrai métier.

BLOC 2 — LA PREUVE PAR LEUR ANALYSE (4-5 lignes)
Phrase 1 : "J'ai analysé la présence en ligne de {biz.get('name')} et j'ai créé une démonstration concrète."
Utilise 2-3 données précises du rapport d'analyse (ex: leur score digital, ce qui manque, ce que leurs concurrents font qu'eux ne font pas). Montre que tu as fait le travail POUR EUX.
Termine par : leur site démo est en ligne maintenant — personnalisé pour leur secteur, avec leur nom, leurs services, prêt à lancer.

BLOC 3 — LES 3 PACKS + CTA 24H (6-8 lignes)
Présente les 3 offres de façon séduisante, avec l'avantage clé de chaque :

⚡ STARTER — 49€/mois (sans engagement)
Site pro + SEO de base + hébergement. Parfait pour démarrer et tester. Résiliable à tout moment.
→ [LIEN_STRIPE_STARTER]

🚀 PRO — 149€/mois
Site + SEO avancé + Google Ads géré + réservations en ligne + avis Google en direct. Le pack pour ceux qui veulent croître.
→ [LIEN_STRIPE_PRO]

👑 ELITE — 299€/mois
Tout le Pro + blog SEO automatique + chatbot WhatsApp IA + site multilingue. La solution clé en main complète.
→ [LIEN_STRIPE_ELITE]

Termine par : "Ton site démo est disponible 24h. Après, il sera supprimé. Choisis ton pack directement via les liens ci-dessus, ou réponds à cet email si tu as une question."

Signature :
Ludovic
Fondateur — Pulse-PME
📞

════ RÈGLES ABSOLUES ════
- Jamais "Je me permets", "Dans le cadre de", "Madame/Monsieur", "Cordialement"
- Les liens [LIEN_STRIPE_*] doivent apparaître EXACTEMENT tels quels (placeholders temporaires)
- Ton : direct, chaleureux, entrepreneur à entrepreneur
- Les données du rapport doivent apparaître dans le bloc 2 (chiffres précis, pas de généralités)
- Longueur totale : 25-30 lignes. L'email est complet, pas un résumé.
- Tout en français

Écris l'email complet, directement, sans objet ni balise HTML."""

        try:
            email_text = self._call(email_prompt, max_tokens=2000)
            # Strip any accidental markers
            email_text = re.sub(r'---\s*EMAIL CONTENT (START|END)\s*---', '', email_text).strip()
            self._push_log("Le Closer", "✅ Email de prospection personnalisé prêt.", "chat")
        except Exception as e:
            email_text = (f"Bonjour,\n\nJe viens de créer un site de démonstration spécialement pour "
                          f"{biz.get('name')}. Seriez-vous disponible 5 minutes pour le découvrir ?\n\n"
                          f"Cordialement,\nLudovic | Local-Pulse")
            self._push_log("Le Closer", f"⚠️ Email simplifié : {e}", "chat")

        return {"html": html, "email": email_text}

    # ──────────────────────────────────────────────────────────────
    #  PHASE 3 — DEPLOY
    # ──────────────────────────────────────────────────────────────

    def run_deploy_crew(self, html_content: str) -> str:
        from backend.agents.tools import VercelDeployTool
        tool = VercelDeployTool()
        return tool._run(html_content, self.business_id)
