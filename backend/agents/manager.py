from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic
from backend.agents.tools import VercelDeployTool, FalFluxTool, GmailDraftTool
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
        "special_instructions": """
- Section MENU obligatoire : 4 onglets (Entrées / Plats / Desserts / Boissons) avec prix.
  Chaque plat = nom, description 1 ligne, prix en €. Style cartes élégantes.
- Bouton de RÉSERVATION proéminent en CTA secondaire dans le hero.
- Section GALERIE avec grille 3 colonnes : photos des plats + ambiance salle.
- Section À PROPOS : histoire du chef ou du restaurant, valeurs artisanales.""",
        "cta_primary": "Réserver une table",
        "cta_secondary": "Voir la carte",
    },
    "cafe": {
        "label": "Café / Salon de thé / Boulangerie",
        "hint": "cozy-artisan : tons beige, moka, crème, chaleureux et artisanal, illustrations hand-drawn",
        "sections": ["hero", "menu", "ambiance_gallery", "about", "testimonials", "hours_map", "contact"],
        "special_instructions": """
- Section CARTE : boissons chaudes, boissons froides, snacks, brunchs/pâtisseries avec prix.
- Section AMBIANCE avec 3 photos en mosaïque : cozy, convivial, artisanal.
- Typographie ronde et chaleureuse. Fond clair (beige/crème).""",
        "cta_primary": "Commander en ligne",
        "cta_secondary": "Voir notre carte",
    },
    "medical": {
        "label": "Médecin / Dentiste / Pharmacie",
        "hint": "clean-medical : blanc pur, vert menthe ou bleu ciel, typo sans-serif, rassurant et accessible",
        "sections": ["hero", "services", "team", "certifications", "testimonials", "appointment", "hours_map"],
        "special_instructions": """
- Section SPÉCIALITÉS / SERVICES : cartes avec icône médicale, nom de la spécialité, description courte.
- Section ÉQUIPE : photo, nom, titre/spécialité de chaque praticien.
- Section CERTIFICATIONS : logos/badges d'agréments et diplômes.
- Formulaire PRISE DE RENDEZ-VOUS en ligne (Nom, Tel, Date souhaitée, Motif).
- Fond blanc/très clair, accents couleur apaisante.""",
        "cta_primary": "Prendre rendez-vous",
        "cta_secondary": "Nos spécialités",
    },
    "automotive": {
        "label": "Garage / Carrosserie / Concessionnaire",
        "hint": "industrial-bold : gris acier, orange électrique ou rouge, robustesse, expertise technique",
        "sections": ["hero", "services", "certifications", "gallery", "testimonials", "estimate_form", "hours_map"],
        "special_instructions": """
- Section PRESTATIONS : liste des services avec icône, description et fourchette de prix (ex. Révision 99€, Pneus dès 49€/unité).
- Section AGRÉMENTS & MARQUES : badges fabricants (Renault, Peugeot, etc.) si mentionnés dans le rapport.
- Formulaire DEVIS EN LIGNE : véhicule (marque, modèle, année), prestation souhaitée, coordonnées.
- Section GALERIE : photos de l'atelier, véhicules en cours, équipements.""",
        "cta_primary": "Demander un devis",
        "cta_secondary": "Nos prestations",
    },
    "beauty": {
        "label": "Salon de beauté / Coiffeur / Spa",
        "hint": "modern-beauty : rose nude, beige doré, blanc cassé, élégance féminine et premium",
        "sections": ["hero", "services_menu", "gallery", "team", "testimonials", "booking", "hours_map"],
        "special_instructions": """
- Section SOINS & PRESTATIONS : tableau avec nom, durée et prix pour chaque soin.
- Section GALERIE : grid 2x3 avec photos avant/après ou réalisations.
- Section ÉQUIPE : photo ronde, prénom, spécialité de chaque praticienne.
- Bouton RÉSERVATION EN LIGNE très visible (lien Planity / calendrier).
- Typographie fine et élégante. Fond très clair ou nude.""",
        "cta_primary": "Réserver ma séance",
        "cta_secondary": "Nos soins",
    },
    "professional": {
        "label": "Avocat / Expert-comptable / Agence",
        "hint": "executive-trust : marine foncé, blanc, touches dorées, sérieux, confiance, expertise",
        "sections": ["hero", "expertise", "team", "process", "testimonials", "contact", "hours_map"],
        "special_instructions": """
- Section DOMAINES D'EXPERTISE : cartes avec icône, titre du domaine, description 2 lignes.
- Section ÉQUIPE : portrait pro, nom, titre, bar de compétences ou spécialités.
- Section PROCESSUS : étapes numérotées (1. Consultation → 2. Analyse → 3. Solution → 4. Suivi).
- Formulaire de contact avec champ "Nature de votre demande".""",
        "cta_primary": "Consultation gratuite",
        "cta_secondary": "Notre expertise",
    },
    "retail": {
        "label": "Commerce / Boutique / Fleuriste",
        "hint": "vibrant-local : couleurs vives et chaleureuses, accessible, convivial, local",
        "sections": ["hero", "featured_products", "promotions", "about", "testimonials", "hours_map", "contact"],
        "special_instructions": """
- Section PRODUITS PHARES : 6 cartes produits avec photo, nom et prix.
- Section PROMOTIONS / À LA UNE : bandeau accrocheur avec offre du moment.
- Section NOTRE HISTOIRE : ancrage local fort, valeurs du commerce de proximité.""",
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
        self.log_queue = log_queue
        self.business_id = business_data.get("business_id")

        import asyncio
        try:
            self.loop = asyncio.get_running_loop()
        except Exception:
            self.loop = None

        import redis
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
        except Exception:
            self.redis_client = None

        self.llm = ChatAnthropic(model=CLAUDE_MODEL, temperature=0.7)
        self.anthropic_client = anthropic.Anthropic()

        self.vercel_tool = VercelDeployTool()
        self.fal_tool = FalFluxTool()
        self.gmail_tool = GmailDraftTool()

        # Detect sector and attach profile to business data
        self.sector = self._detect_sector(business_data.get("types", []))
        self.sector_profile = SECTOR_PROFILES[self.sector]
        self.business_data["sector"] = self.sector
        self.business_data["sector_label"] = self.sector_profile["label"]
        self.business_data["design_hint"] = self.sector_profile["hint"]
        self.design_brief = None  # will be populated by run_design_crew()

    def _detect_sector(self, types: list) -> str:
        for t in types:
            if t in SECTOR_TYPE_MAP:
                return SECTOR_TYPE_MAP[t]
        return "generic"

    def _push_log(self, agent: str, message: str, msg_type: str = "chat"):
        entry = {"agent": agent, "message": message, "type": msg_type}
        if self.log_queue and self.loop:
            self.loop.call_soon_threadsafe(self.log_queue.put_nowait, entry)
        if self.redis_client and self.business_id:
            self.redis_client.rpush(f"logs:{self.business_id}", json.dumps(entry))
            self.redis_client.expire(f"logs:{self.business_id}", 3600)

    def _create_callback(self, agent_name: str):
        def callback(step):
            msg = ""
            try:
                if isinstance(step, list):
                    for s in step:
                        msg = getattr(s, 'thought', '') or getattr(s, 'text', str(s))
                else:
                    msg = getattr(step, 'thought', '') or getattr(step, 'text', str(step))
                if not msg or "failed to parse" in msg.lower():
                    return
                self._push_log(agent_name, msg, "chat")
                if self.redis_client and self.business_id:
                    self.redis_client.set(f"status:{self.business_id}", f"Agent {agent_name} en action...")
            except Exception as e:
                print(f"Callback error ({agent_name}): {e}")
        return callback

    # ──────────────────────────────────────────────────────────────
    #  PHASE 0 — DESIGN BRIEF (runs FIRST, independently)
    # ──────────────────────────────────────────────────────────────

    def run_design_crew(self) -> dict:
        """
        Phase 0 — runs BEFORE investigation.
        The designer analyzes the sector and produces a rich design brief
        that will guide ALL subsequent generation steps.
        """
        biz = self.business_data
        profile = self.sector_profile

        self._push_log("Le Designer", f"🎨 Analyse du secteur **{profile['label']}** pour **{biz.get('name')}**...", "chat")

        if self.redis_client and self.business_id:
            self.redis_client.set(f"status:{self.business_id}", "🎨 Création de l'identité visuelle...")

        designer_agent = Agent(
            role="Le Designer Visionnaire (Brand & UI/UX Director)",
            goal=f"Créer une identité visuelle unique et un brief design JSON pour un {profile['label']}.",
            backstory=f"""Tu es un Lead Designer d'élite (ex-Apple, Nike, BETC).
Tu te spécialises dans les sites web de PME françaises à fort impact visuel.

Secteur détecté : {profile['label']}
Suggestion de style de base : {profile['hint']}

Ta mission : produire un brief design JSON complet et unique qui sera la BIBLE du site.
Tu t'inspires des meilleurs sites du secteur (Michelin, Beauté Prestige, cliniques modernes...).
Tu adaptes chaque choix au commerce spécifique : nom, localisation, ambiance perçue dans les avis clients.""",
            verbose=True, llm=self.llm, allow_delegation=False, max_iter=3,
            step_callback=self._create_callback("Le Designer")
        )

        sections_list = " > ".join(profile["sections"])

        design_task = Task(
            description=f"""Crée le brief design complet pour **{biz.get('name')}** ({biz.get('address', '')}).
Secteur : {profile['label']}
Note Google : {biz.get('rating', 'N/A')}/5
Types d'activité : {', '.join(biz.get('types', []))}
Sections du site : {sections_list}

Produis UNIQUEMENT un objet JSON valide (pas de texte avant ni après) :
{{
  "template": "nom-du-concept-design",
  "sector": "{self.sector}",
  "colors": {{
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "surface": "#hex",
    "text": "#hex",
    "text_muted": "#hex",
    "border": "#hex"
  }},
  "fonts": {{
    "heading": "Nom Google Font",
    "body": "Nom Google Font",
    "accent": "Nom Google Font optionnel ou null"
  }},
  "hero": {{
    "style": "fullscreen-dark|fullscreen-light|split-screen|video-overlay",
    "overlay_opacity": 0.6,
    "text_align": "center|left"
  }},
  "nav": {{
    "style": "transparent-to-solid|always-solid|minimal",
    "cta_text": "{profile['cta_primary']}"
  }},
  "cards": {{
    "style": "glass|solid|bordered|shadow-only",
    "border_radius": "rounded-xl|rounded-2xl|rounded-none"
  }},
  "buttons": {{
    "primary_style": "filled|outline|gradient",
    "border_radius": "rounded-full|rounded-xl|rounded-none"
  }},
  "mood": "3-5 adjectifs décrivant l'ambiance visuelle",
  "unique_angle": "Proposition de valeur unique et accrocheur pour ce commerce spécifique",
  "sections_order": {json.dumps(profile['sections'])},
  "animations": "elegant|energetic|minimal|playful",
  "css_variables": {{
    "--color-primary": "#hex",
    "--color-secondary": "#hex",
    "--color-accent": "#hex",
    "--color-bg": "#hex",
    "--color-surface": "#hex",
    "--color-text": "#hex",
    "--color-text-muted": "#hex",
    "--font-heading": "'Nom Font', serif",
    "--font-body": "'Nom Font', sans-serif",
    "--radius-card": "1rem",
    "--radius-btn": "9999px"
  }}
}}""",
            expected_output="JSON de brief design complet et valide.",
            agent=designer_agent
        )

        crew = Crew(
            agents=[designer_agent],
            tasks=[design_task],
            process=Process.sequential,
            verbose=True,
        )
        crew.kickoff(inputs=biz)

        raw = design_task.output.raw if design_task.output else "{}"

        # Parse the JSON from the designer output
        design_brief = {}
        try:
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                design_brief = json.loads(json_match.group(0))
        except Exception:
            design_brief = {"template": "universal-modern", "mood": "moderne", "sector": self.sector}

        self.design_brief = design_brief
        self._push_log("Le Designer",
            f"✅ Brief design créé ! Concept : **{design_brief.get('template', 'moderne')}** — {design_brief.get('mood', '')}",
            "chat")

        return design_brief

    # ──────────────────────────────────────────────────────────────
    #  HTML GENERATION — Claude API streaming
    # ──────────────────────────────────────────────────────────────

    def _generate_html_streaming(self, prep_data: dict) -> str:
        """Generate a complete, sector-specific themed website using Claude streaming."""
        biz = self.business_data
        profile = self.sector_profile
        design = self.design_brief or {}

        name = biz.get("name", "Mon Commerce")
        address = biz.get("address", "")
        phone = biz.get("phone", "")
        rating = biz.get("rating", 0)

        whatsapp = re.sub(r'[\s\-\.]', '', phone)
        if whatsapp.startswith("0"):
            whatsapp = "+33" + whatsapp[1:]

        encoded_address = urllib.parse.quote(address)

        report = prep_data.get("report", "")[:4000]
        copywriting = prep_data.get("copywriting", "")[:2500]
        ai_photos = prep_data.get("ai_photos", "")[:600]

        photos_str = ai_photos
        if biz.get("photos"):
            photos_str += "\n" + "\n".join(str(p) for p in biz["photos"][:4])

        photo_urls = re.findall(r'https?://\S+', photos_str)
        hero_photo = photo_urls[0].rstrip(")],") if photo_urls else "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1600&auto=format&fit=crop"

        # Extract design values with fallbacks
        colors = design.get("colors", {})
        fonts = design.get("fonts", {})
        css_vars = design.get("css_variables", {})
        hero_cfg = design.get("hero", {})
        cta_primary = profile.get("cta_primary", "Nous contacter")
        cta_secondary = profile.get("cta_secondary", "En savoir plus")
        mood = design.get("mood", "moderne et professionnel")
        unique_angle = design.get("unique_angle", "")
        template_name = design.get("template", "universal-modern")
        card_style = design.get("cards", {}).get("style", "shadow-only")
        btn_radius = design.get("buttons", {}).get("border_radius", "rounded-xl")
        animations = design.get("animations", "smooth")

        # Build CSS variables block
        css_vars_block = "\n".join(f"        {k}: {v};" for k, v in css_vars.items())

        sections_order = design.get("sections_order", profile["sections"])
        sections_guide = profile["special_instructions"]

        prompt = f"""Tu es un développeur web senior expert HTML/CSS/Tailwind. Génère le site web complet et professionnel pour cette PME française.

════════════════════════════════════════
BRIEF DESIGN — CONCEPT "{template_name.upper()}"
════════════════════════════════════════
Secteur : {profile['label']}
Ambiance : {mood}
Angle unique : {unique_angle}

Palette de couleurs :
- Primary   : {colors.get('primary', '#0071E3')}
- Secondary : {colors.get('secondary', '#1A1A2E')}
- Accent    : {colors.get('accent', '#FF6B35')}
- Background: {colors.get('background', '#FFFFFF')}
- Surface   : {colors.get('surface', '#F8F9FA')}
- Text      : {colors.get('text', '#1A1A1A')}

Typographies :
- Titres : {fonts.get('heading', 'Playfair Display')}
- Corps  : {fonts.get('body', 'Inter')}
{f"- Accent : {fonts.get('accent')}" if fonts.get('accent') else ""}

Hero style : {hero_cfg.get('style', 'fullscreen-dark-overlay')}
Cards : {card_style} — Boutons : {btn_radius}
Animations : {animations}

════════════════════════════════════════
DONNÉES DU COMMERCE
════════════════════════════════════════
- Nom : {name}
- Adresse : {address}
- Téléphone : {phone}
- Note Google : {rating}/5
- Photo hero : {hero_photo}

════════════════════════════════════════
RAPPORT D'ANALYSE (avis, concurrents, digital gap)
════════════════════════════════════════
{report}

════════════════════════════════════════
COPYWRITING PRÉPARÉ
════════════════════════════════════════
{copywriting}

════════════════════════════════════════
ORDRE DES SECTIONS : {' → '.join(sections_order)}
════════════════════════════════════════
{sections_guide}

════════════════════════════════════════
EXIGENCES TECHNIQUES STRICTES
════════════════════════════════════════

### HEAD
- Tailwind CSS CDN : <script src="https://cdn.tailwindcss.com"></script>
- Google Fonts pour {fonts.get('heading', 'Playfair Display')} et {fonts.get('body', 'Inter')}
- AOS animations : CDN link + css + `AOS.init({{duration:800, once:true}})`
- CSS custom properties OBLIGATOIRES dans <style> :
  :root {{
{css_vars_block if css_vars_block else "    --color-primary: " + colors.get('primary', '#0071E3') + ";"}
  }}

### NAV
- Fixe en haut, glassmorphism (backdrop-blur-md bg-white/10 border-b border-white/10)
- Logo : initiales en cercle coloré + nom complet
- Liens smooth-scroll vers les sections
- Bouton CTA "{cta_primary}" coloré (bg-[{colors.get('primary', '#0071E3')}])
- Menu hamburger mobile fonctionnel (toggle JS)

### HERO (min-h-screen)
- Image de fond : {hero_photo}
- Overlay : opacity-{int(hero_cfg.get('overlay_opacity', 0.6)*10)*10}
- H1 grand et percutant (le slogan du copywriting)
- Sous-titre accrocheur
- 2 boutons : "{cta_primary}" (primary) + "{cta_secondary}" (outline)
- Badge note Google si rating > 4 : "⭐ {rating}/5"

### SECTIONS DU SITE
Génère CHAQUE section dans l'ordre : {' → '.join(sections_order)}
Utilise les données du rapport et du copywriting pour chaque section.
La carte Google Maps est OBLIGATOIRE dans la section hours_map :
<iframe src="https://maps.google.com/maps?q={encoded_address}&output=embed" width="100%" height="300" style="border:0;border-radius:1rem;" loading="lazy"></iframe>

### BOUTON WHATSAPP FLOTTANT (fixe en bas à droite, z-index 9999)
<a href="https://wa.me/{whatsapp or '+33600000000'}"
   style="position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;background:#25D366;color:white;padding:0.8rem 1.4rem;border-radius:9999px;font-weight:700;text-decoration:none;box-shadow:0 8px 25px rgba(37,211,102,0.45);display:flex;align-items:center;gap:0.5rem;">
  💬 WhatsApp
</a>

### FOOTER
- Fond sombre (bg-[{colors.get('secondary', '#1A1A2E')}])
- Logo + slogan + adresse + téléphone + liens nav
- Copyright © {name} 2026

### QUALITÉ
- Mobile-first, responsive (Tailwind breakpoints sm: md: lg:)
- AOS attributes (data-aos="fade-up") sur chaque section
- Hover effects sur TOUS les boutons, cartes et liens
- Couleurs exclusivement depuis le brief design — COHÉRENCE TOTALE
- Tous les textes en français

COMMENCE DIRECTEMENT par <!DOCTYPE html> — aucun texte ni markdown avant."""

        self._push_log("L'Ingénieur",
            f"🏗️ Génération du site **{template_name}** pour **{name}** ({profile['label']})...", "chat")

        html_chunks = []
        token_batch = []
        token_count = 0

        with self.anthropic_client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=8192,
            system="Tu es un développeur web expert. Tu génères uniquement du HTML valide et complet. "
                   "Commence toujours par <!DOCTYPE html>. Aucun markdown, aucune explication.",
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

        # Strip accidental markdown fences
        if full_html.strip().startswith("```"):
            lines = full_html.strip().split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            full_html = "\n".join(lines)

        self._push_log("L'Ingénieur",
            f"✅ Site généré ! {len(full_html):,} caractères — concept **{template_name}**.", "chat")

        return full_html

    # ──────────────────────────────────────────────────────────────
    #  CREWAI AGENTS & TASKS
    # ──────────────────────────────────────────────────────────────

    def create_agents(self):
        profile = self.sector_profile
        design_summary = ""
        if self.design_brief:
            d = self.design_brief
            design_summary = f"Concept : {d.get('template')} | Mood : {d.get('mood')} | Angle : {d.get('unique_angle')}"

        self.eclaireur = Agent(
            role="L'Éclaireur (Lead Data Scraper)",
            goal="Extraire l'ADN complet d'un commerce et TOUTES les sources médias disponibles.",
            backstory=f"""Tu es un enquêteur numérique spécialisé dans l'analyse des PME locales françaises.
Ta mission : analyser ce {profile['label']} en profondeur.
Tu extrais : note Google, avis clients détaillés (min 5), photos, horaires, concurrent principal.
Tu identifies le Digital Gap (pas de site, site non mobile, absence réseaux sociaux).
{f"Brief design actif : {design_summary}" if design_summary else ""}
Réponse en JSON structuré.""",
            verbose=True, llm=self.llm, allow_delegation=False, max_iter=3,
            step_callback=self._create_callback("L'Éclaireur")
        )

        self.stratege = Agent(
            role="Le Stratège de Vente (Conversion Copywriter)",
            goal=f"Rédiger des textes web persuasifs pour un {profile['label']}, optimisés pour la conversion et le SEO local.",
            backstory=f"""Tu es un copywriter de haut niveau spécialisé dans les PME françaises.
Tu connais les codes culturels du secteur {profile['label']}.
{f"Tu t'alignes sur le concept design : {design_summary}" if design_summary else ""}
Tu crées : slogans percutants, descriptions de services, arguments de vente vs le concurrent, preuve sociale.""",
            verbose=True, llm=self.llm, allow_delegation=False, max_iter=3,
            step_callback=self._create_callback("Le Stratège")
        )

        self.visions_artist = Agent(
            role="Visions Artist (AI Photographer)",
            goal="Fournir ou générer des visuels premium adaptés au concept design.",
            backstory=f"""Tu es un photographe publicitaire d'élite.
Concept design actif : {design_summary or profile['hint']}
Si des photos réelles sont disponibles dans le rapport, tu les priorises.
Sinon, tu génères via Fal.ai des visuels hyper-réalistes cohérents avec le mood "{self.design_brief.get('mood', 'moderne') if self.design_brief else ''}".""",
            verbose=True, llm=self.llm, allow_delegation=False, tools=[self.fal_tool],
            max_iter=3, step_callback=self._create_callback("Visions Artist")
        )

        self.closer = Agent(
            role="Le Closer (Automated Outreach Specialist)",
            goal="Rédiger un email de prospection ultra-personnalisé et créer le brouillon Gmail.",
            backstory="""Tu es un expert en vente B2B locale. Tu rédiges des emails courts, percutants, humains.
Tu mentionnes toujours : la note Google, le fait qu'un site de démo est prêt, et tu proposes un rendez-vous téléphonique.
Tu utilises GmailDraftTool. Tu n'envoies jamais directement.""",
            verbose=True, llm=self.llm, allow_delegation=False, tools=[self.gmail_tool],
            max_iter=3, step_callback=self._create_callback("Le Closer")
        )

    def create_tasks(self):
        biz = self.business_data
        profile = self.sector_profile

        self.investigation_task = Task(
            description=f"""Scanner {{name}} à {{address}}.
CRITIQUE : Extraire toutes les sources médias (photos propriétaire + photos des avis).
Identifier le Digital Gap. Analyser le concurrent principal à moins de 500m.
Secteur analysé : {profile['label']}

Répondre en JSON :
{{{{
  "{{name}}": {{{{
    "nom": "{{name}}", "adresse": "{{address}}", "note": {{rating}},
    "telephone": "si trouvé",
    "horaires": {{{{"Lundi": "9h-18h", "...": "..."}}}},
    "avis": [{{{{"auteur": "...", "note": 5, "commentaire": "...", "date": "..."}}}}],
    "Digital_Gap": {{{{"Site_mobile": "Non/Oui", "Click_Collect": "Non/Oui"}}}},
    "photos_links": {{photos}}
  }}}},
  "Concurrent": {{{{"nom": "...", "note": 4.1, "point_faible": "..."}}}}
}}}}""",
            expected_output="Rapport JSON structuré complet avec avis détaillés et liens médias.",
            agent=self.eclaireur
        )

        sections_copy = " + ".join(profile["sections"])
        self.capture_task = Task(
            description=f"""Sur la base du rapport, rédiger le copywriting complet pour ce {profile['label']} :
1. Slogan accrocheur pour {{name}} (court, mémorable, français)
2. Description "À propos" de 3 paragraphes (histoire, valeurs, ancrage local)
3. Contenu spécifique au secteur pour les sections : {sections_copy}
4. 4 services/produits phares avec descriptions et prix estimés
5. 3 arguments de vente différenciants vs le concurrent
6. Paragraphe de preuve sociale basé sur les vrais avis clients
{profile['special_instructions']}""",
            expected_output="Copywriting complet et structuré pour toutes les sections du site.",
            agent=self.stratege
        )

        mood_text = self.design_brief.get('mood', profile['hint']) if self.design_brief else profile['hint']
        self.visual_creation_task = Task(
            description=f"""Analyser les photos disponibles dans le rapport de l'Éclaireur.
Mood du design : {mood_text}
Si photos réelles suffisantes : retourner les URLs directement.
Sinon, générer 2 visuels premium via Fal.ai, cohérents avec le concept "{self.design_brief.get('template', 'moderne') if self.design_brief else 'moderne'}" et adaptés à {{address}}.""",
            expected_output="URLs des images (réelles ou générées).",
            agent=self.visions_artist
        )

        self.offensive_task = Task(
            description=f"""Rédiger un email de prospection personnalisé pour {biz.get('name', 'ce commerce')}.
Note Google : {biz.get('rating', 'N/A')}/5.
Secteur : {profile['label']}
Mentionne que leur site de démonstration est prêt (concept : {self.design_brief.get('template', 'moderne') if self.design_brief else 'moderne'}).
Email court (max 150 mots), ton humain et bienveillant.
Crée le brouillon via GmailDraftTool.

Format :
--- EMAIL CONTENT START ---
(Texte de l'email)
--- EMAIL CONTENT END ---""",
            expected_output="Texte de l'email + confirmation brouillon Gmail.",
            agent=self.closer
        )

    # ──────────────────────────────────────────────────────────────
    #  CREW RUNS
    # ──────────────────────────────────────────────────────────────

    def run_prep_crew(self) -> dict:
        """Phase 1 : Investigation + Copywriting + Photos (après Design)."""
        self.create_agents()
        self.create_tasks()

        crew = Crew(
            agents=[self.eclaireur, self.stratege, self.visions_artist],
            tasks=[self.investigation_task, self.capture_task, self.visual_creation_task],
            process=Process.sequential,
            verbose=True,
            step_callback=self._create_callback("Crew Prep")
        )

        if self.redis_client and self.business_id:
            self.redis_client.set(f"status:{self.business_id}", "🔍 Investigation & copywriting en cours...")

        crew.kickoff(inputs=self.business_data)

        return {
            "report": self.investigation_task.output.raw if self.investigation_task.output else "",
            "copywriting": self.capture_task.output.raw if self.capture_task.output else "",
            "ai_photos": self.visual_creation_task.output.raw if self.visual_creation_task.output else "",
            "design": json.dumps(self.design_brief) if self.design_brief else "",
        }

    def run_build_crew(self, prep_data: dict) -> dict:
        """Phase 2 : HTML generation (streaming) + email draft."""
        if self.redis_client and self.business_id:
            self.redis_client.set(f"status:{self.business_id}", "🏗️ Génération HTML avec Claude...")

        html = self._generate_html_streaming(prep_data)

        # Email via Closer
        self.create_agents()
        self.create_tasks()
        email_crew = Crew(
            agents=[self.closer],
            tasks=[self.offensive_task],
            process=Process.sequential,
            verbose=True,
        )
        email_crew.kickoff(inputs={**self.business_data, **prep_data})

        email_text = self.offensive_task.output.raw if self.offensive_task.output else ""

        return {"html": html, "email": email_text}

    def run_deploy_crew(self, html_content: str) -> str:
        """Phase 3 : Deploy pre-generated HTML to Vercel."""
        if self.redis_client and self.business_id:
            self.redis_client.set(f"status:{self.business_id}", "🚀 Déploiement Vercel...")
        return self.vercel_tool._run(html_content, self.business_id)
