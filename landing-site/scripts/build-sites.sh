#!/usr/bin/env bash
# Construit les trois exports (un par domaine) et contrôle leur SEO.
#   ../hosting-dist/fr     → pulse-locale-pme.fr (et pme-local-pulse.web.app)
#   ../hosting-dist/info   → pulse-locale-pme.info
#   ../hosting-dist/store  → pulse-locale-pme.store
# Le site principal reste aussi publié depuis landing-site/out (firebase.json, deploy.sh).
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf ../hosting-dist  # exports frais : les liens inter-domaines sont vérifiés sur ceux de ce build
for SITE in info store fr; do
  rm -rf .next out
  NEXT_PUBLIC_SITE=$SITE npm run build >/dev/null
  node scripts/check-seo.mjs out "$SITE"
  rm -rf "../hosting-dist/$SITE" && mkdir -p "../hosting-dist/$SITE" && cp -a out/. "../hosting-dist/$SITE/"
done
# Racine des domaines secondaires : servie par redirection Firebase, jamais par le HTML d'une autre route.
rm -f ../hosting-dist/info/index.html ../hosting-dist/store/index.html
echo "Exports prêts dans hosting-dist/ (out/ contient le build .fr)."
