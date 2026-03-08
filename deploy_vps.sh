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
# Force recreation if broken
if [ ! -f "$VENV_PATH/bin/python" ]; then
    echo "⚠️ venv incomplet ou absent, création..."
    rm -rf "$VENV_PATH"
    python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
pip install --upgrade pip
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "📦 Installation des paquets (cela peut prendre du temps)..."
    pip install numpy==1.26.4
    pip install -r "$PROJECT_DIR/requirements.txt"
    echo "✅ Dépendances Python installées."
else
    echo "⚠️ Erreur : requirements.txt introuvable."
    exit 1
fi

# 4. Configuration Nginx pour le port 80 (Landing & Dashboard)
echo "🌐 Configuration de Nginx (Port 80)..."
sudo rm /etc/nginx/sites-enabled/default || true
cat <<EOF | sudo tee /etc/nginx/sites-available/local-pulse
server {
    listen 80;
    server_name _;

    # Landing Page
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Dashboard Streamlit (Cockpit)
    location /cockpit {
        proxy_pass http://localhost:8501/cockpit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # Streamlit static & websocket support
    location /static {
        proxy_pass http://localhost:8501/static;
    }
    location /_stcore/stream {
        proxy_pass http://localhost:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$host;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
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

echo "🧹 Nettoyage PM2..."
pm2 kill || true

echo "🔍 Diagnostic : Vérification du venv..."
ls -l "$VENV_PATH/bin/python" || echo "❌ ERREUR : Python introuvable dans le venv !"

# Lancement des nouveaux processus
echo "🚀 Lancement des services avec PM2..."
cd "$PROJECT_DIR"

# Dashboard Streamlit
pm2 start app.py --name "lp-dashboard" --interpreter "$VENV_PATH/bin/python" -- run --server.port 8501 --server.address 0.0.0.0 --server.headless true --server.baseUrlPath /cockpit

# Backend API
pm2 start backend/main.py --name "lp-api" --interpreter "$VENV_PATH/bin/python" -- -m uvicorn

# Orchestrateur
pm2 start agent_orchestrator.py --name "lp-orchestrator" --interpreter "$VENV_PATH/bin/python"

# Landing Page statique
pm2 start npx --name "lp-landing" -- serve -s landing -l 3000

pm2 save
pm2 list

echo "🎉 Déploiement terminé !"
echo "🌐 Dashboard : http://VOTRE_IP/cockpit"
