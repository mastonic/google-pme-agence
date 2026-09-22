# Local Pulse — moteur interne de prospection & croissance locale

Local Pulse est le **cockpit privé** utilisé par Ludovic pour identifier, qualifier, contacter et convertir des entreprises locales, puis piloter leur accompagnement digital après signature.

Le logiciel n'est pas commercialisé comme un SaaS pour d'autres agences : le client achète un **service géré**, pas l'outil.

## Flux principal

```
Google Maps / Apify
  → Opportunity Score
  → audit digital & site existant
  → enrichissement du décideur
  → démo personnalisée avant/après
  → séquence de prospection assistée
  → CRM & relances
  → détection des prospects chauds
  → conversion client & onboarding
  → suivi MRR / pilotage
```

## Fonctionnalités

- **Opportunity Score** : distingue la santé digitale de la valeur commerciale du prospect.
- **Audit web** : mobile, HTTPS, SEO local, CTA, formulaire, téléphone, WhatsApp, preuve sociale et autres signaux.
- **Enrichissement B2B** : Google Maps, Pappers et recherche web avec provenance et indice de confiance.
- **Démo personnalisée** : support commercial basé sur les écarts réellement observés.
- **Prospection assistée** : séquence J0/J2/J5/J10 avec validation humaine avant chaque contact.
- **CRM** : prochaines actions, relances, file « À faire aujourd'hui » et pipeline.
- **Hot leads** : vues de démo, clics d'intérêt et score de chaleur.
- **Onboarding client** : conversion prospect → client et checklist de livraison.
- **Pilotage** : opportunités fortes, prospects chauds, MRR actif, MRR pipeline et funnel.
- **Génération / déploiement** : production des actifs web et déploiement de la démo.

## Stack

- **Backend** : FastAPI, SQLAlchemy, PostgreSQL recommandé en production.
- **Frontend privé** : React / Vite.
- **Landing** : Next.js export statique.
- **Cartographie & données** : Google Maps / Apify.
- **Enrichissement** : Pappers / Perplexity selon configuration.
- **IA & médias** : modèles configurés dans l'environnement, Fal.ai selon usage.
- **Déploiement** : Cloud Run / Firebase Hosting / Vercel selon le composant.
- **Paiement** : Stripe.

## Sécurité

Le cockpit privé utilise Google Identity Services. Le frontend ne contient aucune whitelist admin : le backend vérifie le jeton Google et compare l'adresse à `ADMIN_EMAILS`, variable serveur uniquement.

Voir [SECURITY_AND_PRODUCTION.md](SECURITY_AND_PRODUCTION.md) avant tout déploiement de production.

## Installation locale

1. Copier `.env.example` vers `.env` et renseigner les variables nécessaires.
2. Pour le frontend, copier `frontend/.env.example` vers `frontend/.env`.
3. Installer les dépendances Python et JavaScript.
4. Démarrer les services avec les scripts du dépôt ou séparément.

SQLite reste disponible pour le développement local. En production, définir un `DATABASE_URL` persistant et `REQUIRE_PERSISTENT_DB=true`.

## Tarification

La table SQL `plans` est la **source de vérité**. Les interfaces récupèrent la grille active via `/plans`. Une modification de tarif doit être faite depuis la gestion des plans, pas dans plusieurs fichiers frontend.

## Validation continue

La CI vérifie :

- compilation backend Python ;
- tests unitaires ;
- build React/Vite ;
- build statique de la landing Next.js.

---

Local Pulse est conçu pour maximiser la qualité du pipeline et le temps commercial de l'opérateur, pas pour exposer la complexité technique au client final.
