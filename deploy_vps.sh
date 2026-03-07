#!/抄/bash

# --- CONFIGURATION ---
PROJECT_DIR="/home/rigahludovic/google-pme"
VENV_PATH="$PROJECT_DIR/venv"
PORT_FRONTEND=8501
PORT_BACKEND=8000
PORT_LANDING=3000

echo "🚀 Démarrage du déploiement Local-Pulse sur VPS..."

# 1. Mise à jour système et dépendances
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv redis-server nodejs npm sqlite3

# 2. Redis - Assurer le démarrage
sudo system_state redis-server start
echo "✅ Redis est actif."

# 3. Installation des dépendances Python
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
fi
source "$VENV_PATH/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"
echo "✅ Dépendances Python installées."

# 4. Installation des dépendances Frontend & Landing
cd "$PROJECT_DIR"
npm install
cd landing && npm install
echo "✅ Dépendances Node.js installées."

# 5. Migration DB (si nécessaire)
# sqlite3 local_pulse.db < schema.sql (si existant)
echo "✅ Base de données prête."

# 6. Gestion des processus avec PM2 (Recommandé)
if ! command -v pm2 &> /dev/null
then
    echo "⚠️ PM2 non trouvé, installation..."
    sudo npm install -g pm2
fi

# Arrêt des anciens processus
pm2 stop all || true

# Lancement des nouveaux processus
pm2 start "venv/bin/streamlit run app.py --server.port $PORT_FRONTEND --server.address 0.0.0.0 --server.headless true" --name "lp-frontend"
pm2 start "venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port $PORT_BACKEND --reload" --name "lp-backend"
pm2 start "python agent_orchestrator.py" --name "lp-orchestrator"
pm2 start "npx serve -s landing -l $PORT_LANDING" --name "lp-landing"

pm2 save
pm2 list

echo "🎉 Déploiement terminé avec succès !"
echo "🌐 Frontend (Dashboard) : http://VOTRE_IP:$PORT_FRONTEND"
echo "🌐 Backend (API) : http://VOTRE_IP:$PORT_BACKEND"
echo "🌐 Landing Page : http://VOTRE_IP:$PORT_LANDING"
