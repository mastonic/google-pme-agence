#!/bin/bash
set -e

# ─── Configuration ────────────────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="europe-west1"
SERVICE_NAME="local-pulse-api"
FIREBASE_SITE="${FIREBASE_SITE:-}"

# ─── Couleurs ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
error()   { echo -e "${RED}❌ $1${NC}"; exit 1; }

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════╗"
echo "║     Local-Pulse — Déploiement Google Cloud       ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Pré-requis ───────────────────────────────────────────────────────────────
command -v gcloud   >/dev/null 2>&1 || error "gcloud CLI manquant. Installe-le : https://cloud.google.com/sdk/docs/install"
command -v firebase >/dev/null 2>&1 || error "firebase CLI manquant. Lance : npm install -g firebase-tools"
command -v node     >/dev/null 2>&1 || error "Node.js manquant"

# ─── Project ID ───────────────────────────────────────────────────────────────
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
fi
if [ -z "$PROJECT_ID" ]; then
    echo -n "Ton Firebase/GCP Project ID : "
    read PROJECT_ID
fi
info "Projet GCP : $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Mettre à jour .firebaserc
sed -i "s/YOUR_FIREBASE_PROJECT_ID/$PROJECT_ID/g" .firebaserc
info "Firebase projet configuré"

# ─── Variables d'environnement ────────────────────────────────────────────────
if [ ! -f .env ]; then
    error "Fichier .env introuvable. Copie .env.example et remplis les clés."
fi
source .env

REQUIRED_VARS=("ANTHROPIC_API_KEY" "GOOGLE_MAPS_API_KEY")
for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        error "$VAR est vide dans .env"
    fi
done

# ─── 1. Build Frontend ────────────────────────────────────────────────────────
info "Build du frontend React..."
cd frontend
npm install --silent
npm run build
cd ..
success "Frontend buildé → frontend/dist/"

# ─── 2. Activer les APIs Google Cloud nécessaires ─────────────────────────────
info "Activation des APIs Google Cloud..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    sqladmin.googleapis.com \
    firebase.googleapis.com \
    --project="$PROJECT_ID" --quiet
success "APIs activées"

# ─── 3. Stocker les secrets dans Secret Manager ───────────────────────────────
info "Création des secrets dans Secret Manager..."
store_secret() {
    local NAME=$1; local VALUE=$2
    if [ -n "$VALUE" ]; then
        echo -n "$VALUE" | gcloud secrets create "$NAME" --data-file=- --project="$PROJECT_ID" 2>/dev/null \
            || echo -n "$VALUE" | gcloud secrets versions add "$NAME" --data-file=- --project="$PROJECT_ID" 2>/dev/null
        echo "  → $NAME ✓"
    fi
}
store_secret "ANTHROPIC_API_KEY"    "$ANTHROPIC_API_KEY"
store_secret "GOOGLE_MAPS_API_KEY"  "$GOOGLE_MAPS_API_KEY"
[ -n "$APIFY_TOKEN" ]         && store_secret "APIFY_TOKEN"         "$APIFY_TOKEN"
[ -n "$VERCEL_API_TOKEN" ]    && store_secret "VERCEL_API_TOKEN"    "$VERCEL_API_TOKEN"
[ -n "$FAL_KEY" ]             && store_secret "FAL_KEY"             "$FAL_KEY"
success "Secrets stockés"

# ─── 4. Déployer le backend sur Cloud Run ─────────────────────────────────────
info "Déploiement du backend sur Cloud Run ($REGION)..."

# Construction des variables d'env pour Cloud Run
ENV_VARS="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}"
[ -n "$APIFY_TOKEN" ]        && ENV_VARS="${ENV_VARS},APIFY_TOKEN=${APIFY_TOKEN}"
[ -n "$VERCEL_API_TOKEN" ]   && ENV_VARS="${ENV_VARS},VERCEL_API_TOKEN=${VERCEL_API_TOKEN}"
[ -n "$FAL_KEY" ]            && ENV_VARS="${ENV_VARS},FAL_KEY=${FAL_KEY}"
[ -n "$DATABASE_URL" ]       && ENV_VARS="${ENV_VARS},DATABASE_URL=${DATABASE_URL}"

gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars "$ENV_VARS" \
    --project "$PROJECT_ID" \
    --quiet

BACKEND_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --format "value(status.url)" \
    --project "$PROJECT_ID")

success "Backend déployé : $BACKEND_URL"

# ─── 5. Mettre à jour firebase.json avec la bonne région ──────────────────────
sed -i "s/\"region\": \"europe-west1\"/\"region\": \"$REGION\"/g" firebase.json

# ─── 6. Déployer le frontend sur Firebase Hosting ─────────────────────────────
info "Déploiement du frontend sur Firebase Hosting..."
firebase deploy --only hosting --project "$PROJECT_ID" --non-interactive
success "Frontend déployé sur Firebase Hosting"

# ─── Résumé ───────────────────────────────────────────────────────────────────
FRONTEND_URL="https://${PROJECT_ID}.web.app"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              DÉPLOIEMENT TERMINÉ ✅               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  🌐 Application  : ${BLUE}${FRONTEND_URL}${NC}"
echo -e "  🔧 API backend  : ${BLUE}${BACKEND_URL}${NC}"
echo -e "  📊 Console GCP  : ${BLUE}https://console.cloud.google.com/run?project=${PROJECT_ID}${NC}"
echo ""
