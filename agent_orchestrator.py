import os
import redis
import json
import time
import threading
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from tools.VercelDeployTool import VercelDeployTool
from tools.FalFluxTool import FalFluxTool
from tools.GmailDraftTool import GmailDraftTool
from tools.GoogleMapsTool import GoogleMapsTool
from local_queue import FileQueue, StatusStore
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Connexion à Redis (avec fallback sur FileQueue)
QUEUE_NAME = "local_pulse_tasks"

def get_redis_connection():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None

# ==========================================
# 2. DEFINITION DE L'ÉQUIPE CREWAI
# ==========================================
def create_local_pulse_crew(business_name, place_id, project_id):
    """Initialise l'équipe d'agents pour un business donné."""
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # Agent 1 : L'Éclaireur
    scout = Agent(
        role="Éclaireur Maps",
        goal=f"Extraire infos, photos et concurrents pour {business_name} (ID: {place_id})",
        backstory="Expert en données locales Google Maps.",
        llm=llm, verbose=True, allow_delegation=False,
        tools=[GoogleMapsTool()]
    )

    # Agent 2 : Visions Artist
    vision = Agent(
        role="AI Photographer",
        goal=f"Générer 2 images premium (Hero/Produit) pour {business_name} via Fal.ai",
        backstory="Esthète obsédé par le réalisme cinématique.",
        llm=llm, verbose=True, allow_delegation=False,
        tools=[FalFluxTool()]
    )

    # Agent 3 : Le Designer
    designer = Agent(
        role="Designer UI/UX",
        goal=f"Définir l'identité visuelle et choisir le template le plus adapté pour {business_name}",
        backstory="""Expert en design minimaliste et premium. Tu analyses le nombre de photos produits
        pour décider si le template sera Bento Grid, Minimalist Hero ou Split Showreel.""",
        llm=llm, verbose=True, allow_delegation=False
    )

    # Agent 4 : Ingénieur Dev
    dev = Agent(
        role="Vercel Integrator",
        goal=f"Créer le OnePage HTML/Tailwind pour {business_name} en utilisant le template choisi par le Designer et le déployer sur Vercel",
        backstory="""Tu es un artisan du code propre et rapide. Tu reçois le choix du template (Bento, Minimalist ou Split) 
        et tu injectes les données dans la structure HTML correspondante. Tu utilises Tailwind CSS et AOS pour un rendu premium.""",
        llm=llm, verbose=True, allow_delegation=False,
        tools=[VercelDeployTool()]
    )

    # Agent 5 : Le Closer
    closer = Agent(
        role="Outreach Specialist",
        goal=f"Rédiger le mail de vente et créer le brouillon dans Gmail pour {business_name}",
        backstory="Expert en psychologie de vente locale B2B.",
        llm=llm, verbose=True, allow_delegation=False,
        tools=[GmailDraftTool()]
    )

    # Définition des Tâches
    task_maps = Task(description=f"Investigation Maps pour {business_name}", agent=scout, expected_output="Localisation and competitors")
    task_images = Task(description=f"Génération d'images si nécessaire pour {business_name}", agent=vision, expected_output="Two premium images")
    
    task_design = Task(
        description=f"""Analyse les infos de {business_name}. Choisis le meilleur template parmi :
        1. Bento Grid (si > 5 photos produits)
        2. Minimalist Hero (si 1 photo d'ambiance forte ou générée par l'IA)
        3. Split Showreel (si domaine esthétique comme Coiffeur/Spa).
        Définis aussi la palette de couleurs Bleu Électrique/Vert Menthe.""",
        agent=designer,
        expected_output="Template choisi et palette de couleurs"
    )

    task_build = Task(
        description=f"""Build le code HTML final pour {business_name} en utilisant le template choisi.
        SÉCURITÉ DÉMO : Filigrane Local-Pulse Demo, Flou media, Bloque clic droit/F12.
        Lien d'activation: https://local-pulse.app/activate?id={project_id}""",
        agent=dev, 
        expected_output="Vercel URL du site sécurisé et déployé"
    )
    
    task_mail = Task(description=f"Rédaction et création brouillon Gmail pour {business_name}", agent=closer, expected_output="Email draft drafted in Gmail")

    # Orchestration
    crew = Crew(
        agents=[scout, vision, designer, dev, closer],
        tasks=[task_maps, task_images, task_design, task_build, task_mail],
        process=Process.sequential, verbose=True
    )
    
    return crew

# ==========================================
# 3. L'ORCHESTRATEUR
# ==========================================
def update_status(project_id, message):
    r = get_redis_connection()
    if r:
        r.set(f"status:{project_id}", message)
    else:
        StatusStore().set(f"status:{project_id}", message)

def worker_orchestrator():
    """Tourne en boucle et surveille la file d'attente (Redis ou File)."""
    r_check = get_redis_connection()
    if r_check:
        print("🕵️‍♂️ Orchestrateur Local-Pulse : Connecté à Redis (localhost:6379)")
    else:
        print("🕵️‍♂️ Orchestrateur Local-Pulse : Mode FileQueue (Redis absent)")
    
    while True:
        r = get_redis_connection()
        task_data_json = None
        
        if r:
            res = r.blpop(QUEUE_NAME, timeout=2) # On s'assure de ne pas bloquer éternellement
            if res:
                task_data_json = res[1]
        else:
            task_data_json = FileQueue().pop()
        
        if task_data_json:
            try:
                task_data = json.loads(task_data_json)
                biz_name = task_data['business_name']
                place_id = task_data['place_id']
                project_id = task_data['project_id']

                print(f"🚀 Nouvelle tâche reçue : {biz_name} (ID: {place_id})")
                update_status(project_id, "🔴 En cours d'investigation...")

                # 2. Lancement CrewAI
                crew = create_local_pulse_crew(biz_name, place_id, project_id)
                final_result = crew.kickoff()

                update_status(project_id, "✅ Terminé")
                r_store = get_redis_connection()
                if r_store:
                    r_store.set(f"result:{project_id}", str(final_result))
                else:
                    StatusStore().set(f"result:{project_id}", str(final_result))
                
                print(f"✅ Tâche complétée pour {biz_name}.")
                
            except Exception as e:
                project_id = task_data.get('project_id', 'unknown')
                update_status(project_id, f"❌ Erreur : {str(e)}")
                print(f"❌ Erreur : {str(e)}")

        time.sleep(1)

if __name__ == "__main__":
    worker_orchestrator()
