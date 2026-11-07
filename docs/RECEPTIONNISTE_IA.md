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
