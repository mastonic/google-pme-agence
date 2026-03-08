#!/bin/bash

# --- CONFIGURATION DYNAMIQUE ---
# Détecte automatiquement le dossier actuel
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_PATH="$PROJECT_DIR/venv"
PORT_FRONTEND=8501
PORT_BACKEND=8000
PORT_LANDING=3000

echo "🚀 Démarrage du déploiement Local-Pulse sur VPS..."
echo "📂 Dossier de travail : $PROJECT_DIR"

# 1. Mise à jour système et dépendances
echo "⚙️ Installation des dépendances système..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv redis-server nodejs npm sqlite3

# 2. Redis - Assurer le démarrage
echo "⚙️ Démarrage de Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server
echo "✅ Redis est actif."

# 3. Installation des dépendances Python
echo "🐍 Configuration de l'environnement Python..."
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
fi
source "$VENV_PATH/bin/activate"
pip install --upgrade pip
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements.txt"
    echo "✅ Dépendances Python installées."
else
    echo "⚠️ Attention : requirements.txt introuvable dans $PROJECT_DIR"
fi

# 4. Installation des dépendances Frontend & Landing
echo "📦 Installation des dépendances Node.js..."
cd "$PROJECT_DIR"

# Frontend (si présent)
if [ -d "frontend" ]; then
    cd frontend && npm install && cd ..
fi

# Landing (si présent)
if [ -d "landing" ]; then
    # Note: La landing page est statique, donc npm install n'est nécessaire que si elle a un package.json
    if [ -f "landing/package.json" ]; then
        cd landing && npm install && cd ..
    fi
fi
echo "✅ Dépendances Node.js traitées."

# 5. Gestion des processus avec PM2
if ! command -v pm2 &> /dev/null
then
    echo "⚠️ PM2 non trouvé, installation..."
    sudo npm install -g pm2
fi

# Arrêt des anciens processus
pm2 stop all || true
pm2 delete all || true

# Lancement des nouveaux processus
echo "🚀 Lancement des services avec PM2..."
cd "$PROJECT_DIR"

# Dashboard Streamlit
pm2 start "$VENV_PATH/bin/streamlit run app.py --server.port $PORT_FRONTEND --server.address 0.0.0.0 --server.headless true" --name "lp-frontend"

# Backend API
pm2 start "$VENV_PATH/bin/uvicorn backend.main:app --host 0.0.0.0 --port $PORT_BACKEND" --name "lp-backend"

# Orchestrateur
pm2 start "$VENV_PATH/bin/python agent_orchestrator.py" --name "lp-orchestrator"

# Landing Page statique
pm2 start "npx serve -s landing -l $PORT_LANDING" --name "lp-landing"

pm2 save
pm2 list

echo "🎉 Déploiement terminé avec succès !"
echo "🌐 Frontend (Dashboard) : http://VOTRE_IP:$PORT_FRONTEND"
echo "🌐 Backend (API) : http://VOTRE_IP:$PORT_BACKEND"
echo "🌐 Landing Page : http://VOTRE_IP:$PORT_LANDING"
