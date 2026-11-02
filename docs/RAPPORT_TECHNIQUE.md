# Local-Pulse / Pulse-PME — Rapport technique

Ce rapport décrit le fonctionnement réel de la plateforme, les défauts relevés dans le code,
la solution proposée pour couvrir **tous les artisans** que Google Maps peut détecter, et un audit
SEO / AEO / GEO. Chaque affirmation est étiquetée :

- **[Vérifié code]** — lu dans le code, avec référence `fichier:ligne`.
- **[Mesuré]** — calculé pendant l'audit (tests, calcul de volumes, HTML lu).
- **[À confirmer]** — plausible, mais demande un accès production ou une mesure live.

---

## 1. Résumé exécutif

| # | Constat | Impact | Statut |
|---|---------|--------|--------|
| 1 | La découverte utilise `searchNearby` : **20 résultats max par cercle, sans pagination**, triés par importance générale. Les artisans peu visibles n'apparaissent jamais. | Couverture artisans très insuffisante | [Vérifié code] |
| 2 | Le champ `query` des zones d'automatisation est **enregistré mais jamais utilisé** pour scanner. | Une zone scanne « tout et n'importe quoi » | [Vérifié code] |
| 3 | La clé API Google est **insérée dans les URLs de photos** stockées en base et intégrées aux démos publiques. | Fuite de clé probable | [Vérifié code] / [À confirmer] sur une démo live |
| 4 | Le proxy `/photo` valide l'hôte par **sous-chaîne** (`h in url`) : contournable. | Proxy ouvert / SSRF | [Vérifié code] |
| 5 | Les sites générés n'ont **ni title, ni meta description, ni JSON-LD, ni sitemap, ni robots.txt** (le prompt ne les impose pas). | SEO / GEO faibles des démos | [Vérifié code] |
| 6 | La landing : **FAQ non présente dans le HTML initial** (réponses rendues au clic), **soft 404** sur toute URL inconnue, **pas de robots.txt / sitemap / llms.txt**. | AEO / GEO / indexation | [Vérifié code] |
| 7 | La branche de templates Jinja est **morte** (`SECTOR_TEMPLATE = {}`, dossier `backend/templates` absent). | Dette, génération 100 % LLM | [Vérifié code] |
| 8 | Les artisans tombent dans le secteur **« generic »** (`SECTOR_TYPE_MAP` ne contient aucun métier artisan). | Prompts de design moins adaptés | [Vérifié code] |

**État d'implémentation (mis à jour)** : toutes les modifications proposées sont codées et testées (130 tests verts),
à l'exception de celles marquées « non fait » en section 6. Le scan artisans est branché derrière le drapeau
`ARTISAN_DISCOVERY_ENABLED` (désactivé par défaut). Rien n'est encore déployé : voir section 6.

---

## 2. État du dépôt

- Le **dépôt actif** est `google-pme-agence/` (git propre sur `main`, remote `mastonic/google-pme-agence`).
- Le dépôt racine `google-pme/` suit une **version plus ancienne** (`backend/main.py` : 1 602 lignes contre 2 623 dans le dépôt actif). **[Mesuré]**
  Risque : déployer la mauvaise copie. Décider d'un seul dépôt source (voir section 6, P2).
- Des dizaines de fichiers sont modifiés **non commités** dans le dépôt actif (`git status`). À committer ou écarter avant tout déploiement.
- Base locale `local_pulse.db` **vide (0 octet)** : impossible de mesurer la couverture réelle ici. La mesure doit se faire sur la base de production via l'API admin (`/businesses`).
- Tests : **107 tests**, tous verts dans un venv avec `backend/requirements.txt`. Sans dépendances, 5 suites échouent à l'import (environnement, pas code). **[Mesuré]**

---

## 3. Architecture

