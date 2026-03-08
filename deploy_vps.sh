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
sudo apt-get install -y curl python3-pip python3-venv redis-server sqlite3 nginx ufw

# Configuration du Pare-feu (UFW)
echo "🛡️ Configuration du pare-feu..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 8501/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw --force enable

# Installation de Node.js v20 (LTS)
echo "📦 Mise à jour de Node.js vers v20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

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
    # Force reinstall of numpy for CPU compatibility
    pip install numpy==1.26.4
    pip install -r "$PROJECT_DIR/requirements.txt"
    echo "✅ Dépendances Python installées."
else
    echo "⚠️ Attention : requirements.txt introuvable."
fi

# 4. Configuration Nginx pour le port 80 (Landing Page)
echo "🌐 Configuration de Nginx pour le port 80..."
sudo rm /etc/nginx/sites-enabled/default || true
cat <<EOF | sudo tee /etc/nginx/sites-available/local-pulse
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/local-pulse /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# 5. Gestion des processus avec PM2
if ! command -v pm2 &> /dev/null
then
    echo "⚠️ PM2 non trouvé, installation..."
    sudo npm install -g pm2
fi

pm2 delete all || true

# Lancement des nouveaux processus
echo "🚀 Lancement des services avec PM2..."
cd "$PROJECT_DIR"
pm2 start "$VENV_PATH/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true" --name "lp-dashboard"
pm2 start "$VENV_PATH/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000" --name "lp-api"
pm2 start "$VENV_PATH/bin/python agent_orchestrator.py" --name "lp-orchestrator"
pm2 start "npx serve -s landing -l 3000" --name "lp-landing"

pm2 save
pm2 list

echo "🎉 Déploiement terminé avec succès !"
echo "🌐 Site Principal (Port 80) : http://VOTRE_IP/"
echo "⚙️  Dashboard (Direct)    : http://VOTRE_IP:8501"
