# Réceptionniste IA : configurer Twilio, tester, choix technique

## 1. Choix technique

| Option | Latence | Interruption | Coût / contrôle | Verdict |
|---|---|---|---|---|
| **Twilio `<Gather speech>` + `<Say>`** (moteur `gather`, défaut) | 2–4 s par phrase | non | le moins cher, tout chez nous | parfait pour tester et pour la messagerie |
| **Twilio ConversationRelay** (moteur `relay`) | < 1 s | oui | Twilio gère STT/TTS, notre LLM + prompt + résumés | **recommandé en production** |
| Vapi / Retell / ElevenLabs Agents | < 1 s | oui | coût/minute qui s'empile, prompt et données chez un tiers | écarté |

On garde Twilio (numéros FR + bundle réglementaire, SMS, WhatsApp sur le même compte) et on bascule
d'un moteur à l'autre avec `RECEPTIONIST_ENGINE=gather|relay`, sans rien changer d'autre : même
prompt, mêmes réglages du gérant, mêmes résumés. Le moteur `relay` utilise un WebSocket
(`wss://<API>/receptionist/relay/<business_id>`) : Cloud Run le supporte.
Voix `relay` réglables : `RECEPTIONIST_RELAY_TTS_PROVIDER`, `RECEPTIONIST_RELAY_VOICE_FEMME`,
`RECEPTIONIST_RELAY_VOICE_HOMME`, `RECEPTIONIST_RELAY_STT_PROVIDER` (laisser vide = valeurs par défaut de Twilio).

## 1 bis. Webhooks et API : architecture retenue
```
Appelant ──► numéro Twilio ──► https://local-pulse-api-xxxx.run.app/receptionist/...  (Cloud Run, direct)
                                       │  vérifie X-Twilio-Signature, IA, base de données
Gérant ◄── résumé WhatsApp / SMS ◄─────┘  (API Twilio Messages)
```
- **Twilio appelle directement l'URL Cloud Run** (`*.run.app`), pas le domaine Firebase : Firebase Hosting
  ne relaie pas `/receptionist/**` et ne gère pas les WebSockets (moteur `relay`).
- Pas d'intermédiaire (n8n, Zapier) : latence en plus, signature Twilio invalide, logique en double.
- `TWILIO_WEBHOOK_BASE_URL` est inutile avec l'URL `run.app` ; elle ne sert que pour un domaine perso
  (ex. `api.pulsepro.fr` mappé sur Cloud Run).
- URL : `gcloud run services describe local-pulse-api --region europe-west1 --format 'value(status.url)'`
  ou cockpit → onglet Réceptionniste → *Configuration Twilio*.
- Clés : `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `TWILIO_WHATSAPP_NUMBER` dans `.env`
  puis `./deploy.sh` (synchronisées dans Secret Manager et montées dans Cloud Run).
- `min-instances=1` est déjà en place : pas de démarrage à froid (Twilio abandonne après 15 s).
- En local : `uvicorn backend.main:app --port 8000` + `ngrok http 8000`, et l'URL ngrok dans Twilio.

## 2. Tester sans Twilio (2 minutes)
Cockpit → fiche du commerce → onglet **Réceptionniste** → *Simulateur*. Même IA, mêmes réglages, à l'écrit ;
le résumé que recevrait le gérant s'affiche à la fin. Le client a le même test dans son espace (dernière étape de l'onboarding).

## 3. Configurer un compte Twilio neuf
1. **Console → Account info** : copier *Account SID* et *Auth Token* →
   variables `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` du backend (puis redéployer).
2. `TWILIO_WEBHOOK_BASE_URL` = URL publique HTTPS du backend (Cloud Run `local-pulse-api`, ex. `https://local-pulse-api-xxxx.run.app`).
   Sans HTTPS public, Twilio ne peut pas appeler les webhooks (en local : `ngrok http 8000`).
3. Cockpit → onglet **Réceptionniste** → bloc *Configuration Twilio* : vérifie les variables et donne les URLs exactes à copier.

### WhatsApp (sandbox, gratuit, immédiat)
1. *Messaging → Try it out → Send a WhatsApp message* : depuis ton WhatsApp, envoie `join <code>` au +1 415 523 8886.
2. Onglet **Sandbox settings** → *When a message comes in* : `https://<API>/receptionist/whatsapp/<business_id>` — **POST** → Save.
   ⚠️ Le sandbox n'a qu'une URL par compte : elle remplace celle d'un autre projet (ex. un webhook n8n).