```
┌──────────────────────┐        ┌─────────────────────────────────────────────┐
│ Landing (Next.js)    │        │ Backend FastAPI  (Cloud Run "local-pulse-api")│
│ landing-site/        │        │ backend/main.py — ~100 routes               │
│ Firebase Hosting     │        │  ├─ services/  (scan, scoring, audit, …)    │
└──────────────────────┘        │  ├─ agents/manager.py  (LocalPulseManager)  │
┌──────────────────────┐  HTTP  │  ├─ models/database.py (SQLAlchemy)         │
│ Cockpit (React/Vite) │───────▶│  └─ APScheduler maison (asyncio)            │
│ frontend/            │ token  └───────────┬──────────────┬──────────────────┘
└──────────────────────┘ admin             │              │
                                ┌──────────▼───┐  ┌───────▼─────────────────────┐
                                │ Google Maps  │  │ LLM : Gemini 3.8 Flash →     │
                                │ Places (New) │  │ OpenAI GPT-5.6 Luna →        │
                                │ Geocoding    │  │ Mistral Large → Mistral Small│
                                └──────────────┘  └─────────────────────────────┘
                                ┌──────────────┐  ┌─────────────────────────────┐
                                │ Apify (repli)│  │ Fal (Flux) → Pexels → Unsplash│
                                └──────────────┘  └─────────────────────────────┘
                                ┌──────────────┐  ┌─────────────────────────────┐
                                │ Vercel       │  │ Stripe (abonnements, webhook)│
                                │ (démos)      │  │ Gmail (brouillons)           │
                                └──────────────┘  └─────────────────────────────┘
```

**Composants clés [Vérifié code]**

| Fichier | Rôle |
|---|---|
| `backend/main.py` | API FastAPI, orchestration, planificateurs, audit, CRM, Stripe, admin |
| `backend/agents/manager.py` (1 905 l.) | `LocalPulseManager` : crews design → prep → build (HTML) → email → deploy |
| `backend/services/google_maps.py` | Découverte (`searchNearby`), détails, géocodage (Google puis Nominatim) |
| `backend/services/apify_maps.py` | Repli de découverte (scraping Apify) |
| `backend/services/scoring.py` | Score santé digitale (0-100) et score d'opportunité (0-100) |
| `backend/services/website_audit.py` | Audit d'un site existant (technique, SEO, conversion, confiance) |
| `backend/services/monitoring.py` | Supervision quotidienne : SSL, avis Google, SEO basique |
| `backend/services/autopilot.py` | Pipeline nocturne : zones → scan → sélection → génération → déploiement |
| `backend/services/scheduler.py` | Planificateur quotidien sans dépendance (fenêtre aléatoire) |
| `backend/services/site_design_system.py` | Catégories de design (dont `artisan_home`) |
| `backend/services/agent_prompts_v2.py` | Prompts et validation JSON des agents (737 l.) |
| `backend/services/auth.py` | Jeton admin `ADMIN_API_TOKEN`, liste blanche `PUBLIC_ROUTES` |

**Modèle de données [Vérifié code]** (`backend/models/database.py`)
- `Business` : `id` = **place_id Google** (clé de dédoublonnage naturelle), coordonnées, notes, `photos` (JSON), `category` (JSON, types Google), scores, `website_audit`, `status` (`scanned → processing → pending_validation → completed`), `deployment_url`, champs CRM, onboarding client, abonnement.
- `AutomationZone` : nom, `query` (**inutilisé**), lat/lng, `radius`, `min_opportunity_score` (défaut 62), `max_sites_per_run` (défaut 3).
- `AutomationRun` : suivi d'un run nocturne (heartbeat, compteurs, erreurs).
- `Plan`, `DesignPreset`, `CrmActivity`, `AgentTeam`, `BusinessAgentTeam`, `AgentTeamRun`.

---

## 4. Flux de données de bout en bout

### 4.1 Scan manuel — `POST /scan?lat&lng&radius` (`backend/main.py:545`)
1. `GoogleMapsService.search_nearby_businesses` : `POST places:searchNearby`, `maxResultCount=20`, `excludedTypes` (transports, parcs, églises…), **sans `includedTypes`**. **[Vérifié code]** `google_maps.py:20-31`
2. Si erreur → repli Apify (`"commerce local"`, `maxCrawledPlaces=20`). **[Vérifié code]** `apify_maps.py:28-33`
3. Détails concurrents (`get_business_details`) pour les 20 premiers : site, téléphone, avis, photos. Les URLs photo contiennent la clé (voir 5.3).
4. Scores (`calculate_scores`) → upsert `Business` → tri par `opportunity_score`.
5. Audit auto non bloquant des 5 meilleurs ayant un site (`AUTO_AUDIT_TOP_N`).

