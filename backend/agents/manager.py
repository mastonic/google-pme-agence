from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from .tools import VercelDeployTool, FalFluxTool, GmailDraftTool
import os

TEMPLATE_BENTO = """
    <section id="services" class="py-32 px-6 bg-white">
        <div class="max-w-7xl mx-auto">
            <h2 class="text-4xl font-extrabold mb-16 tracking-tight">Nos Incontournables</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="md:col-span-2 bento-card p-10 flex flex-col justify-end min-h-[400px] relative group">
                    <img src="[URL_PHOTO_PRODUIT_1]" class="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-700">
                    <div class="relative z-10 bg-black/20 p-6 rounded-2xl backdrop-blur-sm text-white">
                        <h3 class="text-3xl font-bold">[NOM_PRODUIT_1]</h3>
                        <p class="opacity-80">[PRIX_1]€</p>
                    </div>
                </div>
                <div class="bento-card bg-orange-50 p-10 flex flex-col justify-between">
                    <div class="text-5xl font-bold text-orange-500">100%</div>
                    <p class="text-xl font-semibold leading-tight">Artisanal et préparé avec passion.</p>
                </div>
                <div class="bento-card p-8 group">
                     <img src="[URL_PHOTO_PRODUIT_2]" class="w-full h-48 object-cover rounded-2xl mb-6">
                     <h3 class="text-xl font-bold">[NOM_PRODUIT_2]</h3>
                     <button class="w-full py-3 bg-gray-100 rounded-xl font-bold hover:bg-black hover:text-white transition-colors">Commander</button>
                </div>
                <div class="bento-card p-8 bg-gray-900 text-white flex flex-col justify-center text-center">
                    <h3 class="text-2xl font-extrabold mb-2">Promotion</h3>
                    <p class="text-sm opacity-70">Venez découvrir notre sélection exclusive de la semaine.</p>
                </div>
            </div>
        </div>
    </section>
"""

TEMPLATE_MINIMAL = """
    <section class="relative min-h-screen flex items-center pt-20 px-6">
        <div class="max-w-7xl mx-auto text-center">
            <h1 class="text-7xl md:text-9xl font-black tracking-tighter leading-none mb-10 uppercase" data-aos="fade-up">
                [SLOGAN_ACCROCHEUR]
            </h1>
            <div class="relative max-w-5xl mx-auto" data-aos="zoom-in">
                <img src="[URL_PHOTO_HERO]" class="w-full rounded-[4rem] shadow-2xl aspect-video object-cover">
                <div class="absolute -bottom-10 left-1/2 -translate-x-1/2 flex gap-4">
                    <button class="bg-[#0071E3] text-white px-10 py-5 rounded-full text-xl font-bold shadow-2xl hover:scale-105 transition-transform">RÉSERVER MAINTENANT</button>
                </div>
            </div>
            <p class="text-2xl text-gray-500 mt-24 max-w-2xl mx-auto" data-aos="fade-up">
                [DESCRIPTION_COURTE]
            </p>
        </div>
    </section>
"""

TEMPLATE_SPLIT = """
    <section class="flex flex-col md:flex-row h-screen overflow-hidden">
        <div class="w-full md:w-1/2 h-64 md:h-full sticky top-0">
             <img src="[URL_PHOTO_HERO]" class="w-full h-full object-cover">
        </div>
        <div class="w-full md:w-1/2 h-full overflow-y-auto p-12 md:p-24 bg-white flex flex-col justify-center">
             <div data-aos="fade-left">
                 <span class="text-sm font-bold tracking-widest text-gray-400 uppercase">[NOM_DU_COMMERCE]</span>
                 <h1 class="text-6xl md:text-8xl font-black tracking-tighter mt-4 mb-8">
                     [SLOGAN_ACCROCHEUR]
                 </h1>
                 <p class="text-xl text-gray-500 mb-12 leading-relaxed">
                     [DESCRIPTION_COURTE]
                 </p>
                 <button class="btn-premium w-fit">Prendre Rendez-vous</button>
                 
                 <div class="mt-20 space-y-8">
                     <div class="border-l-4 border-black pl-6">
                         <p class="italic text-lg text-gray-600">"[AVIS_1]"</p>
                         <p class="font-bold mt-2">- [NOM_CLIENT_1]</p>
                     </div>
                 </div>
             </div>
        </div>
    </section>
"""