3. `TWILIO_WHATSAPP_NUMBER=+14155238886` pour que le gérant reçoive aussi ses résumés par WhatsApp
   (son numéro doit avoir rejoint le sandbox).
4. Activer la réceptionniste sur le commerce (cockpit), puis écrire « J'ai une fuite » au numéro sandbox.

### Appels vocaux
1. Compte d'essai : *Phone Numbers → Buy a number* (un numéro US suffit pour tester ; numéro FR = bundle réglementaire).
   En essai, Twilio n'appelle/n'envoie qu'aux **Verified Caller IDs** : vérifier son mobile.
2. Sur le numéro → *Voice configuration* : *A call comes in* = `https://<API>/receptionist/voice/<business_id>` (POST),
   *Call status changes* = `.../status` (POST). `TWILIO_PHONE_NUMBER` = ce numéro (E.164).
3. Appeler le numéro (un message « trial account » est joué d'abord en compte d'essai), parler, raccrocher → résumé SMS/WhatsApp.
4. En réel : le gérant compose sur son mobile les codes de renvoi affichés dans son onglet Réceptionniste (`**61*<numéro>#`…).

## 4. Côté client (espace `/espace`)
- Carte « Nouveau : ta réceptionniste IA » sur *Performance* → activation (30 jours offerts).
- Une fois activée : onglet **Réceptionniste** ; à la 1re visite, onboarding en 6 étapes
  (bienvenue, assistante : prénom/voix/métier/accueil, infos qu'elle peut donner, notifications, renvoi d'appel, test).
- Ensuite : statistiques, derniers appels, codes de renvoi, réglages modifiables, simulateur.

## 5. Pack Connecté (19 € HT/mois, inclus dans Élite, offert pendant l'essai)

Ce que fait le pack :
- **Google Agenda** : à chaque appel, la réceptionniste lit les créneaux libres du gérant (`freeBusy`, selon ses horaires d'ouverture, 7 jours, délai de 2 h).
  - Elle en propose 2 ou 3, puis réserve celui que l'appelant accepte.
  - Un créneau absent de la liste proposée n'est jamais réservé.
  - Si la réservation échoue, le rendez-vous est noté « à confirmer » dans le résumé.
- **Google Sheets** : le tableur « Appels – <commerce> » est créé dans le Drive du gérant, avec une ligne par appel.
- **Webhook** : un POST JSON (`event: call.completed`) est envoyé après chaque appel, signé avec l'en-tête `X-Pulse-Signature: sha256=<HMAC>`.
  - Il se branche sur Zapier (« Catch Hook »), Make, n8n ou toute autre application.

### Configuration (une seule fois)
1. **Clé de chiffrement** :
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Enregistrer le résultat dans le secret `INTEGRATIONS_KEY`. Ne jamais la changer, sinon les comptes Google déjà connectés devront se reconnecter.
2. **Google Cloud Console** (projet du backend) :
   - activer **Google Calendar API** et **Google Sheets API** ;
   - créer l'**écran de consentement OAuth** en mode « Externe » : nom « Pulse Locale PME », logo, domaine `pulse-locale-pme.fr`, lien vers la politique de confidentialité `https://pulse-locale-pme.fr/mentions-legales/#rgpd` ;
   - déclarer les accès demandés (« scopes ») : `openid`, `email`, `drive.file`, `calendar.events`, `calendar.freebusy` ;
   - créer les **identifiants** de type « ID client OAuth / Application Web », avec comme URI de redirection autorisée `https://<site public>/integrations/google/callback` ;
   - enregistrer l'ID et le secret dans `GOOGLE_OAUTH_CLIENT_ID` et `GOOGLE_OAUTH_CLIENT_SECRET`.
3. `./deploy.sh` (les trois secrets sont synchronisés et montés dans Cloud Run). La règle `/integrations/**` est déjà dans `firebase.json`.
4. **Validation Google** :
   - `calendar.events` est un accès « sensible » : tant que Google n'a pas vérifié l'application, seuls les comptes ajoutés en « utilisateurs test » (100 maximum) peuvent la connecter ;
   - pour l'ouvrir à tous, il faut lancer la vérification depuis l'écran de consentement (quelques jours à quelques semaines). Google demande une vidéo de démonstration de la connexion.

### Activation commerciale
- **Élite** : le pack est inclus automatiquement.
- **Essai de la réceptionniste** : le pack est offert.
- **Autres clients** : cockpit → onglet Réceptionniste → « Activer l'option payante » (`POST /businesses/<id>/receptionist/connect {"paid": true}`), ou demande du client depuis son espace.
