# Plan d'implémentation SEO / AEO / GEO

| Priorité | Lot | Statut |
|---|---|---|
| P0 | Configuration de domaine centrale (`app/seo/domains.ts`) : propriétaire de chaque chemin, canoniques absolues, liens inter-domaines | Fait |
| P0 | Redirections 301 des pages « étrangères » sur chaque site Firebase (chemin conservé), racine 302 des sites secondaires conservée (#423) | Fait |
| P0 | Sitemap et robots.txt par domaine, `lastmod` réels (registre `app/seo/pages.ts`) | Fait |
| P0 | `llms.txt` généré au build depuis les registres, URL canoniques | Fait |
| P0 | Script de contrôle `scripts/check-seo.mjs` + tests `tests/test_seo_domains.py` + intégration CI | Fait |
| P1 | Accueil repositionné 78 / 28 (title, H1, intro, zones, `areaServed`) | Fait |
| P1 | Pages piliers `/agence-seo-local-yvelines/` et `/agence-seo-local-eure-et-loir/` (12 sections, contenus distincts) + 10 pages villes | Fait |
| P1 | 6 articles de fond sur .info + index `/info/articles/` | Fait |
| P1 | Page de référence `/info/seo-aeo-geo/`, page `/methode/`, page `/a-propos/` | Fait |
| P1 | FAQ commerciale et locale (8 questions) affichée en HTML | Fait |
| P2 | Auteur identifié (Ludovic Rigah), Organization enrichie (adresse légale, areaServed, founder) | Fait |
| P2 | Composants témoignages / études de cas (vides tant qu'aucune donnée réelle) | Fait |
| P2 | Plan de citations locales, protocole de suivi GEO, guide Search Console / Bing | Fait (documents) |
| P3 | LCP : H1 et chapô des héros affichés sans attendre le JavaScript | Fait |
| P3 | ESLint configuré (`next/core-web-vitals`) | Fait |

## Déploiement (après validation explicite)

1. Fusionner la PR dans `main`.
2. Site principal : `./deploy.sh` (ou workflow `deploy.yml`) — build `.fr` par défaut, `firebase.json` contient désormais les redirections `/info/**` → .info et `/store/**` → .store.
3. Sites secondaires : lancer le workflow manuel « Deploy dedicated info and store hosting ».
4. Vérifier : `curl -I https://pulse-locale-pme.fr/info/` → 301 ; canonique de l'accueil = `https://pulse-locale-pme.fr/` ; sitemaps des 3 domaines.
5. Soumettre les sitemaps (voir `SEARCH_CONSOLE_SETUP.md`).

## Ordre de déploiement conseillé

Déployer **d'abord** les sites .info et .store (ils doivent servir les pages vers lesquelles le .fr va rediriger), **puis** le .fr.