BASE_HTML = """
<!DOCTYPE html>
<html lang="fr" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[NOM_DU_COMMERCE] - Experience</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #FBFBFD; color: #1D1D1F; }
        .glass { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); }
        .bento-card { @apply bg-white rounded-[2.5rem] shadow-sm hover:shadow-xl transition-all duration-500 overflow-hidden border border-gray-100; }
        .btn-premium { @apply px-8 py-4 bg-[#1D1D1F] text-white rounded-full font-semibold hover:scale-105 active:scale-95 transition-all duration-300; }
    </style>
</head>
<body class="antialiased">
    <nav class="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-[90%] max-w-4xl glass border border-white/20 rounded-full px-6 py-3 flex justify-between items-center shadow-lg">
        <div class="font-extrabold text-xl tracking-tight">[NOM_DU_COMMERCE]</div>
        <div class="hidden md:flex gap-8 text-sm font-medium text-gray-600">
            <a href="#services" class="hover:text-black">Services</a>
            <a href="#avis" class="hover:text-black">Avis</a>
            <a href="#contact" class="hover:text-black">Contact</a>
        </div>
        <a href="tel:[TELEPHONE]" class="bg-black text-white px-5 py-2 rounded-full text-sm font-bold">Appeler</a>
    </nav>

    [MAIN_CONTENT]

    <footer id="contact" class="bg-[#1D1D1F] text-white py-24 rounded-t-[4rem]">
        <div class="max-w-7xl mx-auto px-6 grid md:grid-cols-2 gap-20">
            <div>
                <h2 class="text-5xl font-bold mb-8">On se voit bientôt ?</h2>
                <div class="space-y-6 text-xl text-gray-400">
                    <p>📍 [ADRESSE_COMPLETE]</p>
                    <p>📞 [TELEPHONE]</p>
                    <p>🕒 [HORAIRES]</p>
                </div>
            </div>
            <div class="bg-white/5 p-10 rounded-[3rem] border border-white/10">
                <h3 class="text-2xl font-bold mb-6">Envoyez-nous un message</h3>
                <form class="flex flex-col gap-4">
                    <input type="text" placeholder="Votre Nom" class="bg-transparent border-b border-white/20 py-3 outline-none focus:border-white transition-colors">
                    <input type="email" placeholder="Votre Email" class="bg-transparent border-b border-white/20 py-3 outline-none focus:border-white transition-colors">
                    <textarea placeholder="Votre Message" rows="3" class="bg-transparent border-b border-white/20 py-3 outline-none focus:border-white transition-colors resize-none"></textarea>
                    <button class="btn-premium bg-white text-black mt-4">Envoyer le message</button>
                </form>
            </div>
        </div>
    </footer>

    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
    <script>
        AOS.init({ duration: 1000, once: true });
    </script>
</body>
</html>
"""