### 4.2 Génération d'une démo — `POST /orchestrate/{id}` (`main.py:854`)
Statut `processing` → **design** (`run_design_crew`, JSON validé et réparé) → **préparation** (`run_prep_crew` : rapport, copywriting, photos) → **build** (`run_build_crew` : HTML streamé par le LLM, animations injectées) → **email** (`run_email_only`, sans artifacts, lien démo) → **déploiement Vercel** (`run_deploy_crew`, projet nommé d'après le commerce) → statut `pending_validation`.

Chaîne LLM avec cache des fournisseurs en échec pour toute la durée d'un run. **[Vérifié code]** `manager.py:11-21`

### 4.3 Autopilot nocturne — `run_autopilot` (`autopilot.py:263`)
Planifié à **02:00–02:20 Europe/Paris** (`AUTOPILOT_HOUR`, `AUTOPILOT_WINDOW_MINUTES`). **[Vérifié code]** `main.py:222-228`
Pour chaque zone activée : `scan_zone` → candidats `opportunity_score ≥ min_opportunity_score` (62), non générés, dédoublonnés entre zones → `max_sites_per_run` → `generate_and_deploy` → email. Les runs bloqués (heartbeat > 45 min) sont récupérés automatiquement.

### 4.4 Supervision — 08:00–08:45 Paris (`MONITOR_HOUR`)
`_supervise_all_sites` : SSL, nouveaux avis Google (delta de note), contrôle SEO basique (title, meta description, Open Graph, JSON-LD, H1, viewport, sitemap). **[Vérifié code]** `monitoring.py:55-100`

### 4.5 Scoring (`backend/services/scoring.py`)
- **Opportunité 0-100** : demande/réputation 30 (note + volume d'avis en log) · déficit digital 30 (`(100 − santé) × 0,30`, l.209) · contactabilité 15 · valeur du secteur 15 (listes `HIGH_VALUE_SECTORS` incluant `plumber`, `electrician`, `roofing_contractor`…) · confiance des données 10. **[Vérifié code]** l.167-227
- **Santé digitale 0-100** : présence web, avis, photos, téléphone, email, site (audit).

### 4.6 Client et abonnement
Lien d'onboarding tokenisé (`/client/onboarding/{token}`, public), portail Stripe, webhook `/webhook/stripe`, plans et fonctionnalités (`plans.py`).

---

## 5. Problèmes techniques détaillés

### 5.1 Découverte : pourquoi les artisans manquent [Vérifié code]
- `searchNearby` renvoie **au plus 20 lieux par cercle**, sans pagination ni filtre de métier. Une zone dense de Fort-de-France ou du Lamentin ne montre que les 20 établissements les plus « importants » du cercle : restaurants, supermarchés, hôtels. Les plombiers, couvreurs, serruriers sont éliminés avant d'être vus.
- Le rayon par défaut est 500 m (`/scan`) ou 1 000 m (zones). Un artisan situé à 1,5 km d'un centre de zone n'est jamais atteint.
- `zone.query` est enregistré (`main.py:2489`, `2502`) mais `scan_zone` n'envoie que `lat`, `lng`, `radius` (`autopilot.py:70-78`). **Aucun mot-clé métier n'est utilisé.**
- Le repli Apify interroge le terme générique `"commerce local"` (`apify_maps.py:28`) : même limitation.

### 5.2 Secteurs et prompts [Vérifié code]
- `SECTOR_TYPE_MAP` (`manager.py:220-245`) ne contient **aucun type artisan** → `_detect_sector` renvoie `generic` pour un plombier.
- `site_design_system.py:230-249` **sait** gérer les artisans (`artisan_home`), mais la préparation et le prompt HTML utilisent le secteur `generic`. Incohérence entre les deux systèmes.
- `SECTOR_TEMPLATE = {}` (`manager.py:1291`) : la branche `_render_from_template` ne peut jamais rendre. Le dossier `backend/templates/` n'existe pas. Code mort qui laisse croire à un rendu par gabarit.

### 5.3 Fuite probable de la clé Google [Vérifié code] / [À confirmer]
- `google_maps.py:111` : `photo_url = ".../media?...&key={self.api_key}"`. Cette URL est **stockée dans `Business.photos`**, renvoyée par l'API, puis `_proxify` (`manager.py`, `_generate_html_streaming`) l'encapsule dans `/photo?url=…` **dans le HTML public de la démo** (`/demo/{id}` est une route publique, `auth.py` `PUBLIC_ROUTES`).
- Conséquence probable : la clé `GOOGLE_MAPS_API_KEY` est lisible dans le source de chaque démo.
- **Action immédiate** : confirmer en ouvrant une démo et en cherchant `key=` dans le source ; si confirmé, **régénérer la clé** dans Google Cloud Console et restreindre-la (API Places uniquement, référents ou IP du serveur).
- Correctif : ne stocker que `name` (ressource Places) et construire l'URL média **côté serveur** au moment du proxy, avec la clé en en-tête `X-Goog-Api-Key`.

### 5.4 Proxy `/photo` contournable [Vérifié code]
`main.py:316-322` : `if not any(h in url for h in allowed)`. Une URL comme `https://attaquant.exemple/?places.googleapis.com` passe le filtre et le serveur la récupère.
Correctif : `urllib.parse.urlparse(url)`, puis comparer `hostname` à une liste exacte (et refuser les IP privées). Fermer le proxy si l'usage réel est limité aux photos Places.

### 5.5 Audit de site : petit défaut de précédence [Vérifié code]
`website_audit.py:96` : `"localbusiness" in lower or "restaurant" in lower and "application/ld+json" in lower`. Le `and` s'applique avant le `or` : le contrôle accepte n'importe quel JSON-LD contenant « restaurant ». Mieux vaut tester explicitement la présence d'un bloc `application/ld+json` puis son `@type`.

### 5.6 Coût et volume
- Un scan = 1 `searchNearby` + jusqu'à 20 `Place Details` (chacun facturé). **[Vérifié code]** `main.py:575-590`
- Les détails incluent `websiteUri` et `nationalPhoneNumber` qui relèvent de SKU plus coûteux : à vérifier avec la grille tarifaire.
- L'autopilot scanne **toutes les zones activées chaque nuit**, sans cache de couverture.

---

## 6. Mises à jour à mettre en place (priorisées)

### P0 — À faire avant tout nouveau scan à grande échelle
1. **Sécurité clé Google** : confirmer la fuite (5.3), régénérer et restreindre la clé si confirmée, retirer `key=` des URLs stockées (`google_maps.py:111`).
2. **Proxy `/photo`** : validation d'hôte exacte (5.4).
3. **Zones** : soit brancher `zone.query` (la solution artisans, section 7), soit masquer le champ dans l'UI pour ne pas tromper l'utilisateur.

### P1 — Couverture artisans (section 7)
4. Remplacer `searchNearby` par `discover_trades` (module livré) pour `/scan` et `scan_zone`.
5. Ajouter les types artisans à `SECTOR_TYPE_MAP` (`plumber`, `electrician`, `roofing_contractor`, `locksmith`, `painter`, `general_contractor`, `hvac_contractor`, `moving_company`) vers un secteur `artisan`.
6. Étalonner `min_opportunity_score` (62) sur une distribution réelle d'artisans avant de l'utiliser en automatique.

### P1 — SEO / AEO / GEO des démos (section 8)
7. Injecter le `<head>` **côté code** (pas dans le prompt LLM) : `lang="fr"`, title, meta description, canonical, Open Graph, balises géo, JSON-LD `LocalBusiness` (sous-type métier) avec données réelles uniquement.
8. Générer par démo `robots.txt`, `sitemap.xml`, `llms.txt` (déployés avec le site).
9. Ajouter `alt` obligatoire sur les images dans les règles du prompt et contrôler le résultat.
10. Remplacer le Tailwind CDN par un CSS compilé pour les démos (performance, Core Web Vitals).

### P1 — Landing (Pulse-PME)
11. FAQ : remplacer le rendu conditionnel par `<details>/<summary>` (contenu présent dans le HTML initial).
12. Firebase : supprimer ou restreindre le `"**" → /index.html` ; renvoyer un vrai 404 pour les URL inconnues.
13. Ajouter `robots.txt`, `sitemap.xml`, `llms.txt`, `<link rel="canonical">`, Open Graph, JSON-LD `Organization` + `SoftwareApplication`.
14. `noindex` sur `/admin` et `/app`.

### P2 — Maintenance
15. Choisir **un** dépôt source (voir section 2) et supprimer la copie périmée.
16. Supprimer la branche Jinja morte (`SECTOR_TEMPLATE`, `_render_from_template`) ou créer le dossier de templates.
17. Supprimer ou réécrire le repli Apify `"commerce local"`.
18. Committer ou écarter les modifications non commitées du dépôt actif.
19. Ajouter `requirements-dev` (pytest/unittest deps) pour que les 5 suites d'import passent hors Docker.

---

## 7. Solution : couvrir tous les artisans que Google Maps peut détecter

### 7.1 Ce qui est réellement possible
- **Google Business Profile (GBP)** est l'API de gestion des fiches **par leurs propriétaires**. Elle ne donne pas d'annuaire de fiches tierces : elle ne peut pas servir à inventorier les artisans.
- La source officielle pour inventorier les établissements est **Places API (New)**, en particulier **Text Search** (requête texte + zone rectangulaire, avec pagination).
- « Tous » ne peut pas être garanti à 100 % : Places n'expose pas forcément toutes les fiches (fiches très récentes, fermées, non indexées). La cible réaliste est **exhaustive au sens de l'API**, mesurée sur un échantillon.

### 7.2 Limites de l'API à connaître [Vérifié recherche / à confirmer]
- `searchNearby` (New) : 20 résultats max, sans pagination. **[Vérifié code + documentation]**
- `searchText` (New) : pagination par `nextPageToken`, **3 pages de 20 au maximum** utilisées ici (≈ 60 résultats par requête). Cette valeur n'a pas été confirmée sur la page officielle lors de l'audit : **à vérifier** avant production.
- `includedType` : un seul type à la fois. Mis en `includedType` **sans** `strictTypeFiltering`, il favorise le type sans exclure les autres : aucune perte de rappel.
- Types de lieux : `plumber`, `electrician`, `locksmith`, `painter`, `roofing_contractor`, `moving_company` apparaissent comme filtres utilisables. `general_contractor` et `hvac_contractor` sont **à vérifier** dans la table officielle « Place types (New) » ; le module ne les utilise qu'en indice.

### 7.3 Stratégie (implémentée dans `backend/services/artisan_discovery.py`)

| Étape | Mécanisme | Pourquoi |
|---|---|---|
| 1. Catalogue métiers | 26 métiers, 44 formulations (ex. « plombier », « dépannage plomberie ») | Un artisan ne se nomme pas toujours comme le catalogue Google |
| 2. Grille adaptative | Zone découpée en cellules de 10 km ; une cellule saturée (3 pages pleines) est subdivisée en 4, jusqu'à 4 niveaux | Ne rien perdre dans les zones denses, ne pas payer les zones vides |
| 3. Pagination | Jusqu'à 3 pages par requête, `pageToken` seul variable | Respect de la contrainte de paramètres identiques |
| 4. Dédoublonnage | Par `place_id` ; chaque lieu garde la liste des métiers qui l'ont trouvé | Un lieu trouvé par « plombier » et « dépannage » n'est compté qu'une fois |
| 5. Transport réel | `make_places_transport(api_key)` avec `FieldMask` minimal (id, nom, adresse, position, note, nombre d'avis, types, jeton) | Limiter les SKU facturés ; téléphone et site via Place Details, seulement pour les retenus |
| 6. Traçabilité | Compteur `incomplete_cells` (cellules encore saturées à profondeur max) | Savoir quand la couverture est incomplète |

**Vérifié par tests** : grille couvrante, quarts couvrant le parent, pagination jusqu'à disparition du jeton, subdivision et arrêt en profondeur max, dédoublonnage multi-métiers, places sans id ignorées, catalogue sans doublon, erreurs HTTP remontées. **107 tests verts.**

### 7.4 Volume et coût (ordre de grandeur) [Mesuré]
Zone de test approximative : Martinique (≈ 14,39–14,90 N ; −61,25 à −60,80 O ; **bornes à vérifier**).

| Taille de cellule initiale | Cellules | Recherches de base (44 formulations) |
|---|---:|---:|
| 2 km | 725 | 31 900 |
| 5 km | 120 | 5 280 |
| **10 km (recommandé)** | **30** | **1 320** |

Les subdivisions ne s'ajoutent qu'en zone saturée, et la pagination ajoute au plus 2 requêtes par recherche saturée. **Le coût réel se calcule avec la grille tarifaire Google Maps Platform pour la SKU Text Search** : ce rapport ne chiffre pas le prix en euros. Avant tout lancement complet, faire un **essai sur une commune** et compter les appels réels.

### 7.5 Câblage dans l'existant (réalisé derrière `ARTISAN_DISCOVERY_ENABLED=false`)
1. `scan_zone` (`autopilot.py:70`) et `/scan` (`main.py:545`) : remplacer l'appel `search_nearby_businesses` par :
   ```python
   from backend.services.artisan_discovery import discover_trades, grid, make_places_transport
   cells = grid(south, west, north, east, cell_km=10)
   result = discover_trades(make_places_transport(api_key), cells)
   # result["places"] : {place_id: {"place": {...}, "trades": [...]}}
   ```
2. Adapter le format : `id` → `place_id`, `displayName.text` → `name`, `formattedAddress` → `vicinity`, `location` → `geometry.location`, `userRatingCount` → `user_ratings_total`, `types` → `types`, et `trades` → champ `category` enrichi.
3. Persister la **couverture** (table `discovery_cells` : métier, requête, cellule, statut, nombre, date) pour reprendre un scan interrompu et ne pas repayer les cellules déjà couvertes. **Non fait.**
4. Pour `scan_zone`, `zone.query` filtre désormais les métiers (`select_trades`). **Fait.**

### 7.6 Validation de la couverture (à faire en production)
- Choisir **une commune** et établir une **liste de référence** de 50 artisans en vérifiant manuellement sur Google Maps (plombiers, électriciens, couvreurs, serruriers…).
- Lancer `discover_trades` sur cette commune et calculer le **taux de rappel** = artisans de la référence trouvés / artisans de la référence.
- Objectif de départ : rappel ≥ 90 % pour les métiers de la liste de référence. Ajuster les formulations et la taille de cellule en conséquence.
- Surveiller `incomplete_cells` : toute valeur non nulle signale une zone à découper plus finement.

### 7.7 Points de conformité (à valider juridiquement)
- **Conditions Google Maps Platform** : limites sur la conservation des contenus Places (hors `place_id`). Vérifier la durée de rétention autorisée avant de stocker le catalogue complet.
- **Apify / scraping de Google Maps** : contraire aux conditions de Google. À limiter ou retirer du flux de production.
- Données d'artisans : prospection B2B, à aligner sur le cadre RGPD appliqué par l'équipe (base légale, droit d'opposition).

---

## 8. Audit SEO / AEO / GEO

### 8.1 Landing Pulse-PME (`landing-site/`, source active)

| Contrôle | Résultat | Preuve | Statut |
|---|---|---|---|
| `<html lang="fr">` | Présent | `app/layout.tsx` | ✅ |
| `<title>` | « Pulse-PME — une solution de HoldMasto » | `layout.tsx` (metadata) | ✅ (à améliorer : mot-clé métier absent) |
| Meta description | Présente, 160 car. environ | `layout.tsx` | ✅ |
| `robots` meta index/follow | Présent | `layout.tsx` | ✅ |
| H1 unique | 1 H1 | `app/page.tsx:267` | ✅ |
| FAQ dans le HTML initial | **Non** : seule la question ouverte est rendue, les autres réponses n'existent qu'après clic | `app/page.tsx:445-448` | ❌ AEO |
| `robots.txt` | **Absent** (pas de dossier `public/`) | arborescence | ❌ |
| `sitemap.xml` | **Absent** | arborescence | ❌ |
| `llms.txt` | **Absent** | arborescence | ❌ GEO |
| `<link rel="canonical">` | **Absent** | grep `canonical` vide | ❌ |
| Open Graph / Twitter | **Absents** | grep `og:` vide | ❌ |
| JSON-LD (Organization, SoftwareApplication, FAQPage) | **Absent** | grep `ld+json` vide | ❌ GEO/AEO |
| `noindex` sur `/admin`, `/app` | **Absent** | grep `noindex` vide | ❌ |
| Routes inconnues | **Soft 404** : `**` → `/index.html` en 200 | `firebase.json` (2 copies) | ❌ |
| Build publié | `landing-site/out` racine = **version antérieure** (marque LocalPulse, `<title>` différent) | `landing-site/out/index.html` | ⚠️ |

**Note** : la build racine (marque « LocalPulse ») et la source active (« Pulse-PME ») divergent. La vérité de publication dépend du `firebase.json` et du workflow CI utilisés ; à trancher (section 6, P2).

### 8.2 Démos générées (`manager.py`, prompt HTML)

| Contrôle | Prescrit par le prompt ? | Mesure | Statut |
|---|---|---|---|
| `<title>` / meta description | **Non** (le prompt cite Tailwind, polices, AOS, CSS, nav) | À mesurer sur une démo live | ❌ probable |
| JSON-LD `LocalBusiness` | **Non** | `website_audit.py:96` le vérifie, donc un score faible est attendu | ❌ probable |
| `alt` des images | **Non** (seul `src` est imposé) | À mesurer | ⚠️ |
| `robots.txt`, `sitemap.xml`, `llms.txt` | **Non** | Aucun fichier produit par le déploiement (`backend/agents/tools.py:55` n'envoie qu'un `index.html`) | ❌ certain |
| Tailwind via CDN (`cdn.tailwindcss.com`) | **Oui** (imposé) | Script bloquant et non destiné à la production | ⚠️ performance |
| Animations AOS (`once:true`) | **Oui** | Contenu masqué avant animation si JS indisponible | ⚠️ |

**Mesure disponible sans développement** : l'audit existant `POST /businesses/{id}/audit-site` (et `monitoring`) donne un score par démo. Lancer-le sur un échantillon de démos déployées fournit la mesure réelle.

### 8.3 Ce qu'il faut ajouter aux démos (côté code, pas au prompt)
- **Head** : `lang="fr"`, `<title>` « Nom du commerce — Métier à Ville », meta description (≤ 160 car.), `<link rel="canonical">`, Open Graph, `geo.region` / `geo.position` / `ICBM` à partir des coordonnées réelles.
- **JSON-LD `LocalBusiness`** avec le sous-type adapté : `Plumber`, `Electrician`, `RoofingContractor`, `Locksmith`, `HousePainter`, `GeneralContractor`, `HVACBusiness`, `MovingCompany` (à vérifier sur schema.org). Champs : `name`, `address`, `telephone`, `url`, `areaServed`, `geo`, `openingHoursSpecification` **uniquement si connus**.
- **`aggregateRating`** : uniquement à partir des avis Google **réels** et de leur nombre exact. Ne jamais inventer de note : c'est contraire aux consignes de Google sur les données structurées.
- **JSON-LD `FAQPage`** à partir des questions réelles des slots de contenu. Note : Google restreint l'affichage des rich results FAQ depuis 2023, mais le balisage reste utile pour l'analyse par les moteurs IA.
- **`robots.txt`** (autoriser tout, pointer vers le sitemap) et **`sitemap.xml`** (une URL, date de génération).
- **`llms.txt`** : fichier de résumé pour les moteurs de réponse (nom, activité, zone, services, contact, FAQ). Convention émergente : son effet réel sur les moteurs IA n'est pas garanti, il coûte peu.
- **Contenu AEO** : titres formulés en questions fréquentes (« Combien coûte un dépannage plomberie à Fort-de-France ? »), réponses directes de 40 à 60 mots en tête de section.

### 8.4 Cohérence d'entité (GEO / local)
- Nom, adresse et téléphone **identiques** sur la fiche Google, la démo, l'email et l'annuaire (NAP). Aujourd'hui le téléphone vient de la fiche ; vérifier qu'il est normalisé dans les trois endroits.
- Lien explicite vers la fiche Google (`Place ID` ou URL Maps) depuis la démo.
- Les avis ne sont pas copiés en dur : ils sont cités avec leur source.

### 8.5 Synthèse du score
| Périmètre | Score qualitatif | Priorité |
|---|---|---|
| Landing | Bases correctes (lang, title, meta, H1) ; crawlabilité et AEO/GEO faibles | P1 |
| Démos | SEO/GEO quasi absents (pas de head, pas de schema, pas de sitemap) | P1 |
| Cockpit | Non concerné par l'indexation (à protéger, voir `noindex`) | P2 |

---

## 9. Plan de vérification (prochaines étapes)

1. **Aujourd'hui** : ouvrir une démo déployée, chercher `key=` dans le source (5.3) ; si présent, régénérer la clé.
2. **Mesure artisans** : prélever la base de production (`GET /businesses`) et compter les artisans par catégorie `category` ; comparer à la liste de référence d'une commune (7.6).
3. **Essai de coût** : un passage `discover_trades` sur **une** commune à 10 km, en comptant les appels et le coût sur la console Google.
4. **Audit SEO démos** : `POST /businesses/{id}/audit-site` sur 20 démos déployées ; consigner les scores et les `issues`.
5. **Landing** : Lighthouse SEO + test « rich results » de Google sur l'URL publique ; vérifier la présence des FAQ dans le HTML brut (`curl`).

---

## 10. Limites de ce rapport

- Aucun appel live aux API (Google, Apify, LLM, Vercel) n'a été effectué : la découverte est validée par tests unitaires avec transport factice.
- La base de production n'est pas accessible localement : la couverture réelle et le nombre de démos n'ont pas été mesurés.
- Les URL des démos déployées ne sont pas connues du dépôt local : l'audit des démos est décrit, pas mesuré.
- Les prix Google, la durée de rétention autorisée et le nombre maximal exact de résultats par requête doivent être confirmés sur les pages officielles.
- Aucune modification n'a été committée ni déployée. Le module `artisan_discovery.py` et ses tests sont ajoutés au dépôt de travail et ne sont pas encore appelés par l'application.

---

## 11. État d'implémentation (section 6)

| # | Action | Statut |
|---|---|---|
| 1 | Clé Google retirée des URLs de photos ; ajoutée côté serveur uniquement (`photo_proxy.py`) | Fait (code) — **rotation de la clé à faire par le propriétaire** |
| 2 | Proxy `/photo` : hôtes validés exactement, chemin Places contrôlé, clé envoyée seulement à Places | Fait (code) |
| 3 | `zone.query` filtre désormais les métiers | Fait (code) |
| 4 | `/scan` et `scan_zone` utilisent `discover_trades`, derrière `ARTISAN_DISCOVERY_ENABLED` | Fait (code), **désactivé par défaut** : coût à valider avant activation |
| 5 | Types artisans → secteur `artisan` (profil dédié) | Fait (code) |
| 6 | Étalonnage de `min_opportunity_score` | **Non fait** : nécessite les données de production |
| 7 | `<head>` SEO injecté côté code (title, description, OG, geo, JSON-LD sous-type métier) | Fait (code) |
| 8 | `robots.txt`, `sitemap.xml`, `llms.txt` par démo, déployés avec le site | Fait (code) ; URL du sitemap = `<projet>.vercel.app`, à vérifier |
| 9 | `alt` imposé dans le prompt | Fait (code) |
| 10 | Tailwind CDN remplacé par un CSS compilé | **Non fait** : nécessite un pipeline de build par démo |
| 11 | FAQ landing en `<details>` (contenu dans le HTML initial) | Fait (code, build vérifié) |
| 12 | Catch-all Firebase `**` supprimé | Fait (code) |
| 13 | `robots.txt`, `sitemap.xml`, `llms.txt`, canonical, Open Graph, JSON-LD landing | Fait (code, build vérifié) |
| 14 | `noindex` sur `/admin` et cockpit | Fait (code, build vérifié) |
| 15 | Un seul dépôt source | **Décision** : `google-pme-agence/` conservé. Le dépôt racine n'a pas été supprimé |
| 16 | Branche Jinja morte supprimée | Fait (code) |
| 17 | Repli Apify « commerce local » remplacé par les métiers artisans | Fait (code) |
| 18 | Modifications non commitées | **Non fait** : elles appartiennent à ton travail en cours (voir section 12) |
| 19 | `requirements-dev` | **Sans objet** : les dépendances sont déjà dans `requirements.txt` ; les échecs venaient d'un venv vide |

Corrections du rapport : le backend expose **69 routes** (pas ~100).

## 12. Déploiement — points bloquants

- Production (`local-pulse-api`, révision `a9f2111`) **n'a pas de secret `ADMIN_API_TOKEN`**. Le working tree contient l'auth admin globale (`auth.py`) : sans ce secret, toutes les routes protégées répondent 503.
- Le dépôt actif n'a **pas de `.env`** : `deploy.sh` s'arrête. Le `.env` racine ne contient pas `ADMIN_API_TOKEN`.
- Le working tree mélange ton travail en cours (12 fichiers modifiés, plusieurs non suivis) et les modifications ci-dessus. Déployer le working tree envoie les deux.
- La clé `GOOGLE_MAPS_API_KEY` actuelle doit être régénérée par le propriétaire de la console Google.
