#!/bin/bash
set -e
cd "$(dirname "$0")"  # chemins relatifs à la racine du dépôt

# Ne jamais activer `set -x` ici : les valeurs de secrets ne doivent pas apparaître dans les logs.

# ─── Configuration ────────────────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="europe-west1"
SERVICE_NAME="local-pulse-api"
FIREBASE_SITE="${FIREBASE_SITE:-}"

# Secrets : nom du secret dans Secret Manager = nom de la variable d'env exposée au conteneur.
# Ils ne sont jamais passés en clair via --set-env-vars (visible dans la config de révision Cloud Run).
SECRET_NAMES=(
    GOOGLE_MAPS_API_KEY
    GOOGLE_API_KEY
    GEMINI_API_KEY
    MISTRAL_API_KEY
    OPENAI_API_KEY
    ANTHROPIC_API_KEY
    FAL_API_KEY
    PAPPERS_API_KEY
    PERPLEXITY_API_KEY
    PEXELS_API_KEY
    APIFY_TOKEN
    VERCEL_API_TOKEN
    STRIPE_SECRET_KEY
    STRIPE_WEBHOOK_SECRET
    DATABASE_URL
    ADMIN_API_TOKEN
    SMTP_HOST
    SMTP_PORT
    SMTP_USER
    SMTP_PASSWORD
    SMTP_FROM
    TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN
    TWILIO_PHONE_NUMBER
    TWILIO_WHATSAPP_NUMBER
    INTEGRATIONS_KEY
    GOOGLE_OAUTH_CLIENT_ID
    GOOGLE_OAUTH_CLIENT_SECRET
    ALERT_EMAIL
)

# ─── Couleurs ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
error()   { echo -e "${RED}❌ $1${NC}"; exit 1; }

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════╗"
echo "║   Pulse Locale PME — Déploiement complet         ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Options ──────────────────────────────────────────────────────────────────
# ./deploy.sh              → tout : backend Cloud Run + 3 sites (.fr, .info, .store)
# ./deploy.sh --sites-only → uniquement les 3 sites Firebase (plus rapide, backend inchangé)
SITES_ONLY=false
for ARG in "$@"; do
    case "$ARG" in
        --sites-only) SITES_ONLY=true ;;
        -h|--help) sed -n '/^# \.\/deploy.sh/p' "$0"; exit 0 ;;
        *) echo "Option inconnue : $ARG (utilise --sites-only ou rien)"; exit 1 ;;
    esac
done

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
if [ -f .env ]; then
    set -a; source .env; set +a
    info ".env chargé"
else
    warn "Fichier .env introuvable : seuls les secrets déjà présents dans Secret Manager seront utilisés."
    warn "Pour en ajouter/modifier : cp .env.example .env, remplis les clés, puis relance ./deploy.sh"
fi

# Une variable obligatoire doit être soit dans .env, soit déjà dans Secret Manager.
REQUIRED_VARS=("GOOGLE_MAPS_API_KEY")
for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ] && ! gcloud secrets describe "$VAR" --project="$PROJECT_ID" >/dev/null 2>&1; then
        error "$VAR manquant : ni dans .env, ni dans Secret Manager. Lance : cp .env.example .env puis remplis $VAR."
    fi
done

# ─── 1. Build des 3 sites ─────────────────────────────────────────────────────
# scripts/build-sites.sh construit et contrôle (SEO) un export par domaine :
#   hosting-dist/info  → pulse-locale-pme.info   (firebase.multisite.json)
#   hosting-dist/store → pulse-locale-pme.store  (firebase.multisite.json)
#   landing-site/out   → pulse-locale-pme.fr     (firebase.json), construit en dernier
# Ordre important : le cockpit React (Vite) est buildé APRÈS, dans landing-site/out/app.
info "Build des sites .info, .store et .fr (Next.js + contrôle SEO)..."
(cd landing-site && npm ci --silent && bash scripts/build-sites.sh) || error "Build ou contrôle SEO en échec : rien n'a été déployé."
info "Build du cockpit React (Vite → landing-site/out/app/)..."
(cd frontend && npm install --silent && npm run build)
for F in landing-site/out/index.html landing-site/out/app/index.html landing-site/out/espace/index.html \
         hosting-dist/info/info/index.html hosting-dist/store/store/index.html; do
    [ -f "$F" ] || error "Build incomplet : $F manquant, déploiement Firebase annulé."
done
success "Sites buildés : .fr (landing + /app + /espace), .info, .store"

if [ "$SITES_ONLY" = true ]; then
    warn "--sites-only : backend Cloud Run et secrets non modifiés."
else

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
# Idempotent : crée le secret s'il n'existe pas, n'ajoute une version que si la valeur a changé.
info "Synchronisation des secrets dans Secret Manager..."
store_secret() {
    local NAME=$1 VALUE=$2
    if ! gcloud secrets describe "$NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
        gcloud secrets create "$NAME" --replication-policy=automatic --project="$PROJECT_ID" --quiet >/dev/null
    fi
    if [ "$(gcloud secrets versions access latest --secret="$NAME" --project="$PROJECT_ID" 2>/dev/null)" != "$VALUE" ]; then
        printf '%s' "$VALUE" | gcloud secrets versions add "$NAME" --data-file=- --project="$PROJECT_ID" --quiet >/dev/null
        echo "  → $NAME : nouvelle version ajoutée"
    else
        echo "  → $NAME : inchangé"
    fi
}

