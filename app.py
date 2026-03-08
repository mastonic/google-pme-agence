import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
import threading
import time
from crewai import Agent, Task, Crew, Process
from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI
import os
import redis
import json
from local_queue import FileQueue, StatusStore
from dotenv import load_dotenv
import requests
import re
from backend.services.google_maps import GoogleMapsService

# Initialize Google Maps Service
maps_service = GoogleMapsService()
API_URL = "http://localhost:8000"

def get_redis_conn():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# ==========================================
# 0. HELPER FUNCTIONS
# ==========================================
def update_business_status(biz_id, status):
    """Met à jour le statut via l'API backend."""
    try:
        requests.patch(f"{API_URL}/businesses/{biz_id}", json={"status": status})
        return True
    except: return False

def get_businesses():
    """Récupère la liste des commerces sans cache pour garantir la fraîcheur après un scan."""
    try:
        response = requests.get(f"{API_URL}/businesses")
        if response.status_code == 200:
            data = response.json()
            # On s'assure que chaque business a bien ses coordonnées
            return [b for b in data if b.get('latitude') and b.get('longitude')]
    except Exception as e:
        print(f"Error fetching businesses: {e}")
    return []

def scan_businesses(lat, lng):
    try:
        response = requests.post(f"{API_URL}/scan?lat={lat}&lng={lng}&radius=1000")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error scanning: {e}")
    return None

def get_neighborhood_stats(current_biz_id, city):
    """Extrait le leader du quartier depuis la base SQLite."""
    try:
        import sqlite3
        conn = sqlite3.connect('local_pulse.db')
        cursor = conn.cursor()
        # Try city first
        cursor.execute('''
            SELECT name, potential_score FROM businesses 
            WHERE id != ? AND address LIKE ? 
            ORDER BY potential_score DESC LIMIT 1
        ''', (current_biz_id, f'%{city}%'))
        leader = cursor.fetchone()
        
        # Global fallback if city empty
        if not leader:
            cursor.execute('''
                SELECT name, potential_score FROM businesses 
                WHERE id != ? 
                ORDER BY potential_score DESC LIMIT 1
            ''', (current_biz_id,))
            leader = cursor.fetchone()
            
        conn.close()
        return leader
    except Exception: return None

