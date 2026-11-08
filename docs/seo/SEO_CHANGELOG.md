# Journal des modifications SEO

## 2026-11-08 — Branche feat/seo-aeo-geo-yvelines-eure-et-loir

| Problème | Fichier(s) | Correction | Justification | Test | Résultat | Risque résiduel |
|---|---|---|---|---|---|---|
| Canonique .fr vers web.app | `app/seo/domains.ts`, `app/seo/seo.ts`, `app/layout.tsx` | Canonique absolue = domaine propriétaire du chemin ; build .fr par défaut | Consolidation des URL (Google, doc « consolidate duplicate URLs ») | `check-seo.mjs out fr` | ✓ 17 pages | Aucun |
| Copies des pages sur .info/.store | `firebase.json`, `firebase.multisite.json` | 301 des sections étrangères vers leur domaine, chemin conservé ; racine 302 conservée (#423) | Éviter le contenu dupliqué | `tests/test_seo_domains.py`, émulateur Firebase Hosting | ✓ 4 tests, redirections vérifiées sur les 3 sites | Les redirections ne seront actives qu'après déploiement des 3 sites |
| Sitemaps identiques / lastmod = build | `app/sitemap.ts`, `app/seo/pages.ts` | Sitemap filtré par domaine, dates de contenu réelles | Sitemaps exacts | `check-seo.mjs` | ✓ fr 17 / info 29 / store 2 URL | Mettre à jour les dates lors des modifications de contenu |
| robots.txt | `app/robots.ts` | Sitemap du domaine, robots de recherche et d'entraînement distingués | Usage différent des robots | `check-seo.mjs` | ✓ | Choix « entraînement autorisé » À VALIDER |
| Liens inter-domaines | `siteHref` + 17 fichiers | Liens relatifs si même domaine, absolus sinon | Pas de lien vers une page redirigée | `check-seo.mjs` (liens) | ✓ | — |
| Offres JSON-LD vers pages inexistantes | `app/store/page.tsx` | URL vers `/store/#packs` | Données structurées exactes | Build | ✓ | — |
| llms.txt obsolète | `app/llms.txt/route.ts` (remplace `public/llms.txt`) | Généré depuis les registres | Une seule source | Build | ✓ | — |
| Absence 78 / 28 | `app/page.tsx`, `app/layout.tsx`, `app/local/hubs.ts`, `app/components/LocalHub.tsx`, `app/agence-seo-local-*` | Accueil repositionné, 2 pages piliers | Requêtes locales | `check-seo.mjs`, captures | ✓ | — |
| Contenus de fond | `app/info/articles/**`, `app/info/seo-aeo-geo/`, `app/components/ArticleLayout.tsx` | 6 articles + page de référence | AEO / GEO | `check-seo.mjs`, lint | ✓ | Prix concurrents à revérifier tous les 6 mois |
| Confiance | `app/a-propos/`, `app/methode/`, `app/components/Proof.tsx`, `Byline` | Pages entreprise / méthode, auteur, composants de preuves vides | E-E-A-T, transparence | Build | ✓ | Ajouter des preuves réelles |
| FAQ | `app/seo/faq-data.ts` | 8 questions commerciales et locales en HTML | Réponses directes | Build | ✓ | — |
| LCP héros | `app/page.tsx`, `app/components/SubShell.tsx` | H1 et chapô sans animation d'apparition | LCP retardé jusqu'au JS | Mesure Chromium locale | ≈1,2 s → ≈0,1 s (local, non représentatif du terrain) | Mesurer en conditions réelles (CrUX / PageSpeed) |
| Lint absent | `.eslintrc.json`, `package.json` | ESLint `next/core-web-vitals` | Qualité | `npm run lint` | ✓ 0 erreur | — |
