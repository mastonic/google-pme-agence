# Audit complet Pulse Locale PME — 8 novembre 2026

Quatre audits menés en parallèle, en lecture seule, sur le dépôt (`main` @ 090870c) et sur les sites en production :
1. SEO / AEO / GEO en ligne (48 URL des 3 sitemaps crawlées).
2. Sécurité du code (120 routes énumérées, analyse statique, dépendances, historique git).
3. Tests de sécurité en ligne non destructifs (aucune donnée créée, aucun DoS, aucun brute force).
4. Fonctionnel, produit, conformité légale et exploitation.

Tests automatiques : `pytest tests` → **276 passed, 1 skipped**. Aucun secret trouvé dans les 470 commits.

> Limite : le bac à sable passe par un proxy TLS ; versions TLS et dates de certificats sont à revérifier depuis une machine normale (ex. https://www.ssllabs.com/ssltest/).

---

## 1. Synthèse

| Domaine | État |
|---|---|
| SEO technique en production | **Bon** : 48/48 URL en 200, canoniques correctes, un H1, JSON-LD valide, pas de duplication, redirections inter-domaines OK. 2 défauts réels. |
| Contrôle d'accès API | **Bon** : toutes les routes sensibles renvoient 401 sans jeton ; webhooks Stripe/Twilio rejettent les requêtes non signées ; jeton admin comparé en temps constant ; sessions client hachées. |
| Sécurité applicative | **À corriger** : 3 failles élevées (XSS menant au vol du jeton admin), plusieurs moyennes. |
| En-têtes de sécurité / CORS / docs API | **À corriger** : pas de CSP, pages framables, CORS trop ouvert, `/docs` public sur l'URL Cloud Run. |
| Fonctionnel | **Lacunes bloquantes pour vendre la réceptionniste à plusieurs clients** (un seul numéro Twilio, pas de facturation de l'option ni du dépassement). |
| Conformité légale | **À compléter** : CGV, TVA, RGPD, prospection, mention IA. |
| Exploitation | **À renforcer** : sauvegardes non documentées, pas de monitoring, une seule instance Cloud Run. |

---

## 2. Sécurité — constats

| # | Gravité | Constat | Preuve | Correction |
|---|---|---|---|---|
| S1 | **Élevée** | `/photo` (public) relaie n'importe quel fichier de `storage.googleapis.com`/`fal.media` en recopiant le `Content-Type` : un fichier HTML hébergé par un attaquant s'exécute sur `pulse-locale-pme.fr`, où le cockpit garde le jeton admin dans `localStorage`. | `backend/services/photo_proxy.py:8`, `backend/main.py:379-396` | N'accepter que des types image, `nosniff` + `CSP: sandbox`, buckets autorisés, pas de redirection, taille max. |
| S2 | **Élevée** | `/preview/{id}` (public) sert le HTML généré (scripts compris) sur l'origine principale ; les iframes du cockpit et de l'espace client ne sont pas `sandbox`. | `main.py:423-434`, `frontend/src/components/CampaignsView.jsx:577`, `public/espace/index.html:663` | Iframes `sandbox="allow-scripts"` (sans `allow-same-origin`), en-tête `CSP: sandbox allow-scripts` sur `/preview` et `/demo`, à terme domaine isolé. |
| S3 | **Élevée** | URL de logo / photos du profil client insérées sans échappement dans le HTML ; `PUT /client/onboarding/{token}` accepte tout JSON. XSS stocké vérifié localement. | `backend/agents/manager.py:465-518`, `main.py:869-882` | `html.escape(url, quote=True)` + schéma https ; schéma Pydantic sur l'onboarding. |
| S4 | Moyenne | `/demo/{id}` injecte le nom de la fiche Google sans échappement. | `main.py:2101-2185` | `html.escape`. |
| S5 | Moyenne | Jeton d'onboarding permanent placé dans l'URL de retour Stripe et échangeable contre une session client ; `/buy` public pour n'importe quel commerce. | `main.py:2017,2034`, `client_space_api.py:180-183` | Jeton à usage unique, court, lié à la session Stripe ; hacher le jeton. |
| S6 | Moyenne | Limite de débit de `/leads` contournable (premier `X-Forwarded-For`, mémoire non bornée). | `lead_api.py:146` | IP du proxy de confiance ; Turnstile/CAPTCHA. |
| S7 | Moyenne | `href={lead.referrer}` affiche le `Referer` brut d'une requête publique (`javascript:` possible). | `frontend/src/components/LeadsView.jsx:117`, `lead_api.py:162` | Ne garder que `http(s)://`. |
| S8 | Moyenne | `/photo` sans limite : coût Places API et saturation de l'unique instance. | `main.py:379` | Rate limit par IP. |
| S9 | Moyenne | CORS `allow_origins=["*"]` + `allow_credentials=True` : origine arbitraire reflétée (testé en ligne). Impact atténué (auth par en-têtes). | `main.py:56-62` | Liste blanche des 3 domaines, `allow_credentials=False`. |
| S10 | Moyenne | `/docs`, `/redoc`, `/openapi.json` publics sur l'URL Cloud Run (106 chemins dont `/admin/*`). | `main.py:54`, test en ligne | Désactiver en production. |
| S11 | Moyenne | Aucun en-tête de sécurité (CSP, `X-Frame-Options`, `nosniff`, `Referrer-Policy`) ; `/app` et `/espace` framables ; HSTS absent sur .info/.store/.com et l'API. | tests en ligne | Section `headers` de `firebase.json` + middleware FastAPI. |
| S12 | Faible | Anti-SSRF du webhook client purement textuel (`0x7f.0.0.1`, `*.nip.io` acceptés). | `services/integrations.py:179-190` | Résolution DNS + refus des IP privées (réutiliser `_ensure_public_host`). |
| S13 | Faible | État OAuth Google non lié à la session ni à usage unique. | `integrations.py:107-126` | Nonce serveur lié à la session. |
| S14 | Faible | Signature du WebSocket Twilio rejouable ; `/client/track` et `/buy` sans limite. | `receptionist_api.py:424-433` | Vérifier le `callSid`, rate limit. |
| S15 | Faible | Dépendances : `requirements.txt` non épinglé ; npm audit : next 14.2.20 (critique, peu exploitable en export statique), axios, form-data. | `npm audit` | Épingler (`pip-compile`), `npm audit fix`, monter Next. |
| S16 | Faible | Chromium headless en `--no-sandbox` sur du HTML non fiable. | `services/showreel.py` | Sandbox ou blocage des plages internes. |

**Vérifié OK** : 120 routes, aucune route sensible publique ; jeton admin `compare_digest`, fail-closed ; sessions client aléatoires, hachées, expirantes ; signatures Twilio (toutes routes + WebSocket) et Stripe ; pas d'injection SQL ni de commande ; échappement systématique dans l'espace client ; médias client validés par signature d'octets ; jetons Google chiffrés (Fernet) ; Dockerfile non root ; `.env` et `.db` non versionnés ; fichiers sensibles en 404 en ligne ; http → https partout.

---

## 3. SEO en production — constats

| # | Gravité | Constat | Correction |
|---|---|---|---|
| E1 | **Élevée** | Pied de page de l'accueil : liens `/zones/yvelines/` et `/zones/eure-et-loir/` en **404** (`landing-site/app/page.tsx:471-472`). | Pointer vers les pages piliers. |
| E2 | **Élevée** | « Audit visibilité IA · **79 €** » au lieu de 99 € HT (`info/actus/chatgpt-gemini-commerces-locaux/page.tsx:79`). | Corriger. |
| E3 | Moyenne | `www.pulse-locale-pme.info/.store/.com` : erreur de certificat ; `www.pulse-locale-pme.fr` n'existe pas. | Ajouter les www dans Firebase (301 vers l'apex) ou supprimer ces DNS. |
| E4 | Moyenne | `check-seo.mjs` ne vérifie pas l'existence de la page cible d'un lien (d'où E1). | Ajouter le contrôle. |
| E5 | Faible | 2 chaînes de 2 redirections via le `.com` ; prix des kits sans HT ; 16 titles > 60 car. ; 2 descriptions > 160 ; `/zones/` peu maillée ; double balise robots sur la 404. | Corrections mineures. |

**Vérifié OK** : 48 URL en 200, canonique = URL, og:url, `lang=fr`, un H1, JSON-LD parsable, aucun doublon de title/description/H1, pages villes similaires à ~20 % seulement, Brotli, cache immuable des assets, robots/llms.txt corrects, prix cohérents (hors E2), TXT de validation Google présents sur .fr/.info/.store.

---

## 4. Fonctionnel — constats

| # | Priorité | Constat | Preuve |
|---|---|---|---|
| F1 | **P0** | Réceptionniste **mono-client** : un seul `TWILIO_PHONE_NUMBER` global ; WhatsApp en sandbox. | `receptionist_api.py:489,515` |
| F2 | **P0** | Option réceptionniste 39 € HT et Pack Connecté **non payables** (activation admin seulement) ; **dépassement au-delà de 100 appels et règle des 5 min non implémentés** alors qu'ils figurent dans les CGV ; pas de plafond d'appels. | `receptionist_api.py:241,570`, `plans.py:191-194` |
| F3 | **P0** | Webhook Stripe : `invoice.payment_failed` et `customer.subscription.updated` non traités ; résiliation ne coupe pas les services ; webhook non testé. | `main.py:2048-2098` |
| F4 | **P0** | Bouton « Obtenir ce site » de la page démo → `/pricing` en **404**. | `main.py:2179` |
| F5 | P1 | OAuth Google : `calendar.events` exige la vérification Google ; en mode Test les jetons expirent au bout de 7 jours. | `docs/RECEPTIONNISTE_IA.md` |
| F6 | P1 | Un compte en mode test (`trialing`) ne peut plus payer. | `client_space_api.py:568` |
| F7 | P2 | Email non exigé côté API (seulement côté formulaire). | `lead_api.py:104-108` |
| F8 | P1 | Sites clients générés : numéro WhatsApp fictif de secours, pas de page mentions/confidentialité, Maps et polices sans consentement. | `agents/manager.py:1381,1418` |

**Vérifié OK** : prix cohérents backend/affichage/API ; checkout mensuel/annuel ; activation par webhook ; essai 30 jours / 60 appels ; Pack Connecté (OAuth chiffré, créneaux réels) ; mode test admin ; aucun traceur ni cookie tiers sur les sites publics.

---

## 5. Conformité légale

| Manque | Risque | Action |
|---|---|---|
| Mentions légales : pas de téléphone éditeur ni hébergeur, pas de n° de TVA ; hébergeurs incomplets (Cloud Run, Vercel). | LCEN | Compléter. |
| CGV : pas de droit applicable / juridiction, pénalités de retard et **indemnité de 40 €** (L441-10 C. com.), limitation de responsabilité, réversibilité, révision de prix, conditions des produits physiques ; **pas d'acceptation des CGV au paiement**. | CGV inopposables, amende | Compléter + `consent_collection` Stripe. |
| TVA : Stripe facture le HT sans taxe ; « 0,83 € HT = 1 € TTC » suppose 20 % alors que le siège est en Martinique (8,5 %, règles DOM). | Erreur fiscale | **Expert-comptable**, Stripe Tax, mentions de facture ; facturation électronique (émission 09/2027). |
| RGPD : bases légales et durées non précisées, droits incomplets, sous-traitants manquants (Vercel, Apify, Pappers, Perplexity, fal, SMTP), aucune purge, pas de DPA pour la réceptionniste ; vérifier le palier payant Gemini. | Art. 13, 14, 28, 44 | Réécrire la politique, DPA, purge automatique. |
| AI Act art. 50 : un message d'accueil personnalisé peut **supprimer la mention IA**. | Non-conformité | Préfixe IA obligatoire non supprimable. |
| Prospection B2B (démo non sollicitée) : email sans identité, source, ni lien d'opposition ; « désinscription en un clic » promise mais inexistante. | CNIL, art. 14 | Pied d'email + liste d'opposition. |
| « Pack 50 avis… 5 étoiles » | Pratique trompeuse, règles Google | Reformuler. |
| Boutique : kits sans HT/TTC ; pas de « réservé aux professionnels ». | Droit conso (rétractation) | Afficher HT, SIRET, mention pros. |
| Données/photos Google Places dans les démos publiques. | CGU Google Maps Platform | Attributions, durée de vie des démos. |

---

## 6. Exploitation

- **Base de données** : Postgres requis en production mais fournisseur, sauvegardes et restauration non documentés. → PITR + test de restauration.
- **Monitoring** : emails SMTP uniquement ; `/status` ne vérifie pas la base. → sonde de disponibilité, suivi d'erreurs.
- **Cloud Run** : `max-instances=1` (point unique de défaillance), CPU bridé hors requêtes alors que 3 planificateurs internes tournent. → `--no-cpu-throttling` ou Cloud Scheduler ; plus d'une instance avec rate limit partagé.
- **Impayés et dépassements** : non gérés (voir F2, F3).

---

## 7. Ce qu'il reste à faire, par priorité

### P0 — sécurité et blocants
| Action | Effort | Qui |
|---|---|---|
| Corriger S1, S2, S3 (XSS → vol du jeton admin) + S4, S7 | 1 j | dev |
| En-têtes de sécurité, CORS restreint, `/docs` fermé (S9, S10, S11) | 0,5 j | dev |
| Jeton d'onboarding hors URL Stripe (S5) | 0,5 j | dev |
| Corriger E1, E2, F4 (liens 404, prix 79 €, CTA démo) + contrôle E4 | 2 h | dev |
| Mention IA non supprimable (AI Act) | 30 min | dev |
| Réceptionniste multi-clients (1 numéro Twilio par client, WhatsApp Business) | 3-5 j | dev + Twilio |
| Facturation option réceptionniste / Pack Connecté / dépassement **ou** retrait des clauses CGV | 3-4 j (retrait : 0,5 j) | décision + dev |
| Webhooks Stripe impayés / changement / résiliation effective + tests | 1,5 j | dev |
| TVA et factures | — | **expert-comptable** |
| CGV complétées + acceptation au paiement | 1 j | dev + **juriste** |
| Prospection : pied d'email + opposition | 1 j | dev |

### P1
Politique RGPD + DPA + purge (2 j) · vérification Google OAuth (dossier + délai Google) · sauvegardes et monitoring (1 j) · Cloud Run (1 j) · sites clients conformes (1,5 j) · mentions légales (1 h, infos à fournir) · boutique HT/pros (0,5 j) · www des domaines (30 min, console Firebase) · S6, S8, S12-S14 rate limits et SSRF (1 j).

### P2
Email obligatoire côté API · polices locales espace client · attributions Google Places · dépendances épinglées et mises à jour · tests `/buy`, portail, webhook · facturation électronique 2027.

### Actions qui dépendent de toi
- Fournir : téléphone, n° de TVA, avis de l'expert-comptable sur la TVA (Martinique / métropole).
- Décider : implémenter la facturation à l'appel ou la retirer des CGV ; achat d'un numéro Twilio par client.
- Console Firebase : ajouter les domaines `www`.
- Console Google Cloud : vérifier le palier payant Gemini, lancer la vérification OAuth.
- Vérifier les sauvegardes de la base Postgres et la facture Cloud Run.
- Relecture juridique des CGV, RGPD et prospection.
