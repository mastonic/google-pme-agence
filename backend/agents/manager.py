from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic
from backend.agents.tools import VercelDeployTool, FalFluxTool, GmailDraftTool
import anthropic
import urllib.parse
import re
import os

CLAUDE_MODEL = "claude-sonnet-4-5"


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

        self.business_data["suggested_template"] = self._get_design_hint(
            business_data.get("types", [])
        )

    def _get_design_hint(self, types: list) -> str:
        hints = {
            "restaurant": "luxury-dining (ambiance chaleureuse, tons ambrés/noir, typographies serif élégantes)",
            "food": "luxury-dining (ambiance chaleureuse, tons ambrés/noir, typographies serif élégantes)",
            "cafe": "cozy-cafe (tons beiges, moka, chaleureux, illustrations artisanales)",
            "pharmacy": "clean-medical (blanc, vert menthe, bleu, typo sans-serif, rassurant)",
            "doctor": "clean-medical (blanc, vert menthe, bleu, typo sans-serif, rassurant)",
            "health": "clean-medical (blanc, vert menthe, bleu, typo sans-serif, rassurant)",
            "car_repair": "industrial-bold (gris acier, orange, robustesse, expertise technique)",
            "car_dealer": "industrial-bold (gris acier, orange, robustesse, expertise technique)",
            "beauty_salon": "modern-beauty (rose nude, beige, doré, élégance féminine)",
            "spa": "modern-beauty (rose nude, beige, doré, élégance féminine)",
        }
        for t in types:
            if t in hints:
                return hints[t]
        return "universal-modern (bleu, blanc, sobre et professionnel)"

    def _push_log(self, agent: str, message: str, msg_type: str = "chat"):
        entry = {"agent": agent, "message": message, "type": msg_type}
        if self.log_queue and self.loop:
            self.loop.call_soon_threadsafe(self.log_queue.put_nowait, entry)
        if self.redis_client and self.business_id:
            import json
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
    #  HTML GENERATION — Claude API streaming
    # ──────────────────────────────────────────────────────────────

    def _generate_html_streaming(self, prep_data: dict) -> str:
        """Generate a complete website HTML using Claude with real token streaming."""
        biz = self.business_data
        name = biz.get("name", "Mon Commerce")
        address = biz.get("address", "")
        rating = biz.get("rating", 0)
        types = ", ".join(biz.get("types", []))
        phone = biz.get("phone", "")

        # Format phone for WhatsApp (French: 06... → +336...)
        whatsapp = re.sub(r'[\s\-\.]', '', phone)
        if whatsapp.startswith("0"):
            whatsapp = "+33" + whatsapp[1:]

        # URL-encode address for Google Maps embed
        encoded_address = urllib.parse.quote(address)

        # Extract first usable photo URL
        report = prep_data.get("report", "")[:4000]
        design = prep_data.get("design", "")[:1500]
        copywriting = prep_data.get("copywriting", "")[:2500]
        ai_photos = prep_data.get("ai_photos", "")[:600]

        photos_str = ai_photos
        if biz.get("photos"):
            photos_str += "\n" + "\n".join(str(p) for p in biz["photos"][:4])

        photo_urls = re.findall(r'https?://\S+', photos_str)
        hero_photo = photo_urls[0].rstrip(")],") if photo_urls else "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1600&auto=format&fit=crop"

        prompt = f"""Tu es un développeur web senior expert en HTML/CSS/Tailwind. Génère un site web professionnel complet pour cette PME française.

## DONNÉES DU COMMERCE
- Nom : {name}
- Adresse : {address}
- Téléphone : {phone}
- Note Google : {rating}/5
- Secteur : {types}

## RAPPORT D'INVESTIGATION (avis clients, concurrent, digital gap)
{report}

## DIRECTIVES DESIGN DU DESIGNER
{design}

## COPYWRITING
{copywriting}

## PHOTOS DISPONIBLES
Photo hero : {hero_photo}
Autres : {photos_str[:300]}

## EXIGENCES STRICTES

### Format
- Commence DIRECTEMENT par `<!DOCTYPE html>` — aucun texte avant, aucun markdown
- HTML complet, auto-suffisant, inline styles pour les éléments critiques
- Tailwind CSS via CDN : `<script src="https://cdn.tailwindcss.com"></script>`
- Google Fonts (2 familles cohérentes avec le secteur)
- AOS animations : CDN link + css + script init

### Sections OBLIGATOIRES dans l'ordre
1. **NAV** fixe, glassmorphism, logo (initiales + nom), liens smooth-scroll, bouton "Appeler" coloré
2. **HERO** fullscreen (min-h-screen), image de fond ({hero_photo}), overlay sombre (opacity-60), H1 percutant, sous-titre accrocheur, 2 boutons CTA (Réserver + WhatsApp)
3. **À PROPOS** (id="about") : histoire du commerce extraite du rapport, icônes emoji, 3 points forts
4. **NOS SERVICES** (id="services") : grid 3 colonnes, cartes avec icônes, titres, descriptions et prix si disponibles dans le rapport
5. **AVIS CLIENTS** (id="avis") : AU MOINS 3 vrais avis extraits du rapport (auteur, étoiles ★, commentaire, date), carousel ou grid
6. **HORAIRES & CARTE** (id="horaires") : tableau des horaires par jour + iframe Google Maps embed OBLIGATOIRE :
   `<iframe src="https://maps.google.com/maps?q={encoded_address}&output=embed" width="100%" height="300" style="border:0;border-radius:1rem;" loading="lazy"></iframe>`
7. **CONTACT** (id="contact") : formulaire (Nom, Email, Téléphone, Message) + side panel avec adresse/tel/horaires
8. **FOOTER** : logo, adresse, téléphone, liens nav, copyright {name} 2026

### Éléments FIXES OBLIGATOIRES
Bouton WhatsApp flottant :
```html
<a href="https://wa.me/{whatsapp or '+33600000000'}"
   style="position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;background:#25D366;color:white;padding:0.8rem 1.4rem;border-radius:9999px;font-weight:700;text-decoration:none;box-shadow:0 8px 25px rgba(37,211,102,0.45);display:flex;align-items:center;gap:0.5rem;font-size:0.9rem;transition:transform 0.2s;"
   onmouseover="this.style.transform='scale(1.08)'"
   onmouseout="this.style.transform='scale(1)'">
  💬 WhatsApp
</a>
```

### Qualité
- Mobile-first, responsive (Tailwind breakpoints)
- Animations AOS sur chaque section (fade-up, fade-left, zoom-in)
- Hover effects sur cartes, boutons, liens
- Palette cohérente avec le secteur ({design[:200] if design else 'moderne et professionnelle'})
- Tous textes en français
- Aucune image placeholder générique — utilise uniquement les photos du rapport

Génère le HTML maintenant. Commence par <!DOCTYPE html>"""

        # Notify start
        self._push_log("L'Ingénieur", f"🏗️ Génération du site pour **{name}** avec Claude {CLAUDE_MODEL}...", "chat")

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

                # Send batched tokens every 8 tokens for smooth streaming UX
                if token_count % 8 == 0:
                    batch_text = "".join(token_batch)
                    self._push_log("L'Ingénieur", batch_text, "stream_token")
                    token_batch = []

        # Flush remaining tokens
        if token_batch:
            self._push_log("L'Ingénieur", "".join(token_batch), "stream_token")

        full_html = "".join(html_chunks)

        # Strip any accidental markdown fences
        if full_html.strip().startswith("```"):
            lines = full_html.strip().split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            full_html = "\n".join(lines)

        self._push_log("L'Ingénieur",
            f"✅ HTML généré ! {len(full_html):,} caractères, {full_html.count('<section'):} sections.",
            "chat")

        return full_html

    # ──────────────────────────────────────────────────────────────
    #  CREWAI AGENTS & TASKS
    # ──────────────────────────────────────────────────────────────

    def create_agents(self):
        self.eclaireur = Agent(
            role="L'Éclaireur (Lead Data Scraper)",
            goal="Extraire l'ADN d'un commerce et TOUTES les sources de médias disponibles.",
            backstory="""Tu es un enquêteur numérique spécialisé dans l'analyse des PME locales françaises.
            Ta mission : analyser {name} à {address}.
            Tu extrais : note Google, avis clients détaillés (min 5), photos propriétaire + avis, horaires, concurrent principal.
            Tu identifies le Digital Gap (pas de site, site non mobile, absence de réseaux sociaux).
            Tu formated ta réponse en JSON structuré.""",
            verbose=True, llm=self.llm, allow_delegation=False, max_iter=3,
            step_callback=self._create_callback("L'Éclaireur")
        )

        self.stratege = Agent(
            role="Le Stratège de Vente (Conversion Copywriter)",
            goal="Rédiger des textes web persuasifs optimisés pour la conversion et le SEO local.",
            backstory="""Tu es un copywriter de haut niveau, spécialisé dans les PME françaises.
            Tu crées des slogans percutants, des descriptions de services convaincantes, et des arguments qui parlent au cœur du client local.
            Tu connais les codes culturels français et tu sais valoriser l'artisanat et le local.""",
            verbose=True, llm=self.llm, allow_delegation=False, max_iter=3,
            step_callback=self._create_callback("Le Stratège")
        )

        self.visions_artist = Agent(
            role="Visions Artist (AI Photographer)",
            goal="Générer des visuels premium si et seulement si aucune photo réelle n'est disponible.",
            backstory="""Tu es un photographe publicitaire d'élite.
            Si les photos réelles du propriétaire ou des avis sont disponibles dans le rapport, tu les utilises EN PRIORITÉ.
            Si aucune photo n'est disponible, tu génères via Fal.ai des visuels hyper-réalistes adaptés à la localisation et la démographie locale.
            Tu fournis uniquement les URLs des images.""",
            verbose=True, llm=self.llm, allow_delegation=False, tools=[self.fal_tool],
            max_iter=3, step_callback=self._create_callback("Visions Artist")
        )

        self.designer = Agent(
            role="Le Designer Visionnaire (UI/UX Director)",
            goal="Créer un plan design JSON unique adapté au secteur et à l'identité du commerce.",
            backstory=f"""Tu es un Lead Designer d'élite (ex-Apple, Nike). Tu crées des identités visuelles uniques pour les PME françaises.
            Suggestion de base : {self.business_data.get("suggested_template", "modern")}.

            Tu produis un JSON de directives design qui sera utilisé par l'Ingénieur pour générer le site :
            {{
              "template": "nom du concept design",
              "colors": {{
                "primary": "#hex",
                "secondary": "#hex",
                "accent": "#hex",
                "background": "#hex",
                "text": "#hex"
              }},
              "fonts": {{
                "heading": "Nom Google Font",
                "body": "Nom Google Font"
              }},
              "hero_style": "description du style hero",
              "mood": "adjectifs d'ambiance",
              "unique_angle": "proposition de valeur unique pour ce commerce"
            }}

            Adapte la palette au secteur : restaurant (ambre, noir), médical (blanc, vert), garage (acier, orange), beauté (nude, doré).""",
            verbose=True, llm=self.llm, allow_delegation=False, max_iter=3,
            step_callback=self._create_callback("Le Designer")
        )

        self.closer = Agent(
            role="Le Closer (Automated Outreach Specialist)",
            goal="Rédiger un email de prospection ultra-personnalisé et créer le brouillon Gmail.",
            backstory="""Tu es un expert en vente B2B locale. Tu rédiges des emails courts, percutants, humains.
            Tu mentionnes toujours : la note Google du commerce, le fait qu'un site de démo est prêt, et tu proposes un rendez-vous téléphonique.
            Tu utilises GmailDraftTool pour créer le brouillon. Tu n'envoies jamais directement.""",
            verbose=True, llm=self.llm, allow_delegation=False, tools=[self.gmail_tool],
            max_iter=3, step_callback=self._create_callback("Le Closer")
        )

    def create_tasks(self):
        self.investigation_task = Task(
            description="""Scanner {name} à {address}.
            CRITIQUE : Extraire toutes les sources médias (photos propriétaire + photos des avis).
            Identifier le Digital Gap. Analyser le concurrent principal à moins de 500m.

            Répondre en JSON :
            {{
              "{name}": {{
                "nom": "{name}", "adresse": "{address}", "note": {rating},
                "telephone": "si trouvé",
                "horaires": {{"Lundi": "9h-18h", ...}},
                "avis": [{{"auteur": "...", "note": 5, "commentaire": "...", "date": "..."}}],
                "Digital_Gap": {{"Site_mobile": "Non/Oui", "Click_Collect": "Non/Oui"}},
                "photos_links": {photos}
              }},
              "Concurrent": {{"nom": "...", "note": 4.1, "point_faible": "..."}}
            }}""",
            expected_output="Rapport JSON structuré complet avec avis détaillés et liens médias.",
            agent=self.eclaireur
        )

        self.capture_task = Task(
            description="""Sur la base du rapport de l'Éclaireur, rédiger :
            1. Un slogan accrocheur pour {name} (court, mémorable, en français)
            2. Une description "À propos" de 3 paragraphes qui raconte l'histoire du commerce
            3. 4 services/produits phares avec descriptions et prix estimés
            4. 3 arguments de vente différenciants vs le concurrent
            5. Un paragraphe de preuve sociale basé sur les avis clients""",
            expected_output="Copywriting complet pour le site web.",
            agent=self.stratege
        )

        self.visual_creation_task = Task(
            description="""Analyser les photos disponibles dans le rapport.
            Si photos réelles suffisantes : retourner les URLs directement.
            Sinon, générer 2 visuels premium via Fal.ai adaptés à {address} (respecter la démographie locale).""",
            expected_output="URLs des images (réelles ou générées).",
            agent=self.visions_artist
        )

        suggested = self.business_data.get("suggested_template", "universal-modern")
        self.artistic_task = Task(
            description=f"""Créer le plan design JSON pour {self.business_data.get("name", "ce commerce")}.
            Suggestion de base : {suggested}.
            Analyse le secteur d'activité, la localisation, l'ambiance du commerce dans les avis.
            Produis un JSON de directives design complet et unique (palette, typo, mood, angle unique).
            Ce JSON sera lu directement par le générateur HTML.""",
            expected_output="JSON de directives design complet et valide.",
            agent=self.designer
        )

        self.offensive_task = Task(
            description=f"""Rédiger un email de prospection personnalisé pour {self.business_data.get("name", "ce commerce")}.
            Note Google : {self.business_data.get("rating", "N/A")}/5.
            Mentionne que leur site de démonstration est prêt et que tu vas leur envoyer le lien.
            Email court (max 150 mots), ton humain et bienveillant, pas de jargon technique.
            Crée le brouillon via GmailDraftTool.

            Format de ta réponse finale :
            --- EMAIL CONTENT START ---
            (Texte de l'email ici)
            --- EMAIL CONTENT END ---""",
            expected_output="Texte de l'email personnalisé + confirmation du brouillon Gmail.",
            agent=self.closer
        )

    # ──────────────────────────────────────────────────────────────
    #  CREW RUNS
    # ──────────────────────────────────────────────────────────────

    def run_prep_crew(self) -> dict:
        """Phase 1 : Investigation + Copywriting + Photos + Design."""
        self.create_agents()
        self.create_tasks()

        crew = Crew(
            agents=[self.eclaireur, self.stratege, self.visions_artist, self.designer],
            tasks=[self.investigation_task, self.capture_task, self.visual_creation_task, self.artistic_task],
            process=Process.sequential,
            verbose=True,
            step_callback=self._create_callback("Crew Prep")
        )

        if self.redis_client and self.business_id:
            self.redis_client.set(f"status:{self.business_id}", "🔍 Analyse & Design en cours...")

        crew.kickoff(inputs=self.business_data)

        return {
            "report": self.investigation_task.output.raw if self.investigation_task.output else "",
            "copywriting": self.capture_task.output.raw if self.capture_task.output else "",
            "ai_photos": self.visual_creation_task.output.raw if self.visual_creation_task.output else "",
            "design": self.artistic_task.output.raw if self.artistic_task.output else ""
        }

    def run_build_crew(self, prep_data: dict) -> dict:
        """Phase 2 : HTML generation (streaming) + email draft."""
        if self.redis_client and self.business_id:
            self.redis_client.set(f"status:{self.business_id}", "🏗️ Génération HTML avec Claude...")

        # Generate HTML with real streaming
        html = self._generate_html_streaming(prep_data)

        # Generate email draft via Closer agent
        self.create_agents()
        self.create_tasks()

        deploy_inputs = {**self.business_data, **prep_data}

        email_crew = Crew(
            agents=[self.closer],
            tasks=[self.offensive_task],
            process=Process.sequential,
            verbose=True,
        )
        email_crew.kickoff(inputs=deploy_inputs)

        email_text = self.offensive_task.output.raw if self.offensive_task.output else ""

        return {"html": html, "email": email_text}

    def run_deploy_crew(self, html_content: str) -> str:
        """Phase 3 : Deploy pre-generated HTML to Vercel."""
        if self.redis_client and self.business_id:
            self.redis_client.set(f"status:{self.business_id}", "🚀 Déploiement Vercel...")

        result = self.vercel_tool._run(html_content, self.business_id)
        return result
