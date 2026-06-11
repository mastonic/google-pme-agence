import anthropic
import urllib.parse
import re
import os
import json

CLAUDE_MODEL = "claude-sonnet-4-5"

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
        "label": "Café / Salon de thé / Boulangerie",
        "hint": "cozy-artisan : tons beige, moka, crème, chaleureux et artisanal",
        "sections": ["hero", "menu", "ambiance_gallery", "about", "testimonials", "hours_map", "contact"],
        "special_instructions": """- Section CARTE : boissons chaudes, froides, snacks, pâtisseries avec prix.
- Section AMBIANCE avec 3 photos en mosaïque.""",
        "cta_primary": "Commander en ligne",
        "cta_secondary": "Voir notre carte",
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

SECTOR_TYPE_MAP = {
    "restaurant": "restaurant", "food": "restaurant", "meal_delivery": "restaurant",
    "meal_takeaway": "restaurant", "bakery": "restaurant",
    "cafe": "cafe", "bar": "cafe",
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
}


class LocalPulseManager:
    def __init__(self, business_data: dict, log_queue=None):
        self.business_data = business_data
        self.log_queue     = log_queue
        self.log_buffer    = None   # attached by orchestration task for polling
        self.business_id   = business_data.get("business_id")
        self.client        = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

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

    def _call(self, prompt: str, max_tokens: int = 2048, system: str = "") -> str:
        """Simple blocking Anthropic API call."""
        messages = [{"role": "user", "content": prompt}]
        kwargs = {"model": CLAUDE_MODEL, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        resp = self.client.messages.create(**kwargs)
        return resp.content[0].text

    # ──────────────────────────────────────────────────────────────
    #  PHASE 0 — DESIGN BRIEF
    # ──────────────────────────────────────────────────────────────

    def run_design_crew(self) -> dict:
        """Phase 0 : direct Anthropic call for design brief."""
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
            m = re.search(r'\{[\s\S]*\}', raw)
            self.design_brief = json.loads(m.group(0)) if m else {}
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
        """Phase 1 : direct Anthropic calls for investigation + copywriting."""
        biz     = self.business_data
        profile = self.sector_profile
        design_summary = f"Concept : {self.design_brief.get('template')} | Mood : {self.design_brief.get('mood')}" \
                         if self.design_brief else ""

        # ── Investigation ──
        self._push_log("L'Éclaireur",
            f"🔍 Investigation de **{biz.get('name')}** ({biz.get('address', '')})...", "chat")

        invest_prompt = f"""Tu es un expert en analyse de PME locales françaises.

Analyse ce commerce et fournis un rapport structuré :
- Nom : {biz.get('name')}
- Adresse : {biz.get('address', '')}
- Note Google : {biz.get('rating', 'N/A')}/5 ({biz.get('user_ratings_total', 0)} avis)
- Secteur : {profile['label']}
- Téléphone : {biz.get('phone', 'non communiqué')}

Identifie :
1. Le Digital Gap (absence de site, site non-mobile, etc.)
2. 3 points faibles visibles en ligne
3. Le concurrent principal estimé
4. Les 3 arguments de vente à mettre en avant
5. Une accroche slogan percutante (max 10 mots)

Réponse structurée en texte clair, format rapport professionnel."""

        try:
            report = self._call(invest_prompt, max_tokens=1500)
            self._push_log("L'Éclaireur", "✅ Rapport d'investigation terminé.", "chat")
        except Exception as e:
            report = f"Analyse de {biz.get('name')} — Commerce local secteur {profile['label']}."
            self._push_log("L'Éclaireur", f"⚠️ Analyse simplifiée : {e}", "chat")

        # ── Copywriting ──
        self._push_log("Le Stratège",
            f"✍️ Rédaction du copywriting pour **{biz.get('name')}**...", "chat")

        copy_prompt = f"""Tu es un copywriter expert en PME françaises.

Sur la base de cette analyse :
{report[:1500]}

Commerce : {biz.get('name')} | Secteur : {profile['label']}
{f"Brief design : {design_summary}" if design_summary else ""}

Rédige :
1. Un slogan accrocheur (court, mémorable, français)
2. Description "À propos" en 2 paragraphes (histoire, valeurs, ancrage local)
3. 4 services/produits phares avec descriptions et prix estimés
4. 3 arguments différenciants vs la concurrence
5. Preuve sociale : 3 témoignages clients fictifs mais crédibles
{profile['special_instructions']}

Format : texte structuré avec titres clairs."""

        try:
            copywriting = self._call(copy_prompt, max_tokens=2000)
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

        photo_urls  = re.findall(r'https?://\S+', prep_data.get("ai_photos", ""))
        hero_photo  = photo_urls[0].rstrip(")],") if photo_urls else \
                      "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1600&auto=format&fit=crop"

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

════ EXIGENCES TECHNIQUES ════
HEAD :
- <script src="https://cdn.tailwindcss.com"></script>
- Google Fonts pour {fonts.get('heading', 'Playfair Display')} et {fonts.get('body', 'Inter')}
- AOS : CDN + AOS.init({{duration:800, once:true}})
- CSS :root avec variables :
  :root {{ {css_vars_block or f'--color-primary: {colors.get("primary","#0071E3")};'} }}

NAV : fixe, glassmorphism, logo + liens smooth-scroll + bouton CTA "{cta_primary}"
HERO : min-h-screen, image {hero_photo}, overlay, H1 percutant, 2 boutons CTA, badge ⭐{rating}/5
SECTIONS : générer CHAQUE section dans l'ordre {' → '.join(sections_order)}
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

        with self.client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=8192,
            system="Tu génères uniquement du HTML valide. Commence par <!DOCTYPE html>. Aucun markdown.",
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                html_chunks.append(text)
                token_batch.append(text)
                token_count += 1
                if token_count % 8 == 0:
                    self._push_log("L'Ingénieur", "".join(token_batch), "stream_token")
                    token_batch = []

        if token_batch:
            self._push_log("L'Ingénieur", "".join(token_batch), "stream_token")

        full_html = "".join(html_chunks)

        if full_html.strip().startswith("```"):
            lines = full_html.strip().split("\n")
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].strip() == "```": lines = lines[:-1]
            full_html = "\n".join(lines)

        self._push_log("L'Ingénieur",
            f"✅ Site généré ! {len(full_html):,} caractères.", "chat")
        return full_html

    # ──────────────────────────────────────────────────────────────
    #  PHASE 2 — BUILD (HTML + email)
    # ──────────────────────────────────────────────────────────────

    def run_build_crew(self, prep_data: dict) -> dict:
        html = self._generate_html_streaming(prep_data)

        self._push_log("Le Closer",
            f"📧 Rédaction de l'email de prospection...", "chat")

        biz = self.business_data
        email_prompt = f"""Rédige un email de prospection court (max 120 mots) pour {biz.get('name')}.
Note Google : {biz.get('rating', 'N/A')}/5. Secteur : {self.sector_profile['label']}.
Mentionne que leur site de démonstration est prêt. Ton humain et bienveillant.
Propose un appel téléphonique.

Format exact :
--- EMAIL CONTENT START ---
(texte de l'email)
--- EMAIL CONTENT END ---"""

        try:
            email_text = self._call(email_prompt, max_tokens=400)
            self._push_log("Le Closer", "✅ Email de prospection prêt.", "chat")
        except Exception as e:
            email_text = f"Bonjour,\n\nVotre site de démonstration est prêt.\n\nCordialement"
            self._push_log("Le Closer", f"⚠️ Email simplifié : {e}", "chat")

        return {"html": html, "email": email_text}

    # ──────────────────────────────────────────────────────────────
    #  PHASE 3 — DEPLOY
    # ──────────────────────────────────────────────────────────────

    def run_deploy_crew(self, html_content: str) -> str:
        from backend.agents.tools import VercelDeployTool
        tool = VercelDeployTool()
        return tool._run(html_content, self.business_id)
