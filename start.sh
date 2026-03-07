#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Lancement de la Suite Complète Local-Pulse SaaS ===${NC}"

# 0. Check Environment
if [ ! -f ".env" ]; then
    echo -e "${RED}Attention: Fichier .env manquant. Copie de .env.example...${NC}"
    cp .env.example .env
fi

# Stop all existing processes on relevant ports to prevent conflicts
echo "Nettoyage des anciens processus..."
pkill -f uvicorn 2>/dev/null
pkill -f streamlit 2>/dev/null
pkill -f "node.*vite" 2>/dev/null
pkill -f "agent_orchestrator" 2>/dev/null
pkill -f "npx serve" 2>/dev/null
sleep 2

# Reset logs
rm -f *.log
touch orchestrator.log backend.log streamlit.log vite.log landing.log

# Function to handle cleanup on exit
cleanup() {
    echo -e "\n${RED}Arrêt de tous les services...${NC}"
    # Use jobs -p to get PIDs of background processes
    PIDS=$(jobs -p)
    if [ ! -z "$PIDS" ]; then
        kill $PIDS 2>/dev/null
    fi
    exit
}

trap cleanup SIGINT SIGTERM EXIT

# Determine which venv to use
if [ -d "venv" ]; then
    VENV_PATH="venv"
elif [ -d ".venv" ]; then
    VENV_PATH=".venv"
else
    echo -e "${RED}Erreur: Dossier venv introuvable dans le root.${NC}"
    exit 1
fi

echo -e "${GREEN}Utilisation de l'environnement virtuel: $VENV_PATH${NC}"
source $VENV_PATH/bin/activate
export PYTHONPATH=$PYTHONPATH:.

# Check Redis
echo -n "Vérification de Redis (localhost:6379)... "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}PRÊT !${NC}"
else
    echo -e "${RED}ABSENT (Utilisation du mode FileQueue).${NC}"
    echo "Démarrage forcé de Redis-Server par sécurité (tentative)..."
    sudo systemctl start redis-server > /dev/null 2>&1
    sleep 1
fi

# Check Frontend Dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installation des dépendances Frontend...${NC}"
    cd frontend && npm install && cd ..
fi

# 1. Start Agent Orchestrator (Redis Worker)
echo -e "${BLUE}Démarrage de l'Orchestrateur CrewAI...${NC}"
python agent_orchestrator.py > orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!

# 2. Start Streamlit Dashboard
echo -e "${BLUE}Démarrage du Dashboard Streamlit (8501)...${NC}"
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > streamlit.log 2>&1 &
STREAMLIT_PID=$!

# 3. Start API Backend (FastAPI)
echo -e "${BLUE}Démarrage du Backend API (8000)...${NC}"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!

# 4. Start Frontend (Vite)
echo -e "${BLUE}Démarrage du Frontend Vite (5173)...${NC}"
cd frontend
npm run dev -- --host 0.0.0.0 > ../vite.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 5. Start Landing Page (3000)
echo -e "${BLUE}Démarrage de la Landing Page (3000)...${NC}"
npx serve -s landing -l 3000 > landing.log 2>&1 &
LANDING_PID=$!

echo -e "\n${GREEN}La suite Local-Pulse est opérationnelle !${NC}"
echo -e "${BLUE}----------------------------------------------------${NC}"
echo -e "🚀 Landing Page        : ${GREEN}http://localhost:3000${NC}"
echo -e "📡 Dashboard (React)   : ${GREEN}http://localhost:5173${NC}"
echo -e "🕵️ Cockpit (Streamlit) : ${GREEN}http://localhost:8501${NC}"
echo -e "⚙️  API Backend (Docs)  : ${GREEN}http://localhost:8000/docs${NC}"
echo -e "${BLUE}----------------------------------------------------${NC}"
echo -e "Logs disponibles dans : ${YELLOW}*.log${NC}"
echo -e "Appuyez sur ${RED}Ctrl+C${NC} pour tout arrêter.\n"

# Monitor orchestration activity
echo -e "${BLUE}Affichage des logs de l'Orchestrateur (Ctrl+C pour quitter)...${NC}"
tail -f orchestrator.log backend.log