for SECRET in "${SECRET_NAMES[@]}"; do
    # Seuls les secrets présents dans .env sont (re)synchronisés ; les autres doivent déjà exister.
    if [ -n "${!SECRET}" ]; then
        store_secret "$SECRET" "${!SECRET}"
    fi
done
success "Secrets synchronisés"

# Le compte de service d'exécution Cloud Run doit pouvoir lire les secrets montés.
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
RUNTIME_SA="${RUNTIME_SA:-${PROJECT_NUMBER}-compute@developer.gserviceaccount.com}"

# ─── 4. Déployer le backend sur Cloud Run ─────────────────────────────────────
info "Déploiement du backend sur Cloud Run ($REGION)..."

# Secrets montés via --set-secrets (ENV=SECRET:version), uniquement ceux qui existent dans Secret Manager.
SECRET_SPECS=()
for SECRET in "${SECRET_NAMES[@]}"; do
    if gcloud secrets describe "$SECRET" --project="$PROJECT_ID" >/dev/null 2>&1; then
        gcloud secrets add-iam-policy-binding "$SECRET" \
            --member="serviceAccount:${RUNTIME_SA}" \
            --role="roles/secretmanager.secretAccessor" \
            --project="$PROJECT_ID" --quiet >/dev/null
        SECRET_SPECS+=("${SECRET}=${SECRET}:latest")
    fi
done
# tools.py copie FAL_API_KEY vers FAL_KEY, et manager.py lit FAL_KEY directement : on expose les deux.
if gcloud secrets describe FAL_API_KEY --project="$PROJECT_ID" >/dev/null 2>&1; then
    SECRET_SPECS+=("FAL_KEY=FAL_API_KEY:latest")
fi
SECRETS_ARG=$(IFS=,; echo "${SECRET_SPECS[*]}")

# Variables non sensibles uniquement (configuration).
ENV_VAR_SPECS=("SCORING_ENGINE=opportunity_v1")
[ -n "$PERPLEXITY_MODEL" ] && ENV_VAR_SPECS+=("PERPLEXITY_MODEL=${PERPLEXITY_MODEL}")
[ -n "$MONITOR_TZ" ]       && ENV_VAR_SPECS+=("MONITOR_TZ=${MONITOR_TZ}")
[ -n "$FRONTEND_URL" ]     && ENV_VAR_SPECS+=("FRONTEND_URL=${FRONTEND_URL}")
ENV_VARS_ARG=$(IFS=,; echo "${ENV_VAR_SPECS[*]}")

gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 1 \
    --max-instances 1 \
    --set-env-vars "$ENV_VARS_ARG" \
    --set-secrets "$SECRETS_ARG" \
    --project "$PROJECT_ID" \
    --quiet

BACKEND_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --format "value(status.url)" \
    --project "$PROJECT_ID")

success "Backend déployé : $BACKEND_URL"
fi

# ─── 5. Mettre à jour firebase.json avec la bonne région ──────────────────────
sed -i "s/\"region\": \"europe-west1\"/\"region\": \"$REGION\"/g" firebase.json firebase.multisite.json

# ─── 6. Déployer les 3 sites sur Firebase Hosting ─────────────────────────────
# D'abord .info et .store : le .fr redirige (301) vers leurs pages, elles doivent déjà être en ligne.
info "Déploiement de pulse-locale-pme.info et pulse-locale-pme.store..."
firebase deploy --config firebase.multisite.json --only hosting --project "$PROJECT_ID" --non-interactive
success ".info et .store déployés"
info "Déploiement de pulse-locale-pme.fr..."
firebase deploy --only hosting --project "$PROJECT_ID" --non-interactive
success ".fr déployé"

# ─── 7. Vérification rapide en ligne ──────────────────────────────────────────
check_url() {
    local URL=$1 EXPECTED=$2 CODE
    CODE=$(curl -s -o /dev/null -m 20 -w '%{http_code}' "$URL" || echo "000")
    if [ "$CODE" = "$EXPECTED" ]; then echo "  ✓ $URL → $CODE"; else warn "$URL → $CODE (attendu $EXPECTED)"; fi
}
if command -v curl >/dev/null 2>&1; then
    info "Vérification des domaines..."
    check_url https://pulse-locale-pme.fr/ 200
    check_url https://pulse-locale-pme.fr/info/ 301
    check_url https://pulse-locale-pme.info/info/ 200
    check_url https://pulse-locale-pme.store/store/ 200
    check_url https://pulse-locale-pme.fr/status 200
fi

# ─── Résumé ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              DÉPLOIEMENT TERMINÉ ✅               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  🌐 Site         : ${BLUE}https://pulse-locale-pme.fr${NC}"
echo -e "  📚 Ressources   : ${BLUE}https://pulse-locale-pme.info${NC}"
echo -e "  🛒 Boutique     : ${BLUE}https://pulse-locale-pme.store${NC}"
echo -e "  🧭 Cockpit      : ${BLUE}https://pulse-locale-pme.fr/app/${NC}"
[ -n "$BACKEND_URL" ] && echo -e "  🔧 API backend  : ${BLUE}${BACKEND_URL}${NC}"
echo -e "  📊 Console GCP  : ${BLUE}https://console.cloud.google.com/run?project=${PROJECT_ID}${NC}"
echo ""