def calculate_capture_math(biz_id, city):
    """Calcule le potentiel de capture par rapport au leader local."""
    try:
        import sqlite3
        import math
        conn = sqlite3.connect('local_pulse.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rating, user_ratings_total, potential_score FROM businesses WHERE id = ?", (biz_id,))
        p = cursor.fetchone()
        
        # Search leader
        cursor.execute("SELECT rating, user_ratings_total, potential_score FROM businesses WHERE address LIKE ? AND id != ? ORDER BY potential_score DESC LIMIT 1", (f'%{city}%', biz_id))
        l = cursor.fetchone()
        
        if not l: # Fallback to global best
            cursor.execute("SELECT rating, user_ratings_total, potential_score FROM businesses WHERE id != ? ORDER BY potential_score DESC LIMIT 1", (biz_id,))
            l = cursor.fetchone()
            
        conn.close()
        if not p or not l: return 15 # Basal improvement
        
        # Math: Capture depends on Score Gap + Review volume gap
        p_val = (p[0] or 0) * math.log((p[1] or 0) + 1.1)
        l_val = (l[0] or 0) * math.log((l[1] or 0) + 1.1)
        
        if l_val <= p_val: return 10 # Maintenance gain
        
        gap = (l_val - p_val) / l_val
        return min(int(gap * 50), 45) # Max 45% gain
    except Exception: return 15

# --- RÉCUPÉRATION DES VRAIES DATA SQLITE POUR LE DASHBOARD ---
def get_real_stats():
    import sqlite3
    try:
        conn = sqlite3.connect('local_pulse.db')
        cursor = conn.cursor()
        
        # Compte total des démos générées (status différent de scanned)
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE status != 'scanned'")
        total_demos = cursor.fetchone()[0]
        
        # Calcul du MRR réel (ex: 150€/mois par client au statut 'completed')
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE status = 'completed'")
        clients_signes = cursor.fetchone()[0]
        real_mrr = clients_signes * 150
        
        conn.close()
        return total_demos, real_mrr
    except:
        return 0, 0

def get_growth_data():
    import sqlite3
    import pandas as pd
    try:
        conn = sqlite3.connect('local_pulse.db')
        # On groupe par date de mise à jour pour simuler l'historique
        df = pd.read_sql_query("""
            SELECT date(updated_at) as date, COUNT(*) as nb 
            FROM businesses 
            WHERE status != 'scanned'
            GROUP BY date(updated_at) 
            ORDER BY date ASC
        """, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 1. CONFIGURATION & STYLE (Look Premium)
# ==========================================
st.set_page_config(page_title="Local-Pulse | Cockpit", layout="wide", page_icon="🦊")

# Style CSS pour le look "Apple Premium" (Light Mode)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    :root {
        --brand-blue: #0071E3;
        --brand-teal: #00BFA5;
        --bg-light: #FBFBFD;
        --text-dark: #1D1D1F;
        --text-dim: #86868B;
        --glass: rgba(255, 255, 255, 0.8);
    }

    * { font-family: 'Inter', sans-serif !important; }
    
    .stApp { background-color: var(--bg-light); }
    
    /* Header & Sidebar branding */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    
    /* Glass Cards */
    .glass-card { 
        background: white; 
        padding: 30px; 
        border-radius: 35px; 
        box-shadow: 0 10px 40px rgba(0,0,0,0.03); 
        border: 1px solid rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }

    /* Buttons */
    .stButton>button { 
        border-radius: 16px; 
        padding: 12px 28px; 
        background: linear-gradient(135deg, var(--brand-blue), var(--brand-teal));
        color: white; border: none; font-weight: 700;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 10px 20px rgba(0, 113, 227, 0.2);
    }
    .stButton>button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 15px 30px rgba(0, 113, 227, 0.3);
        color: white;
    }

    /* Cockpit Bubbles */
    .cockpit-bubble {
        background: white;
        border-radius: 28px;
        margin-bottom: 25px;
        overflow: hidden;
        box-shadow: 0 15px 45px rgba(0,0,0,0.05);
        border: 1px solid rgba(0,0,0,0.03);
    }
    .cockpit-header {
        padding: 15px 25px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 800;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .header-scout { background: rgba(0, 113, 227, 0.1); color: var(--brand-blue); border-bottom: 1px solid rgba(0, 113, 227, 0.1); }
    .header-designer { background: rgba(0, 191, 165, 0.1); color: var(--brand-teal); border-bottom: 1px solid rgba(0, 191, 165, 0.1); }
    .header-closer { background: rgba(255, 145, 0, 0.1); color: #FF9100; border-bottom: 1px solid rgba(255, 145, 0, 0.1); }
    
    .cockpit-body {
        padding: 25px;
        font-size: 1rem;
        line-height: 1.7;
        color: #424245;
    }

    /* NEON PULSE BUTTON */
    .neon-pulse {
        background: linear-gradient(135deg, #FF3B30, #FF9500) !important;
        box-shadow: 0 0 20px rgba(255, 59, 48, 0.4) !important;
        border: none !important;
        color: white !important;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 10px rgba(255, 59, 48, 0.4); }
        50% { box-shadow: 0 0 25px rgba(255, 59, 48, 0.7); }
        100% { box-shadow: 0 0 10px rgba(255, 59, 48, 0.4); }
    }

    /* Progress Bar Gradient */
    .digital-gap-bar {
        height: 10px;
        border-radius: 5px;
        background: #F2F2F7;
        width: 100%;
        margin: 15px 0;
        overflow: hidden;
    }
    .digital-gap-fill {
        height: 100%;
        border-radius: 5px;
        background: linear-gradient(90deg, #E5E5EA 0%, #FF3B30 100%);
    }

    .stat-pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        background: #F2F2F7;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #1D1D1F;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    /* Stats Bar */
    .stats-container {
        display: flex;
        justify-content: center;
        gap: 15px;
        margin-top: -30px;
        margin-bottom: 40px;
    }
    .stat-badge {
        background: white;
        padding: 10px 20px;
        border-radius: 14px;
        font-size: 0.9rem;
        font-weight: 600;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 4px 15px rgba(0,0,0,0.02);
    }
    .stat-label { color: var(--text-dim); margin-right: 8px; font-weight: 500; }
    .stat-value { color: var(--text-dark); font-weight: 700; }

    /* Responsive Grid for CRM */
    .glass-card { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
    .glass-card:hover { transform: translateY(-5px); box-shadow: 0 20px 60px rgba(0,0,0,0.08); }

    /* Tablet/Mobile Adjustments */
    @media (max-width: 1200px) {
        .stats-container { flex-wrap: wrap; margin-top: 0; }
        .glass-card { padding: 20px; border-radius: 20px; }
    }
    
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
        .stats-container { justify-content: flex-start; padding: 0 10px; }
        .stat-badge { width: 100%; border-radius: 12px; margin-bottom: 5px; }
        .phone-vessel { display: none; } /* Hide heavy mockup on mobile to save space */
    }

    /* Smartphone Mockup Scaling */
    .phone-vessel {
        border: 8px solid #1D1D1F; 
        border-radius: 40px; 
        background: white; 
        padding: 10px; 
        box-shadow: 0 20px 50px rgba(0,0,0,0.1); 
        width: 100%; 
        max-width: 250px; 
        margin: 20px auto; 
        min-height: 480px; 
        position: relative;
    }
    
    /* Responsive Grid for CRM */
    .crm-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 24px;
        width: 100%;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #E0E0E0; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #D0D0D0; }

    /* Correction Contraste Sidebar */
    [data-testid="stSidebar"] { background-color: #FBFBFD !important; border-right: 1px solid #EAEAEA; }
    [data-testid="stSidebar"] .st-emotion-cache-17l69k { color: #1a1c23 !important; font-weight: 600 !important; }
    
    /* Force la couleur des labels de la sidebar */
    [data-testid="stSidebar"] label {
        color: #111827 !important;
        font-weight: 600 !important;
    }

    /* Fix visibilité texte et icônes dans option_menu */
    .nav-link span, .nav-link i {
        opacity: 1 !important;
    }

    /* Widget Objectif (Gauge) */
    .goal-container {
        background: white; padding: 20px; border-radius: 20px; text-align: center;
        border: 1px solid #EAEAEA; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .gauge-circle {
        width: 120px; height: 120px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; margin: 0 auto;
    }
    .gauge-inner {
        width: 90px; height: 90px; background: white; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2em;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. INITIALISATION DE LA MÉMOIRE (Session State)
# ==========================================
if 'last_business' not in st.session_state:
    st.session_state.last_business = None
if 'map_center' not in st.session_state:
    st.session_state.map_center = [48.8566, 2.3522] # Paris par défaut
if 'crew_history' not in st.session_state:
    st.session_state.crew_history = [] # Stocke la discussion des agents
if 'is_crew_running' not in st.session_state:
    st.session_state.is_crew_running = False
if 'businesses' not in st.session_state:
    st.session_state.businesses = get_businesses()
if 'last_scan_center' not in st.session_state:
    st.session_state.last_scan_center = None

# ==========================================
# 3. LE CALLBACK HANDLER CREWAI (Live Streaming)
# ==========================================
class StreamlitChatCallbackHandler(BaseCallbackHandler):
    """Intercepte les pensées structurées des agents CrewAI pour Streamlit."""
    def __init__(self, agent_name):
        self.agent_name = agent_name

    def on_agent_action(self, action, **kwargs):
        # On n'intercepte que les pensées significatives
        if len(action.log) > 10:
            st.session_state.crew_history.append({
                "type": "agent",
                "name": self.agent_name,
                "text": action.log
            })

# ==========================================
# 4. SIMULATION DE LA LOGIQUE CREWAI (Threaded)
# ==========================================
def run_crewai_thread(business_name):
    """Exécute le workflow CrewAI dans un thread séparé."""
    
    # 1. Configuration des Agents avec Callbacks greffés sur le LLM
    # (Remplace gpt-4 par gpt-3.5 pour réduire les coûts)
    scout_llm = ChatOpenAI(model_name="gpt-4o-mini", callbacks=[StreamlitChatCallbackHandler("Éclaireur")])
    scout = Agent(
        role='Éclaireur Maps',
        goal=f'Trouver les infos et avis sur {business_name} sur Google Maps',
        backstory='Expert en extraction de données locales.',
        llm=scout_llm, verbose=True
    )

    designer_llm = ChatOpenAI(model_name="gpt-4o-mini", callbacks=[StreamlitChatCallbackHandler("Designer UI")])
    designer = Agent(
        role='Designer UI/UX',
        goal=f'Créer une palette de couleurs et un layout pour {business_name}',
        backstory='Spécialiste du design minimaliste et premium.',
        llm=designer_llm, verbose=True
    )

    # 2. Définition des Tâches
    task1 = Task(description=f'Scraper Google Maps pour {business_name}', agent=scout, expected_output="Informations sur l'entreprise")
    task2 = Task(description=f'Créer le design (Couleurs, Layout) pour {business_name}', agent=designer, expected_output="Recommandations de design")

    # 3. Exécution
    st.session_state.crew_history.append({"type": "system", "text": f"Démarrage de l'orchestration pour {business_name}..."})
    
    crew = Crew(agents=[scout, designer], tasks=[task1, task2], process=Process.sequential)
    
    # Kickoff réel (Simulation temps de calcul)
    result = crew.kickoff()
    
    # 4. Finalisation
    st.session_state.crew_history.append({"type": "system", "text": f"✅ Tâche terminée.\n\nRésultat : {result}"})
    st.session_state.is_crew_running = False
    st.session_state.last_demo_url = f"https://{business_name.lower().replace(' ', '-')}.vercel.app"

# ==========================================
# 5. BARRE LATÉRALE : MENU & RECHERCHE
# ==========================================
with st.sidebar:
    # Logo & Branding based on mockup
    st.markdown("""
        <div class="sidebar-logo">
            <svg width="32" height="32" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M50 95C50 95 85 60 85 35C85 15.67 69.33 0 50 0C30.67 0 15 15.67 15 35C15 60 50 95 50 95Z" fill="url(#logoGrad)"/>
                <circle cx="50" cy="35" r="15" fill="white"/>
                <path d="M35 35H45L50 20L55 50L60 35H65" stroke="#0071E3" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
                <defs>
                    <linearGradient id="logoGrad" x1="50" y1="0" x2="50" y2="95" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#0071E3"/>
                        <stop offset="1" stop-color="#00BFA5"/>
                    </linearGradient>
                </defs>
            </svg>
            <span style="font-weight: 800; font-size: 1.4rem; tracking: -0.02em; color: #1D1D1F;">Local--Pulse</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Menu de Navigation (Matching Mockup Labels/Icons)
    selected_menu = option_menu(
        menu_title=None,
        options=["Dashboard", "Campaigns", "Cockpit", "CRM", "Settings"],
        icons=["house", "layout-text-window", "terminal", "inbox", "gear"],
        menu_icon="cast", default_index=1,
        styles={
            "container": {"background-color": "transparent", "padding": "0 !important"},
            "icon": {"color": "#6B7280", "font-size": "18px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "border-radius": "12px", "padding": "12px 20px", "color": "#1D1D1F"},
            "nav-link-selected": {"background-color": "#0071E3", "color": "#FFFFFF", "font-weight": "700", "box-shadow": "0 8px 20px rgba(0, 113, 227, 0.2)"}
        }
    )
    
    st.markdown("---")
    st.subheader("🌐 Zone de Recherche")
    search_query = st.text_input("Ville ou Code Postal", value="Paris")
    
    if st.button("Centrer la Map", use_container_width=True):
        st.toast(f"Recherche de : {search_query}")
        # FALLBACK MANUEL POUR MARTINIQUE SI API GEOCODING NON ACTIVE
        if "972" in search_query or "martinique" in search_query.lower():
            st.session_state.map_center = [14.6035, -61.0662] # Fort-de-France
            st.rerun()
        else:
            geo_result = maps_service.geocode(search_query)
            if isinstance(geo_result, dict) and "error" not in geo_result:
                st.session_state.map_center = [geo_result["lat"], geo_result["lng"]]
                st.rerun()
            else:
                st.error(f"Erreur de géocodage: {geo_result.get('error', 'Inconnu')}")
                st.info("💡 Note: Si l'API Geocoding n'est pas activée, essayez de taper '97200' ou 'Martinique' (fallback activé).")

# Top Stats Bar
st.markdown("""
    <div class="stats-container">
        <div class="stat-badge"><span class="stat-label">Démos Créées:</span><span class="stat-value">128</span></div>
        <div class="stat-badge"><span class="stat-label">MRR:</span><span class="stat-value">1,450€</span></div>
    </div>
""", unsafe_allow_html=True)

# MAPPING SELECTED MENU TO LOGIC
if selected_menu == "Dashboard":
    # 1. Extraction des données réelles
    import sqlite3
    total_demos, real_mrr = get_real_stats()
    growth_df = get_growth_data()
    objectif_mrr = 5000
    calcul_gauge = min(int((real_mrr / objectif_mrr) * 100), 100) if objectif_mrr > 0 else 0

    st.title("📊 Agence Dashboard")
    
    # 2. Vrais KPIs (Style Metric Apple)
    col1, col2, col3 = st.columns(3)
    col1.metric("Démos Créées", total_demos, f"+{total_demos}" if total_demos > 0 else None)
    col2.metric("Revenus Réels (MRR)", f"{real_mrr}€", "Premium")
    col3.metric("Objectif", f"{objectif_mrr}€", f"{calcul_gauge}% atteint")

    st.markdown("---")

    left_col, mid_col, right_col = st.columns([2, 1, 1])

    with left_col:
        st.markdown("#### 📈 Historique de Prospection")
        if not growth_df.empty:
            st.area_chart(growth_df.set_index('date'), color="#0071E3", height=250)
        else:
            st.info("💡 Aucune donnée de prospection encore enregistrée. Lancez un scan pour commencer.")

    with mid_col:
        st.markdown("#### 🎯 Objectif")
        st.markdown(f"""
            <div class="goal-container">
                <div class="gauge-circle" style="background: conic-gradient(#0071E3 {calcul_gauge}%, #F2F2F7 0);">
                    <div class="gauge-inner">{calcul_gauge}%</div>
                </div>
                <p style="margin-top:10px; font-weight:bold; color:#1D1D1F;">{real_mrr}€ / {objectif_mrr}€</p>
                <small style="color:#86868B;">Objectif de croissance mensuel</small>
            </div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown("#### ⚡ Derniers Scans")
        try:
            conn = sqlite3.connect('local_pulse.db')
            recent = pd.read_sql_query("SELECT name, status FROM businesses ORDER BY updated_at DESC LIMIT 5", conn)
            conn.close()
            
            if not recent.empty:
                for _, row in recent.iterrows():
                    icon = "🟢" if row['status'] in ["completed", "deployed"] else "🟠" if row['status'] == "processing" else "⚪"
                    st.write(f"{icon} **{row['name']}**")
            else:
                st.caption("Aucun scan récent.")
        except:
            st.caption("Erreur de connexion BDD.")

elif selected_menu == "Campaigns":
    st.title("📍 Prospection & Campagnes")
    
    col_map, col_fiche = st.columns([2, 1])
    with col_map:
        m = folium.Map(location=st.session_state.map_center, zoom_start=14, tiles="CartoDB positron")
        
        # ADD MARKERS FIRST
        all_biz = get_businesses()
        for biz in all_biz[:150]: # Show up to 150 for performance
            color = 'red' if biz.get('potential_score', 0) >= 8.0 else 'orange' if biz.get('potential_score', 0) >= 5.0 else 'blue'
            folium.Marker(
                [biz['latitude'], biz['longitude']], 
                popup=biz['name'],
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)

        # Then display map
        map_data = st_folium(m, width=900, height=600, key="prospect_map")
        
        # CRITICAL: Update session state when map moves so scan uses current view
        if map_data and map_data.get('center'):
            st.session_state.map_center = [map_data['center']['lat'], map_data['center']['lng']]
        
        if st.button("🔍 Scanner cette zone", use_container_width=True):
            with st.spinner(f"Analyse Google Maps à ({st.session_state.map_center[0]:.4f}, {st.session_state.map_center[1]:.4f})..."):
                scan_result = scan_businesses(st.session_state.map_center[0], st.session_state.map_center[1])
                if scan_result:
                    count = scan_result.get('count', 0)
                    st.success(f"✅ {count} commerces trouvés !")
                    if count > 0:
                        st.session_state.businesses = get_businesses() # Refresh local list
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Le scan n'a retourné aucun résultat.")
        if map_data and map_data.get('last_object_clicked_popup'):
            clicked_name = map_data['last_object_clicked_popup']
            for b in businesses:
                if b['name'] == clicked_name:
                    st.session_state.last_business_obj = b
                    st.session_state.last_business = clicked_name
                    st.rerun()

    with col_fiche:
        # 1. Création du conteneur dynamique pour la fiche
        fiche_sidebar = st.empty()

        if st.session_state.get('last_business_obj'):
            biz = st.session_state.last_business_obj
            # On affiche la fiche initiale dans le container empty
            with fiche_sidebar.container():
                # --- INITIALISATION ---
                competitor_name = "le standard du marché"
                # --- GESTION DU CACHE D'ANALYSE (SImulation High-Tech) ---
                if 'analyzed_cache' not in st.session_state: st.session_state.analyzed_cache = set()
                
                if biz['id'] not in st.session_state.analyzed_cache:
                    with st.status(f"🕵️‍♂️ Local--Pulse analyse {biz['name']}...", expanded=True) as status:
                        st.write("Extraction des derniers avis GMB et analyse sémantique...")
                        time.sleep(1.2)
                        st.write("Calcul du Digital Gap Score face aux leaders locaux...")
                        time.sleep(1.0)
                        st.write("Simulation de l'interface mobile exclusive...")
                        time.sleep(0.8)
                        status.update(label="✅ Diagnostic terminé !", state="complete", expanded=False)
                    st.session_state.analyzed_cache.add(biz['id'])
                    # On affiche brièvement le score avant le rerun pour fluidité
                    st.toast(f"Analyse terminée pour {biz['name']}", icon="✅")
                    st.rerun()

                # --- HEADER VISUEL (Hero Section) ---
                photo_url = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800" # Img Commerce
                st.markdown(f"""
                    <div style="background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.6)), url('{photo_url}'); 
                                height:160px; border-radius:28px; display:flex; flex-direction: column; align-items:flex-start; justify-content:flex-end; padding: 25px; color:white; background-size: cover; background-position: center; margin-bottom: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.1);">
                        <h3 style="margin:0; font-weight: 800; font-size: 1.5rem; text-shadow: 0 2px 15px rgba(0,0,0,0.4);">{biz['name'].upper()}</h3>
                        <p style="margin:0; font-size: 0.8rem; opacity: 0.9; font-weight: 500; display: flex; align-items: center; gap: 5px;">
                            📍 {biz.get('address', 'Localisation en cours...')[:45]}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                # --- VISUAL BADGES (Metrics) ---
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; gap: 12px; margin-bottom: 25px;">
                        <div style="flex:1; background: rgba(52, 199, 89, 0.08); padding: 15px 10px; border-radius: 20px; text-align: center; border: 1px solid rgba(52, 199, 89, 0.15);">
                            <span style="display: block; font-size: 1.3rem; font-weight: 800; color: #28a745;">{biz.get('rating', '0')}</span>
                            <small style="color: #666; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Confiance</small>
                        </div>
                        <div style="flex:1; background: rgba(255, 59, 48, 0.08); padding: 15px 10px; border-radius: 20px; text-align: center; border: 1px solid rgba(255, 59, 48, 0.15);">
                            <span style="display: block; font-size: 1.3rem; font-weight: 800; color: #FF3B30;">{len(biz.get('photos', [])) if biz.get('photos') else 0}</span>
                            <small style="color: #666; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Photos</small>
                        </div>
                        <div style="flex:1; background: rgba(255, 149, 0, 0.08); padding: 15px 10px; border-radius: 20px; text-align: center; border: 1px solid rgba(255, 149, 0, 0.15);">
                            <span style="display: block; font-size: 1.3rem; font-weight: 800; color: #FF9500;">LOW</span>
                            <small style="color: #666; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">SEO</small>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # --- DIAGNOSTIC DIGITAL ---
                st.markdown("#### 📊 Diagnostic Digital")
                
                score = biz.get('potential_score', 0)
                score_val = f"{score}/10"
                if score >= 8:
                    label, color = "🔴 CRITIQUE", "#FF3B30"
                elif score >= 5:
                    label, color = "🟠 MODÉRÉ", "#FF9500"
                else:
                    label, color = "🟢 EXCELLENT", "#34C759"
                
                st.markdown(f"**Digital Gap Score : <span style='color:{color}'>{label}</span> ({score_val})**", unsafe_allow_html=True)
                
                # Progress bar elegantly with gradient
                st.markdown(f"""
                    <div style="width: 100%; background: #F2F2F7; border-radius: 10px; height: 14px; overflow: hidden; margin: 10px 0 25px 0;">
                        <div style="width: {score * 10}%; height: 100%; background: linear-gradient(90deg, #FF3B30, #FF9500); border-radius: 10px;"></div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.write("---")
                
                # --- OPPORTUNITÉ DE MARCHÉ ---
                st.markdown("#### ⚔️ Opportunité de Marché")
                
                # Extraction du leader local
                address = biz.get('address', '')
                city = "local"
                if ',' in address:
                    parts = [p.strip() for p in address.split(',')]
                    # Prends l'avant dernière partie (souvent la ville) ou la dernière si il n'y a que deux parties
                    if len(parts) >= 2:
                        city = parts[-2] if "France" not in parts[-1] and "Martinique" not in parts[-1] else parts[-1]
                        # Remove zip codes
                        import re
                        city = re.sub(r'\d+', '', city).strip()
                
                leader = get_neighborhood_stats(biz['id'], city)
                
                if leader:
                    l_name, l_score = leader
                    competitor_name = l_name
                    col_duel_1, col_vs, col_duel_2 = st.columns([1, 0.4, 1])
                    with col_duel_1:
                        st.markdown(f"<div style='text-align:center;'><small style='color:#86868B;'>Vous</small><br><b>{biz['name'][:12]}</b><br><h3 style='color:#FF3B30; margin:0;'>{score}</h3></div>", unsafe_allow_html=True)
                    with col_vs:
                        st.markdown("<h2 style='text-align:center; padding-top:15px; color:#86868B; opacity:0.3;'>VS</h2>", unsafe_allow_html=True)
                    with col_duel_2:
                        st.markdown(f"<div style='text-align:center;'><small style='color:#86868B;'>Leader</small><br><b>{l_name[:12]}</b><br><h3 style='color:#2ecc71; margin:0;'>{l_score}</h3></div>", unsafe_allow_html=True)
                    
                    capture_val = calculate_capture_math(biz['id'], city)
                    st.markdown(f"""
                        <div style="background: rgba(0, 113, 227, 0.05); border-left: 4px solid #0071E3; padding: 15px; border-radius: 15px; margin-top: 15px;">
                            <p style="margin:0; font-size: 0.7rem; color: #0071E3; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">🚀 Analyse d'opportunité</p>
                            <h3 style="margin:5px 0; color: #1D1D1F;">+{capture_val}% <span style="font-size: 0.8rem; font-weight: normal;">de capture de flux</span></h3>
                            <p style="margin:0; font-size: 0.75rem; color: #86868B;">En activant votre site mobile, vous interceptez les clients qui choisissent vos concurrents par défaut.</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"**Analyse Concurrentielle :** En cours de calcul...")
                    st.markdown(f"**Standard du Marché :** Pas de concurrent local direct détecté.")
                
                st.write("---")
                
                # --- ACTION RECOMMANDÉE ---
                st.markdown("#### ⚡ Action Recommandée")
                has_web = biz.get('website')
                insight = f"L'absence de site web coûte actuellement environ {int(score*2)} clients par semaine à {biz['name']} au profit de ses concurrents digitaux."
                if has_web:
                    insight = f"L'interface mobile de {biz['name']} n'est pas optimisée pour la conversion, causant un abandon de panier de {int(score*5)}% sur mobile."
                
                st.markdown(f"> \"{insight}\"")
                st.write("")
                
                # --- LE BOUTON MODIFIÉ AVEC TUNNEL DE RÉFLEXION ---
                if st.button("🚀 Générer Média & Démo Complete", key="gen_btn", use_container_width=True):
                    # --- PHASE DE REFLEXION VISUELLE ---
                    with fiche_sidebar.container():
                        st.markdown(f"### 🕵️‍♂️ Intelligence Artificielle - {biz['name']}")
                        st.write("Synchronisation des agents CrewAI...")
                        
                        status_text = st.empty()
                        bar = st.progress(0)
                        
                        steps = [
                            "Scan des avis Google Maps et analyse du sentiment...",
                            f"Identification des points faibles du concurrent '{competitor_name}'...",
                            "Génération du prompt artistique pour les visuels...",
                            "Calcul de la palette de couleurs optimale (UX/UI)...",
                            "Assemblage du template Bento Grid personnalisé..."
                        ]
                        
                        for i, step in enumerate(steps):
                            status_text.markdown(f"**Agent en action :** *{step}*")
                            bar.progress((i + 1) * 20)
                            time.sleep(1.2) 
                        
                        st.toast("Intelligence synchronisée !", icon="🧠")
                        
                        # LANCEMENT RÉEL DE L'API
                        requests.post(f"{API_URL}/orchestrate/{biz['id']}")
                        
                        st.success("✅ Démo générée avec succès ! Redirection...")
                        time.sleep(1)
                        
                        st.session_state.is_crew_running = True
                        st.session_state.current_project_id = biz['id']
                        st.rerun()
                
                # Stylisation du bouton pulse
                st.markdown("""
                    <style>
                    div[data-testid="stButton"] button[key="gen_btn"] {
                        background: linear-gradient(135deg, #FF3B30, #FF9500) !important;
                        box-shadow: 0 0 20px rgba(255, 59, 48, 0.4) !important;
                        animation: pulse 2s infinite;
                    }
                    </style>
                """, unsafe_allow_html=True)

                # --- PHONE PREVIEW ---
                if not has_web:
                    preview_img = "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500"
                    st.markdown(f"""
                        <div style="position: relative; width: 260px; height: 500px; margin: 30px auto; background: #1D1D1F; border-radius: 45px; border: 8px solid #3A3A3C; padding: 12px; box-shadow: 0 30px 60px rgba(0,0,0,0.3); overflow: hidden;">
                            <div style="position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 120px; height: 25px; background: #1D1D1F; border-bottom-left-radius: 15px; border-bottom-right-radius: 15px; z-index: 10;"></div>
                            <div style="width: 100%; height: 100%; background: white; border-radius: 30px; overflow: hidden; position: relative;">
                                <img src="{preview_img}" style="width: 100%; height: 100%; object-fit: cover; opacity: 0.9;">
                                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-15deg); background: rgba(255, 59, 48, 0.9); color: white; padding: 10px 20px; border-radius: 8px; font-weight: 900; font-size: 0.9rem; border: 2px solid white; box-shadow: 0 10px 20px rgba(0,0,0,0.2); z-index: 5; pointer-events: none; white-space: nowrap;">
                                    🔒 DÉMO PROTÉGÉE
                                </div>
                                <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 120px; background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); display: flex; flex-direction: column; justify-content: flex-end; padding: 20px; color: white;">
                                    <div style="font-size: 0.8rem; font-weight: 800;">{biz['name']}</div>
                                    <div style="font-size: 0.6rem; opacity: 0.8;">Interface Mobile exclusive</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.success(f"🌐 Site existant détecté : {has_web}")
                    st.markdown(f"[Accéder au site]({has_web})")
        else:
            st.markdown(f"""
                <div class="glass-card" style="text-align:center; padding: 80px 20px; border: 2px dashed rgba(0,0,0,0.05); background: transparent;">
                    <div style="font-size: 4rem; opacity: 0.2; margin-bottom: 20px; animation: float 6s ease-in-out infinite;">🛰️</div>
                    <h4 style="color: #8E8E93; font-weight: 700;">SYSTÈME LOCAL--PULSE PRÊT</h4>
                    <p style="color: #8E8E93; font-size: 0.85rem; max-width: 250px; margin: 0 auto;">Sélectionnez une cible sur la carte pour lancer le diagnostic digital en temps réel.</p>
                </div>
            """, unsafe_allow_html=True)

elif selected_menu == "Cockpit":
    st.title("🕵️‍♂️ Live Agent Cockpit")
    
    # --- LIGNE DE STATUT DES AGENTS (High-Tech Cards) ---
    st.markdown("#### 🤖 Statut des Agents CrewAI")
    c1, c2, c3 = st.columns(3)
    
    is_running = st.session_state.get('is_crew_running', False)
    scout_status = "🟢 ACTIVE" if is_running else "🔵 READY"
    designer_status = "🟡 WAITING" if is_running else "🔵 READY"
    closer_status = "⚪ STANDBY" if is_running else "🔵 READY"
    
    with c1:
        st.markdown(f"""
            <div class="glass-card" style="text-align:center; padding: 20px;">
                <div style="font-size: 2rem; margin-bottom: 10px;">🔍</div>
                <b style="font-size: 1.1rem;">Scout</b><br>
                <span style="color:{'#34C759' if is_running else '#0071E3'}; font-weight: 800;">{scout_status}</span>
                <p style="font-size: 0.7rem; color: #86868B; margin-top: 5px;">Scan GMB & Analyse Sentiment</p>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="glass-card" style="text-align:center; padding: 20px;">
                <div style="font-size: 2rem; margin-bottom: 10px;">🎨</div>
                <b style="font-size: 1.1rem;">Designer</b><br>
                <span style="color:#FF9500; font-weight: 800;">{designer_status}</span>
                <p style="font-size: 0.7rem; color: #86868B; margin-top: 5px;">UX/UI & Prompt Engineering</p>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="glass-card" style="text-align:center; padding: 20px;">
                <div style="font-size: 2rem; margin-bottom: 10px;">✍️</div>
                <b style="font-size: 1.1rem;">Closer</b><br>
                <span style="color:#8E8E93; font-weight: 800;">{closer_status}</span>
                <p style="font-size: 0.7rem; color: #86868B; margin-top: 5px;">Gmail Sync & Vercel Deploy</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- SYNCHRONISATION REDIS ---
    r = get_redis_conn()
    if r and st.session_state.get('current_project_id'):
        pid = st.session_state.current_project_id
        # Récupérer les logs
        raw_logs = r.lrange(f"logs:{pid}", 0, -1)
        if raw_logs:
            new_history = []
            for entry in raw_logs:
                try:
                    import json
                    data = json.loads(entry)
                    new_history.append({
                        "name": data.get("agent", "System"),
                        "text": data.get("message", ""),
                        "type": "agent" if data.get("agent") else "system"
                    })
                except: pass
            st.session_state.crew_history = new_history
            
        # Récupérer le statut global
        sys_status = r.get(f"status:{pid}")
        if sys_status:
            if "Prête" in sys_status:
                st.session_state.is_crew_running = False
            else:
                st.session_state.is_crew_running = True
                
        # Auto-refresh logic
        if st.session_state.get('is_crew_running'):
            time.sleep(2)
            st.rerun()

    # --- SESSION STATS SIDEBAR (Integrated) ---
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1: st.metric("Tokens Session", "12.4k", "+1.2k")
    with col_stat2: st.metric("Temps Moyen", "45s", "-4s")
    is_active = st.session_state.get('is_crew_running', False)
    with col_stat3: st.metric("Agents Actifs", "3/3" if is_active else "0/3", "Full")
    with col_stat4: st.metric("Dernier Deploy", "En cours..." if is_active else "Prêt", "Vercel")

    st.markdown("---")

    # Zone de Chat / Terminal
    chat_container = st.empty()
    
    if not st.session_state.get('crew_history'):
        # --- TERMINAL FANTÔME (Idle Mode) ---
        st.markdown("#### 📟 System Status")
        st.markdown(f"""
            <div style="background: #000; color: #34C759; padding: 20px; border-radius: 15px; font-family: 'Courier New', monospace; font-size: 0.8rem; opacity: 0.7; border: 1px solid #333; box-shadow: inset 0 0 10px rgba(0,255,0,0.1);">
                <span style="opacity: 0.5;">[{time.strftime('%H:%M:%S')}]</span> SYS_BOOT: OK<br>
                <span style="opacity: 0.5;">[{time.strftime('%H:%M:%S')}]</span> REDIS_CONN: ACTIVE<br>
                <span style="opacity: 0.5;">[{time.strftime('%H:%M:%S')}]</span> AGENT_CLUSTER: READY<br>
                <span style="opacity: 0.5;">[{time.strftime('%H:%M:%S')}]</span> <span style="animation: blink 1s infinite;">_</span> WAITING_FOR_MAP_TRIGGER...
            </div>
            <style>
                @keyframes blink {{ 0% {{ opacity: 0; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
            </style>
        """, unsafe_allow_html=True)
        
        st.info("🛰️ **Système en veille.** En attente d'une cible depuis le Cockpit Map.")
    else:
        # Zone de Chat existante pour les logs en direct
        with chat_container.container():
            for message in st.session_state.crew_history:
                name = message['name']
                text = message['text']
                is_system = message.get("type") != "agent"
                
                if is_system:
                    st.markdown(f"<div style='margin-bottom: 20px; text-align: center;'><span style='background: #F2F2F7; color: #8E8E93; padding: 6px 15px; border-radius: 50px; font-size: 0.8rem; font-weight: 600;'>{text}</span></div>", unsafe_allow_html=True)
                    continue

                agent_class = "header-scout" if "Scout" in name or "Éclaireur" in name else "header-designer" if "Designer" in name else "header-closer"
                icon = "🔍" if "Scout" in name or "Éclaireur" in name else "🎨" if "Designer" in name else "💰"
            
                try:
                    # Detection JSON
                    clean_text = text.strip()
                    if "```json" in clean_text:
                        clean_text = clean_text.split("```json")[1].split("```")[0].strip()
                    
                    if clean_text.startswith('{') or clean_text.startswith('['):
                        data = json.loads(clean_text)
                        if isinstance(data, dict) and "images" in data:
                            st.markdown(f"<div class='cockpit-bubble'><div class='cockpit-header {agent_class}'><span>{icon} {name}</span></div><div class='cockpit-body'>", unsafe_allow_html=True)
                            cols_img = st.columns(min(len(data["images"]), 2))
                            for idx, img_url in enumerate(data["images"]):
                                cols_img[idx % len(cols_img)].image(img_url, use_container_width=True)
                            st.markdown("</div></div>", unsafe_allow_html=True)
                            continue
                        elif isinstance(data, (dict, list)):
                            st.markdown(f"<div class='cockpit-bubble'><div class='cockpit-header {agent_class}'><span>{icon} {name}</span></div><div class='cockpit-body'>", unsafe_allow_html=True)
                            st.json(data)
                            st.markdown("</div></div>", unsafe_allow_html=True)
                            continue
                except: pass

                text_content = text.replace('\n', '<br>')
                st.markdown(f"<div class='cockpit-bubble'><div class='cockpit-header {agent_class}'><span>{icon} {name}</span><span style='margin-left: auto; opacity: 0.6; font-size: 0.7rem;'>LOG D'ACTIVITÉ</span></div><div class='cockpit-body'>{text_content}</div></div>", unsafe_allow_html=True)

elif selected_menu == "CRM":
    if 'selected_biz_crm' not in st.session_state:
        st.session_state.selected_biz_crm = None

    if st.session_state.selected_biz_crm:
        # --- VUE DÉTAILLÉE (DOSSIER) ---
        biz = st.session_state.selected_biz_crm
        
        col_back, col_title = st.columns([1, 4])
        with col_back:
            if st.button("← Retour Archives"):
                st.session_state.selected_biz_crm = None
                st.rerun()
        with col_title:
            st.title(f"📂 Dossier : {biz['name']}")
        
        st.markdown(f"**Adresse :** {biz.get('address', 'N/A')} | **Score :** {biz.get('potential_score', 0)}/10")
        
        tab_report, tab_photos, tab_mail, tab_preview = st.tabs(["📝 Rapport & Copy", "🖼️ Photos", "📧 Email Draft", "🌐 Site Web"])
        
        # Parse data
        data = biz.get('generated_copy')
        if data is None: data = {}
        if isinstance(data, str):
            try: data = json.loads(data)
            except: data = {}
        
        with tab_report:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔍 Rapport d'Investigation")
                st.info(data.get('report', 'Rapport non disponible.'))
            with col2:
                st.subheader("✍️ Stratégie Copywriting")
                st.success(data.get('copywriting', 'Copywriting non disponible.'))
        
        with tab_photos:
            st.subheader("📸 Galerie Photos (IA & Maps)")
            all_photos = []
            if data.get('ai_photos'):
                import re
                urls = re.findall(r'(https?://[^\s"\',]+)', str(data['ai_photos']))
                all_photos.extend([u.replace(']', '').replace(')', '') for u in urls])
            
            # Simulated or additional photos from Gmaps if available
            if not all_photos:
                st.warning("Aucune photo générée pour ce dossier.")
            else:
                cols = st.columns(3)
                for i, img in enumerate(all_photos):
                    cols[i % 3].image(img, use_container_width=True)
        
        with tab_mail:
            st.subheader("📧 Email de Prospection")
            email_text = data.get('email', 'Email non généré.')
            
            # Clean up logic
            if email_text and isinstance(email_text, str):
                import re
                marker_match = re.search(r'--- EMAIL CONTENT START ---([\s\S]*?)--- EMAIL CONTENT END ---', email_text)
                if marker_match:
                    email_text = marker_match.group(1).strip()
                else:
                    # Fallback cleanup
                    email_text = re.sub(r'\[.*\] \| \[.*\] \| \[.*\] \| \[.*\] \| \[.*\]', '', email_text).strip()
            
            st.text_area("Brouillon Gmail", value=email_text, height=400)
            st.button("Copier pour Gmail", key="copy_gmail_btn")
            
        with tab_preview:
            st.subheader("🌐 Aperçu de la Démo")
            v_url = data.get('vercel_url')
            if v_url:
                st.markdown(f"[Ouvrir le site dans un nouvel onglet]({v_url})")
                st.components.v1.iframe(v_url, height=600, scrolling=True)
            else:
                st.warning("Aucun site web déployé pour ce dossier.")

    else:
        # --- VUE TABLEAU DE BORD CRM ---
        st.title("� Pipeline de Sales Closing")
        businesses = get_businesses()
        
        if not businesses:
            st.info("Aucune campagne détectée. Scannez la carte pour commencer.")
        else:
            # --- 1. COMMAND CENTER (KPIs) ---
            st.markdown("#### 📊 Performance de la Session")
            k_col1, k_col2, k_col3, k_col4 = st.columns(4)
            
            nb_generated = len([b for b in businesses if b['status'] in ['completed', 'deployed']])
            nb_pending = len([b for b in businesses if b['status'] == 'completed'])
            nb_signed = len([b for b in businesses if b['status'] == 'signed'])
            
            k_col1.metric("Démos Créées", f"{nb_generated}", "+3")
            k_col2.metric("À Envoyer", f"{nb_pending}", "-2")
            k_col3.metric("Conversions", f"{nb_signed}", "+1")
            k_col4.metric("MRR Estimé", f"{nb_signed * 250}€", "+250€")
            
            st.markdown("---")

            # --- 2. FILTRES ET RECHERCHE ---
            f_col_search, f_col_status = st.columns([3, 1])
            search_query = f_col_search.text_input("🔍 Rechercher un prospect...", placeholder="Nom, adresse, ville...")
            status_filter = f_col_status.selectbox("� Filtrer par état", ["Tous", "ANALYSE...", "DÉMO PRÊTE", "SIGNÉ", "PERDU"])

            # Filtrage des données
            filtered_data = businesses
            if search_query:
                filtered_data = [b for b in filtered_data if search_query.lower() in b['name'].lower() or search_query.lower() in b.get('address', '').lower()]
            
            if status_filter != "Tous":
                s_map = {"ANALYSE...": "processing", "DÉMO PRÊTE": "completed", "SIGNÉ": "signed", "PERDU": "lost"}
                filtered_data = [b for b in filtered_data if b['status'] == s_map.get(status_filter)]

            # --- 3. LISTE TABULAIRE PREMIUM ---
            # Header
            st.markdown("""
                <div style='display: grid; grid-template-columns: 0.8fr 3fr 1.2fr 1.5fr 2fr 2.5fr; font-weight: 800; padding: 15px; background: rgba(0,0,0,0.02); border-radius: 12px; margin-bottom: 10px; font-size: 0.8rem; color: #86868B; text-transform: uppercase;'>
                    <div>Aperçu</div>
                    <div>Commerce</div>
                    <div>Score</div>
                    <div>🎨 Template</div>
                    <div>Statut Pipeline</div>
                    <div>Actions Rapides</div>
                </div>
            """, unsafe_allow_html=True)

            for biz in filtered_data:
                # Calcul des données de ligne
                score = biz.get('potential_score', 0)
                status = biz['status']
                template = biz.get('template', 'Default')
                
                # Render Row
                row_col1, row_col2, row_col3, row_col_tmpl, row_col4, row_col5 = st.columns([0.8, 3, 1.2, 1.5, 2, 2.5])
                
                with row_col1: # Thumbnail
                    preview_img = "https://images.unsplash.com/photo-1551218808-94e220e084d2?w=100"
                    st.markdown(f"""
                        <div style='width: 50px; height: 50px; border-radius: 12px; overflow: hidden; border: 1px solid #EEE;'>
                            <img src='{preview_img}' style='width:100%; height:100%; object-fit:cover;'>
                        </div>
                    """, unsafe_allow_html=True)
                
                with row_col2: # Info
                    st.markdown(f"<b>{biz['name']}</b><br><small style='color:#86868B;'>{biz.get('address', 'N/A')[:40]}...</small>", unsafe_allow_html=True)
                
                with row_col3: # Score
                    color = "#2ecc71" if score > 7 else "#FF9500" if score > 4 else "#FF3B30"
                    st.markdown(f"<span style='color:{color}; font-weight:bold;'>{score}/10</span>", unsafe_allow_html=True)
                
                with row_col_tmpl: # Template Badge
                    st.markdown(f"""<span style='background: #e7f3ff; color: #0071e3; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 800;'>{template}</span>""", unsafe_allow_html=True)
                
                with row_col4: # Status Selector
                    status_options = ["scanned", "processing", "completed", "signed", "lost"]
                    try:
                        idx = status_options.index(status)
                    except: idx = 0
                    
                    new_s = st.selectbox("Statut", status_options, index=idx, key=f"status_sel_{biz['id']}", label_visibility="collapsed")
                    if new_s != status:
                        if update_business_status(biz['id'], new_s):
                            st.toast(f"{biz['name']} mis à jour en {new_s}", icon="✅")
                            time.sleep(0.5)
                            st.rerun()

                with row_col5: # Actions
                    btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)
                    
                    # 👁️ View Site
                    if btn_c1.button("👁️", key=f"view_{biz['id']}", help="Aperçu Vercel"):
                        st.session_state.selected_biz_crm = biz
                        st.rerun()
                    
                    # 📧 Email
                    btn_c2.button("📧", key=f"mail_{biz['id']}", help="Brouillon Gmail")
                    
                    # 💬 WhatsApp (Simulated)
                    btn_c3.button("💬", key=f"wa_{biz['id']}", help="Contact WhatsApp")
                    
                    # ⚙️ Manage
                    if btn_c4.button("⚙️", key=f"mgr_{biz['id']}", help="Gérer Dossier"):
                        st.session_state.selected_biz_crm = biz
                        st.rerun()

                st.markdown("<hr style='margin:10px 0; opacity:0.1;'>", unsafe_allow_html=True)

elif selected_menu == "Settings":
    st.title("⚙️ Paramètres")
    st.markdown("<div class='glass-card'><h4>Compte Agence</h4><p>Version SaaS 1.0.4 - Premium</p></div>", unsafe_allow_html=True)

# FOOTER Branding
st.sidebar.markdown("---")
st.sidebar.markdown("""
    <div style='display: flex; align-items: center; gap: 10px; opacity: 0.6; padding: 10px;'>
        <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' width='24'>
        <span style='font-size: 0.8rem; font-weight: 600;'>Admin • Pro Plan</span>
    </div>
""", unsafe_allow_html=True)
