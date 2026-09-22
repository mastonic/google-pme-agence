# Local Pulse — sécurité & mise en production

Local Pulse est désormais conçu comme un **cockpit privé** utilisé par l'opérateur pour vendre et délivrer un service aux entreprises locales. Le logiciel n'est pas exposé comme un SaaS à des agences tierces.

## 1. Authentification admin

Le frontend n'embarque plus de whitelist d'adresses email. L'utilisateur se connecte avec Google Identity Services, puis le backend vérifie le jeton Google et l'adresse autorisée.

Variables backend obligatoires en production :

- `GOOGLE_OAUTH_CLIENT_ID` : client OAuth Google Web.
- `ADMIN_EMAILS` : adresses autorisées, séparées par des virgules. Cette valeur reste uniquement côté serveur.
- `ADMIN_AUTH_REQUIRED=true`.

Variable frontend au build :

- `VITE_GOOGLE_CLIENT_ID` : le même client OAuth Web. Un OAuth client ID est public par conception ; les adresses admin, elles, ne doivent jamais être injectées dans le frontend.

Dans Google Cloud, ajoutez les domaines utilisés par Local Pulse dans les **origines JavaScript autorisées** du client OAuth.

Le backend est en mode fail-closed : si l'authentification est requise mais mal configurée, le cockpit renvoie une erreur de configuration au lieu de devenir public.

## 2. Routes publiques

Seules les routes nécessaires au prospect restent publiques : la page de démo, son aperçu, les assets nécessaires, le webhook Stripe et le catalogue public des offres. Les routes de scan, CRM, administration, génération, dashboard et enrichissement exigent un jeton admin valide.

## 3. Base de données persistante

SQLite reste pratique en local, mais ne doit pas être utilisé comme stockage de production sur une instance éphémère ou multi-instance.

Production :

```env
DATABASE_URL=postgresql://...
REQUIRE_PERSISTENT_DB=true
```

Avec `REQUIRE_PERSISTENT_DB=true`, l'application refuse de démarrer si `DATABASE_URL` pointe encore vers SQLite. Cela évite de perdre ou fragmenter prospects, événements de démo, CRM et onboarding entre plusieurs instances.

## 4. Tarification

La table SQL `plans` est la source de vérité. Le cockpit, le modal d'abonnement, l'administration, l'onboarding et la landing publique consomment le catalogue `/plans`.

Pour modifier un prix ou le contenu d'une offre, utilisez l'administration des plans ; ne modifiez pas plusieurs composants frontend.

## 5. Ordre de déploiement

1. Fournir la base PostgreSQL et `DATABASE_URL`.
2. Configurer le client OAuth Google et les origines autorisées.
3. Définir `ADMIN_EMAILS`, `GOOGLE_OAUTH_CLIENT_ID` et `ADMIN_AUTH_REQUIRED=true` côté backend.
4. Fournir `VITE_GOOGLE_CLIENT_ID` au build du frontend.
5. Déployer le backend Cloud Run.
6. Construire la landing et le frontend.
7. Déployer Firebase Hosting avec les rewrites de `firebase.json`.
8. Vérifier `/status` : `admin_auth_configured=true` et `database.persistent=true`.
9. Tester une connexion admin, un scan, une démo publique et un clic « Cette proposition m'intéresse ».

## 6. Secrets

Ne commitez jamais de clés API, tokens Stripe, clés Google Maps, mots de passe SQL ou liste réelle d'adresses admin. Les fichiers `.env.example` ne contiennent que des placeholders.
