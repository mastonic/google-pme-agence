# Audit SEO / AEO / GEO — Pulse Locale PME

Date de l'audit : 8 novembre 2026 · Branche : `feat/seo-aeo-geo-yvelines-eure-et-loir`

Toutes les constatations « production » ci-dessous ont été relevées par requêtes HTTP réelles le 8 novembre 2026, avant toute modification.

## 1. Architecture constatée

| Élément | État constaté |
|---|---|
| Code | Next.js 14.2.20 (App Router, `output: 'export'`, `trailingSlash: true`) dans `landing-site/`, cockpit Vite dans `frontend/` copié dans `landing-site/out/app`, espace client statique `landing-site/public/espace/`. |
| Hébergement | Firebase Hosting, projet `pme-local-pulse`, 3 sites : `pme-local-pulse` (firebase.json, `landing-site/out`), `pulse-locale-info` et `pulse-locale-store` (firebase.multisite.json, `hosting-dist/info|store`). |
| API | Cloud Run `local-pulse-api` (europe-west1) via rewrites Firebase (identiques sur les 3 sites). |
| Déploiement | `deploy.sh` / `.github/workflows/deploy.yml` / Cloud Build pour le site principal ; `deploy-secondary-hosting.yml` (manuel) pour .info et .store. |
| Domaines | `pulse-locale-pme.fr` → 200 ; `pulse-locale-pme.com` → 301 vers .fr (chemin conservé) ; `.info` et `.store` → 302 racine vers `/info/` et `/store/` (correctif hydratation React #423). Certificats HTTPS actifs sur les 4 domaines. `www.pulse-locale-pme.fr` ne répond pas (À VALIDER côté DNS, non modifié). |

## 2. Problèmes identifiés (avant correction)

| # | Gravité | Problème | Preuve |
|---|---|---|---|
| P0-1 | Critique | La canonique de **pulse-locale-pme.fr** pointait vers `https://pme-local-pulse.web.app/` | `curl https://pulse-locale-pme.fr/` → `<link rel="canonical" href="https://pme-local-pulse.web.app/">` |
| P0-2 | Critique | **Contenu triplé** : les sites .info et .store servaient une copie de toutes les pages (accueil, boutique, guides, mentions…), chacune canonique sur elle-même | `https://pulse-locale-pme.info/store/` → canonique `.info/store/` ; `https://pulse-locale-pme.store/info/` → canonique `.store/info/` |
| P0-3 | Critique | Sitemaps identiques en contenu sur les 3 domaines, avec l'hôte du build (`web.app` sur le .fr) | `https://pulse-locale-pme.fr/sitemap.xml` → 24 `<loc>` en `pme-local-pulse.web.app` |
| P0-4 | Élevée | `lastmod` = date/heure du build pour toutes les URL | `<lastmod>2026-11-08T14:19:07.554Z</lastmod>` sur tout le sitemap .store |
| P0-5 | Élevée | robots.txt du .fr pointant vers le sitemap `web.app` | `Sitemap: https://pme-local-pulse.web.app/sitemap.xml` |
| P0-6 | Moyenne | Liens internes relatifs vers des sections d'autres domaines (ex. `/store/` depuis .info), et liens absolus codés en dur | Code : `SubShell.tsx` (constantes MAIN/STORE/INFO), `store/page.tsx`, `OrderButton.tsx` |
| P0-7 | Moyenne | Offres JSON-LD de la boutique pointant vers des pages produit inexistantes (`/store/pack-avis-50/`, `/store/audit-visibilite-ia/`) | `app/store/page.tsx` |
| P0-8 | Moyenne | `llms.txt` statique avec les URL `web.app` | `public/llms.txt` |
| P1-1 | Élevée | Aucune page ni mention des Yvelines / de l'Eure-et-Loir sur le site en production ; `areaServed` = France uniquement | Recherche « Yvelines » dans le HTML : 0 occurrence |
| P1-2 | Moyenne | Contenus de fond limités (1 actu), aucune page de référence SEO/AEO/GEO, aucune page méthode ni « qui sommes-nous » dédiée | Arborescence `app/` |
| P2-1 | Moyenne | Contenus signés par « l'équipe » sans personne identifiée (signal E-E-A-T faible) | Guides |
| P3-1 | Moyenne | LCP retardé par l'animation d'apparition du H1 (masqué jusqu'à l'exécution du JavaScript) | Mesure locale Chromium : LCP ≈ 1,1–1,25 s sur `/`, `/info/`, `/store/` contre ≈ 0,05 s sur les autres pages |
| — | Info | ESLint non configuré (`next lint` interactif) | `package.json` |

## 3. Concurrence locale (relevé du 8 novembre 2026)

Pages Yvelines de concurrents (Refonte Up, Web Ranker, SEO Supernova, Vincent Hego, SEO Yvelines…) : la plupart disposent d'une page locale dédiée, de `FAQPage`, `BreadcrumbList`, `areaServed` par ville, et souvent d'un `llms.txt`. Différenciateurs de Pulse Locale PME : réceptionniste IA, abonnement dès 49 € HT, tarifs publics, démo avant paiement. Faiblesses : pas d'ancrage physique local, pas encore d'avis ni d'études de cas publiés.

## 4. Points à valider (non tranchés dans le code)

- **Robots d'entraînement** (GPTBot, ClaudeBot, Google-Extended, Applebot-Extended) : autorisés comme avant. C'est une décision éditoriale et juridique (réutilisation des contenus pour l'entraînement), sans effet déclaré sur la visibilité en recherche. À VALIDER.
- **`www.pulse-locale-pme.fr`** : ne répond pas. Ajouter le sous-domaine dans Firebase (redirection vers l'apex) puis l'enregistrement DNS chez IONOS. À VALIDER, non modifié.
- **Mentions de prix publics de concurrents** dans deux articles (sources citées et datées, sans dénigrement) : relecture juridique conseillée au titre de la publicité comparative. À VALIDER.
- **Ancienne actu** `/info/actus/chatgpt-gemini-commerces-locaux/` : contient une affirmation non sourcée (« de plus en plus de clients… ») ; à sourcer ou reformuler. À VALIDER.
