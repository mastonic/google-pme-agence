# 🕵️‍♂️ Local-Pulse : Agence de Prospection SaaS "Elite"

Local-Pulse est une plateforme SaaS d'automatisation de prospection B2B utilisant **CrewAI** pour orchestrer une équipe d'agents intelligents. Elle aide les agences marketing à scanner des commerces locaux, analyser leur "Digital Gap" et générer des démos (Landing Pages) ultra-personnalisées en moins de 60 secondes.

## 🚀 Fonctionnalités Clés

- **Scout Agent** : Scan profond Google Maps (Avis, Photos propriétaire/clients, Catégories).
- **Designer Agent** : Routage de template automatique par métier (Restaurant, Pharmacie, Garage) et palettes de couleurs ciblées.
- **Copywriter Agent** : Storytelling persuasif et email outreach personnalisé.
- **Ingénieur Agent** : Génération de Landing Page (HTML/Tailwind) et déploiement immédiat sur **Vercel**.
- **Motion Director** : après la génération du site, une présentation vidéo motion design est rendue (Pillow + ffmpeg), avec voix off française (Google Cloud Text-to-Speech, voix féminine Chirp 3 HD) calée scène par scène et musique générée qui baisse sous la voix. Elle est publiée avec la démo (`presentation.mp4`). Sur Cloud Run, aucune clé : il suffit d'activer l'API « Cloud Text-to-Speech » dans le projet (sinon : vidéo + musique, sans voix). En local : `GOOGLE_TTS_API_KEY`. `GOOGLE_TTS_VOICE` (facultatif, `fr-FR-Chirp3-HD-Aoede` par défaut).
- **Dashboard Elite** : Suivi des KPIs (MRR, Démos), Pipeline CRM et cockpit de contrôle des agents en temps réel.

## 🛠️ Stack Technique

- **Backend** : FastAPI, SQLAlchemy (SQLite), Redis.
- **Frontend** : Streamlit (Dashboard Elite) & React/Vite.
- **AI Engine** : CrewAI, OpenAI GPT-4o-mini, Fal.ai (Flux.1), LangChain.
- **Infrastructure** : Vercel (Hosting démos), Gmail API (Outreach).

## 📦 Installation & Déploiement

### Déploiement Local
1. Clonez le dépôt.
2. Configurez votre fichier `.env` (voir `.env.example`).
3. Lancez les services :
   ```bash
   ./start.sh
   ```

### Déploiement VPS
Utilisez le script automatisé fourni :
```bash
chmod +x deploy_vps.sh
./deploy_vps.sh
```

## 📞 Réceptionniste IA (module complémentaire)

Répond aux appels que le gérant ne peut pas prendre (chantier, client en cours…), qualifie la demande
(urgence, motif, adresse, créneau souhaité, nom, téléphone) selon le métier, puis envoie un résumé
au gérant par WhatsApp, SMS et/ou email (canaux configurables, défaut WhatsApp + SMS). Gratuit 30 jours à l'activation, puis payant ; après l'essai, le numéro bascule
en simple messagerie (enregistrement + notification, sans IA). L'IA n'utilise que les données réelles
du commerce : jamais de prix ni de disponibilité inventés.

### 1. Acheter un numéro Twilio français
1. Console Twilio → *Phone Numbers → Buy a number* → pays **France**, capacité **Voice** (+ SMS si
   possible ; sinon les SMS partent d'un numéro/expéditeur autorisé par Twilio pour la France).
2. Twilio exige un *Regulatory Bundle* (justificatif d'adresse / Kbis) pour les numéros FR.

### 2. Brancher les webhooks sur le numéro (un numéro par commerce)
Dans la configuration du numéro, section *Voice* :
- **A call comes in** → Webhook `POST https://<API>/receptionist/voice/<business_id>`
- **Call status changes** → `POST https://<API>/receptionist/voice/<business_id>/status`

Si l'API est derrière un proxy qui modifie l'URL, renseigner `TWILIO_WEBHOOK_BASE_URL`
(ex. `https://api.pulsepro.fr`) : la signature Twilio est calculée sur l'URL publique exacte.

### 3. Renvoi d'appel sur non-réponse (côté gérant)
Depuis le mobile du gérant, composer : `**61*<numéro Twilio>#` puis appeler
(ex. `**61*+33912345678#`). Variante avec délai : `**61*<numéro>**20#` (20 s avant renvoi).
Désactivation : `##61#`. Certains opérateurs (ou lignes fixes / box) passent par leur espace client ;
renvoi si occupé : `**67*<numéro>#`, si injoignable : `**62*<numéro>#`.

### 4. WhatsApp
- Le résumé peut partir par WhatsApp (`whatsapp:+TWILIO_WHATSAPP_NUMBER` → numéro du gérant).
  Il faut un **expéditeur WhatsApp Business approuvé** dans Twilio (*Messaging → Senders → WhatsApp*).
- Un message à l'initiative de l'entreprise (hors fenêtre de 24 h après un message du gérant) exige
  un **modèle (template) approuvé par Meta** ; sans lui, l'envoi échoue et les autres canaux
  (SMS / email) prennent le relais. Le sandbox Twilio suffit pour les tests.
- Canaux par commerce : `notify_channels` parmi `whatsapp`, `sms`, `email` (défaut `["whatsapp","sms"]`).
- Bonus : les clients peuvent écrire sur WhatsApp au même numéro. Dans l'expéditeur WhatsApp,
  *When a message comes in* → `POST https://<API>/receptionist/whatsapp/<business_id>` ; la même
  qualification se fait par écrit et le gérant reçoit le résumé.

### 5. Variables d'environnement
| Variable | Rôle |
|---|---|
| `TWILIO_ACCOUNT_SID` | Compte Twilio (API SMS) |
| `TWILIO_AUTH_TOKEN` | Validation des signatures webhooks + API SMS (sans elle, les webhooks répondent 403) |
| `TWILIO_PHONE_NUMBER` | Numéro Twilio au format E.164, expéditeur des SMS |
| `TWILIO_WHATSAPP_NUMBER` | Expéditeur WhatsApp Twilio (E.164, sans préfixe `whatsapp:`) |
| `TWILIO_WEBHOOK_BASE_URL` | (optionnel) URL publique de l'API pour la signature |
| `RECEPTIONIST_VOICE` | (optionnel) voix TTS, défaut `Polly.Lea` |

Les trois premières sont synchronisées dans Secret Manager par `deploy.sh` et montées par
`cloudbuild.yaml` / `cloudbuild.github.yaml`. L'email au gérant réutilise la config SMTP des alertes,
le LLM réutilise la chaîne de providers existante (`GEMINI_API_KEY`…) avec un script de secours.

### 6. API
- `POST /client/space/receptionist/activate` — démarre l'essai (session client)
- `GET /client/space/receptionist` — statut (`trial`/`active`/`expired`), jours restants, appels récupérés
- `GET|POST /businesses/<id>/receptionist[/activate]` — cockpit admin (`{"paid_active": true}` pour passer en payant)

## 🎨 Templates Métiers
Le système switch automatiquement entre les styles suivants en fonction de la catégorie Google Places :
- **luxury-dining-v3** : Restaurants et Food.
- **clean-medical-v1** : Pharmacies et cabinets médicaux.
- **industrial-bold-v2** : Garages et services techniques.

---
*Développé pour l'automatisation de prospection B2B haute fidélité.*