class LocalPulseManager:
    def __init__(self, business_data: dict, log_queue=None):
        self.business_data = business_data
        self.log_queue = log_queue
        self.business_id = business_data.get("business_id")
        import asyncio
        try:
            self.loop = asyncio.get_running_loop()
        except:
            self.loop = None
        print(f"!!! MANAGER INIT !!! business_id: {self.business_id}")
        
        # Redis connection for log sharing with Streamlit
        import redis
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
        except:
            self.redis_client = None
        self.openai_model = "gpt-4o-mini"
        self.llm = ChatOpenAI(model=self.openai_model, temperature=0.7)
        self.vercel_tool = VercelDeployTool()
        self.fal_tool = FalFluxTool()
        self.gmail_tool = GmailDraftTool()
        
    def _create_callback(self, agent_name: str):
        print(f"!!! Callback Factory created for {agent_name} !!!")
        def callback(step):
            print(f"!!! CALLBACK CALLED for {agent_name} !!! Object: {step}")
            print(f"!!! CALLBACK TRIGGERED for {agent_name} !!! Step type: {type(step)}")
            msg = ""
            try:
                if isinstance(step, list):
                    for s in step:
                        msg = getattr(s, 'thought', str(s)) or getattr(s, 'text', str(s))
                else:
                    msg = getattr(step, 'thought', str(step)) or getattr(step, 'text', str(step))
                
                if not msg or "failed to parse" in msg.lower() or "invalid format" in msg.lower():
                    return

                log_entry = {"agent": agent_name, "message": msg, "type": "chat"}
                
                # 1. Internal Queue (for FastAPI SSE) - Using thread-safe call
                if self.log_queue is not None and self.loop:
                    self.loop.call_soon_threadsafe(self.log_queue.put_nowait, log_entry)
                
                # 2. Redis (for Streamlit Cockpit)
                if self.redis_client and self.business_id:
                    import json
                    r_key = f"logs:{self.business_id}"
                    print(f"DEBUG: Pushing log to Redis key {r_key}: {msg[:50]}...")
                    self.redis_client.rpush(r_key, json.dumps(log_entry))
                    self.redis_client.set(f"status:{self.business_id}", f"Agent {agent_name} en action...")
                    self.redis_client.expire(r_key, 3600)

                    # Update Template in DB if Designer finished
                    if agent_name == "Le Designer":
                        try:
                            # Extract template name from the output
                            template_matches = ["BENTO_GRID", "MINIMALIST_HERO", "SPLIT_SHOWREEL", "luxury-dining", "clean-medical", "industrial-bold"]
                            for t in template_matches:
                                if t.upper() in msg.upper():
                                    from ..models.database import SessionLocal, Business
                                    db = SessionLocal()
                                    biz = db.query(Business).filter(Business.id == self.business_id).first()
                                    if biz:
                                        biz.template = t
                                        db.commit()
                                    db.close()
                                    break
                        except: pass
                else:
                    print(f"DEBUG: Redis client or business_id missing. Client: {self.redis_client is not None}, ID: {self.business_id}")
            except Exception as e:
                print(f"Callback error: {e}")
        return callback

    def select_template_v2(self, types):
        templates = {
            "restaurant": "luxury-dining-v3",
            "food": "luxury-dining-v3",
            "cafe": "luxury-dining-v3",
            "pharmacy": "clean-medical-v1",
            "doctor": "clean-medical-v1",
            "health": "clean-medical-v1",
            "car_repair": "industrial-bold-v2",
            "car_dealer": "industrial-bold-v2",
            "gas_station": "industrial-bold-v2"
        }
        for t in types:
            if t in templates:
                return templates[t]
        return "universal-modern-v1"

    def create_agents(self):
        # 1. L'Éclaireur (Lead Data Scraper) - Updated for full media scan
        self.eclaireur = Agent(
            role="L'Éclaireur (Lead Data Scraper)",
            goal="Extraire l'ADN d'un commerce et TOUTES les sources de médias disponibles (Propriétaire + Avis).",
            backstory="""Tu es un enquêteur numérique spécialisé. Ta mission est d'analyser {name} à {address}.
            CRITICAL Média : Cherche en priorité les images postées par le propriétaire (logos, devanture) 
            PUIS les images des derniers avis clients (plats, rayons, accueil). 
            Tu ne rates aucun détail : horaires, avis récents, qualité des photos.
            Tu dois identifier : 
            1. Le 'Digital Gap' (Présence Web, Site mobile, Click & Collect). 
            2. 5 Avis récents détaillés avec photos associées si mentionnées.
            3. 5 Liens de photos réelles récupérées via Maps.
            4. Le point faible du concurrent principal à moins de 500m.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False,
            max_iter=3,
            step_callback=self._create_callback("L'Éclaireur")
        )
        
        # 2. Le Stratège de Vente (Conversion Copywriter)
        self.stratege = Agent(
            role="Le Stratège de Vente (Conversion Copywriter)",
            goal="Concevoir un copywriting persuasif basé sur la psychologie de vente locale.",
            backstory="""Tu es un copywriter de haut niveau, spécialisé dans le ROI et le storytelling. 
            Tu es persuasif et empathique. Tu parles le langage du commerçant.
            En utilisant les données de l'Éclaireur, tu rédiges des arguments choc pour {name}, 
            montrant au gérant pourquoi il perd de l'argent face à la concurrence.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False,
            max_iter=3,
            step_callback=self._create_callback("Le Stratège")
        )
        
        # 2.5 Visions Artist (AI Photographer)
        self.visions_artist = Agent(
            role="Visions Artist (AI Photographer)",
            goal="Transformer les descriptions textuelles de l'Éclaireur en visuels de haute voltige.",
            backstory="""Tu es un photographe publicitaire d'élite. Si l'Éclaireur signale un manque de photos de qualité, tu dois concevoir des prompts pour Flux.1 via Fal.ai.
            Analyse le type de commerce (ex: Boulangerie artisanale) et sa LOCALISATION ({address}).
            IMPORTANT : Tu dois adapter le profil des personnages (couleur de peau, style vestimentaire) à la démographie locale. 
            Par exemple, si l'adresse est en Martinique (972), les personnages doivent impérativement avoir une peau antillaise/noire/métisse.
            Crée un prompt décrivant une scène hyper-réaliste, éclairage naturel, style 'Dribbble/Instagram Premium'.
            Assure-toi que les couleurs correspondent à la palette du Designer.
            Utilise des mots-clés comme '8k, photorealistic, depth of field, high-end commercial photography'.
            Ton rôle est de générer UNIQUEMENT l'URL des photos, rien d'autre. Pas de blabla.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False,
            tools=[self.fal_tool],
            max_iter=3,
            step_callback=self._create_callback("Visions Artist")
        )

        # 3. Le Designer Visionnaire (UI/UX Stylist)
        self.designer = Agent(
            role="Le Designer Visionnaire (UI/UX Stylist)",
            goal="Choisir le meilleur template et définir l'identité visuelle adaptée à la niche.",
            backstory="""Tu es un Lead UI/UX Designer d'élite. Tu dois choisir parmi les templates exclusifs :
            - luxury-dining-v3 (Restaurants, Food, Cafe)
            - clean-medical-v1 (Pharmacy, Doctor, Health)
            - industrial-bold-v2 (Garage, Car repair, Industrial)
            - BENTO_GRID, MINIMALIST_HERO, SPLIT_SHOWREEL (Universal)
            
            Directive Templating : {suggested_template} est le choix recommandé basé sur la catégorie.
            
            Storytelling visuel :
            - Restaurants : Ambre, Noir, Crème. Focus sur les plats et l'ambiance.
            - Pharmacie : Blanc, Vert Menthe, Bleu. Focus sur la propreté et la santé.
            - Garage : Gris Acier, Orange, Jaune. Focus sur l'expertise technique.
            
            Tu dois définir la palette Tailwind et les polices Google Fonts.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False,
            max_iter=3,
            step_callback=self._create_callback("Le Designer")
        )
        
        # 4. L'Ingénieur de Déploiement (Fullstack Dev Agent)
        self.ingenieur = Agent(
            role="L'Ingénieur de Déploiement (Fullstack Dev Agent)",
            goal="Construire et déployer le site OnePage sur Vercel.",
            backstory="""Tu es l'artisan efficace et rigoureux. Tu prends le texte du Stratège et 
            le style du Designer pour générer un fichier index.html unique basé sur le Master Template fourni. 
            Tu maîtrises les templates spécifiques : luxury-dining-v3, clean-medical-v1, industrial-bold-v2.
            Tu DOIS ABSOLUMENT remplacer TOUS les placeholders entre crochets [ ] par les données du rapport de l'Éclaireur.
            Une fois le code généré, tu utilises l'outil 'Vercel Deploy Tool' pour le mettre en ligne immédiatement.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False,
            tools=[self.vercel_tool],
            max_iter=3,
            step_callback=self._create_callback("L'Ingénieur")
        )

        # 5. Le Closer (Automated Outreach Specialist)
        self.closer = Agent(
            role="Le Closer (Automated Outreach Specialist)",
            goal="Responsable de l'engagement client et de l'envoi des démos.",
            backstory="""Tu es un expert en vente B2B locale. Ta mission est de prendre l'URL générée par l'Ingénieur 
            et les arguments du Stratège pour contacter le commerçant. Tu es diplomate et persévérant.
            Tu sais transformer une démo technique en une opportunité business irrésistible. Tu DOIS toujours créer un brouillon (Draft) sans jamais l'envoyer directement.""",
            verbose=True,
            llm=self.llm,
            allow_delegation=False,
            tools=[self.gmail_tool],
            max_iter=3,
            step_callback=self._create_callback("Le Closer")
        )

    def create_tasks(self):
        suggested_template = self.select_template_v2(self.business_data.get("types", []))
        
        # Tâche 1 : Investigation Locale
        self.investigation_task = Task(
            description="""Scanner {name} à {address}. 
            CRITICAL : Extraire TOUTES les sources de médias (Propriétaire + derniers avis avec photos).
            Identifier le Digital Gap et formater ta réponse EXACTEMENT selon ce modèle JSON :
            {{
              "{name}": {{
                "nom": "{name}",
                "adresse": "{address}",
                "note": {rating},
                "avis": [
                   {{ "auteur": "Nom", "date": "Date", "note": 5, "commentaire": "Texte...", "photo_url": "URL si dispo" }}
                 ],
                "photos_links": ["URL 1", "URL 2", "URL 3"],
                "Digital Gap": {{
                  "Site mobile": "Non disponible / Disponible",
                  "Click & Collect": "Non offert / Offert"
                }}
              }},
              "Concurrent principal": {{
                "nom": "Nom du concurrent",
                "adresse": "Adresse du concurrent",
                "note": 4.1,
                "point faible": "Description du point faible"
              }}
            }}""",
            expected_output="Un rapport JSON structuré complet avec liens médias réels.",
            agent=self.eclaireur
        )

        # Tâche 2 : Stratégie de Capture
        self.capture_task = Task(
            description="""Analyser le rapport de l'Éclaireur. Rédiger les textes du site (Slogan, Avantages, Preuve sociale). 
            Créer un tableau Markdown intitulé "Perte de revenus vs Potentiel" croisant les statistiques du concurrent principal avec la situation du commerce scanné.""",
            expected_output="Contenu marketing complet (Copywriting).",
            agent=self.stratege
        )

        # Tâche 2.5 : Création Visuelle
        self.visual_creation_task = Task(
            description="""Générer 2 visuels 'Hero' premium via Fal.ai adaptés à la catégorie du commerce.
            RESPECT DE LA LOCALITÉ : Analyse {address}. Si des personnages apparaissent, ils doivent refléter la démographie locale.""",
            expected_output="URLs des images générées.",
            agent=self.visions_artist
        )

        # Tâche 3 : Direction Artistique
        self.artistic_task = Task(
            description=f"""1. Analyser le rapport d'investigation.
            2. CONFIRMER l'usage du template : {suggested_template} (ou proposer BENTO_GRID/MINIMALIST_HERO s'il est plus pertinent).
            3. Storytelling visuel : Définir la palette (ex: Ambre/Noir pour resto) et les typos.
            Répondre avec le Nom du template choisi en premier.""",
            expected_output="Directives de design et template sélectionné.",
            agent=self.designer
        )

        # Tâche 4 : Assemblage & Déploiement
        self.build_task = Task(
            description=f"""Prendre tous les éléments marketing et visuels. 
            Injecter ces données dans le code source du template sélectionné ({suggested_template} par défaut).
            Utiliser 'Vercel Deploy Tool' pour le déploiement immédiat.
            Le 'project_name' doit être '{self.business_id}'.""",
            expected_output="Confirmation du déploiement avec l'URL live.",
            agent=self.ingenieur
        )

        # Tâche 5 : Offensive Commerciale
        self.offensive_task = Task(
            description="""Rédiger un email de prospection unique et hyper personnalisé. 
            L'email DOIT inclure l'URL de démo et l'argumentaire comparatif.""",
            expected_output="Texte final de l'email personnalisé.",
            agent=self.closer
        )

    def run_prep_crew(self):
        self.create_agents()
        self.create_tasks()
        
        crew = Crew(
            agents=[self.eclaireur, self.stratege, self.visions_artist, self.designer],
            tasks=[self.investigation_task, self.capture_task, self.visual_creation_task, self.artistic_task],
            process=Process.sequential,
            verbose=True,
            step_callback=self._create_callback("Crew Prep")
        )
        
        print(f"DEBUG: Starting Crew Prep for {self.business_id}...")
        crew.kickoff(inputs=self.business_data)
        print("DEBUG: Crew Prep finished.")
        
        structured_output = {
            "report": self.investigation_task.output.raw if self.investigation_task.output else "",
            "copywriting": self.capture_task.output.raw if self.capture_task.output else "",
            "ai_photos": self.visual_creation_task.output.raw if self.visual_creation_task.output else "",
            "design": self.artistic_task.output.raw if self.artistic_task.output else ""
        }
        return structured_output

    def run_deploy_crew(self, prep_data):
        self.create_agents()
        self.create_tasks()
        
        # We need to inject the prep data into the inputs so the engineers/closers know what to build
        deploy_inputs = {
            **self.business_data,
            "report": prep_data.get("report", ""),
            "copywriting": prep_data.get("copywriting", ""),
            "ai_photos": prep_data.get("ai_photos", ""),
            "design": prep_data.get("design", "")
        }

        # Modify tasks for deploy step to explicitly use the prep data
        self.build_task.description = f"""
        Assembler le code HTML/Tailwind parfait pour '{deploy_inputs['name']}'.
        
        Choix du Template par le Designer : {deploy_inputs['design']}
        
        CODE DES TEMPLATES DISPONIBLES :
        --- BASE_HTML ---
        {BASE_HTML}
        
        --- TEMPLATE_BENTO ---
        {TEMPLATE_BENTO}
        
        --- TEMPLATE_MINIMAL ---
        {TEMPLATE_MINIMAL}
        
        --- TEMPLATE_SPLIT ---
        {TEMPLATE_SPLIT}
        
        INSTRUCTIONS:
        1. Identifie quel template a été choisi par le Designer ({deploy_inputs['design']}).
        2. Utilise BASE_HTML comme structure globale.
        3. Remplace [MAIN_CONTENT] par le code du template choisi.
        4. Remplace TOUS les placeholders entre crochets [ ] (ex: [NOM_DU_COMMERCE], [ADRESSE_COMPLETE], [URL_PHOTO_HERO]) par les données réelles du rapport : {deploy_inputs['report']}.
        5. Si des photos ont été générées ({deploy_inputs['ai_photos']}), utilise leurs URLs.
        
        Une fois le code HTML complet assemblé, utilise le VercelDeployTool pour le mettre en ligne.
        """
        
        self.offensive_task.description = f"""
        TA MISSION LA PLUS IMPORTANTE : Rédiger un email de prospection unique, ultra-personnalisé et humain pour '{deploy_inputs['name']}'.
        
        L'email DOIT inclure :
        1. L'URL de démo générée : [URL_VERCEL_GENEREE]
        2. Un argumentaire basé sur leur note de {deploy_inputs.get('rating', 'N/A')}/5.
        3. Une proposition de rendez-vous.
        
        D'ABORD, utilise le GmailDraftTool pour créer le brouillon.
        
        ENSUITE, ta RÉPONSE FINALE doit impérativement suivre cette structure :
        --- EMAIL CONTENT START ---
        (Insère ici tout le texte de ton email)
        --- EMAIL CONTENT END ---
        
        Puis termine par ta signature technique :
        [{deploy_inputs.get('business_id', 'Unknown ID')}] | [URL_VERCEL_GENEREE] | [Flux Images: {'Yes' if deploy_inputs.get('ai_photos') and deploy_inputs['ai_photos'] != 'Pas besoin de nouvelles photos' else 'No'}] | [Gmail Draft: Ready] | [Benchmark: Done]
        
        IMPORTANT : Remplace [URL_VERCEL_GENEREE] par la vraie URL fournie par l'ingénieur.
        """
        
        crew = Crew(
            agents=[self.ingenieur, self.closer],
            tasks=[self.build_task, self.offensive_task],
            process=Process.sequential,
            verbose=True,
            step_callback=self._create_callback("Crew Deploy")
        )
        
        result = crew.kickoff(inputs=deploy_inputs)
        
        import json
        structured_output = {
            "email": self.offensive_task.output.raw if self.offensive_task.output else "",
            "vercel_url": getattr(self.build_task.output, 'raw', ''),
            "orchestration_summary": str(result), # Contains the final formatted string
            **prep_data # Keep previous data
        }
        
        return json.dumps(structured_output)
