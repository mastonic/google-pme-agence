# Architecture du système email — Pulse Locale PME

## Vue d'ensemble

```
Formulaire (.fr / .info / .store)          Stripe (événement signé)
        │  POST /leads                               │  POST /webhook/stripe
        ▼                                             ▼
 backend/lead_api.py                         backend/main.py (_queue_order_emails)
  ├─ validation, origine, pot de miel,        └─ seulement si payment_status == "paid"
  │  temps de remplissage, limite de débit
  ├─ anti-doublon (request_id + empreinte 10 min)
  └─ UNE transaction : InboundLead (CRM) + 2 lignes email_outbox
                         │
                         ▼
         backend/services/email_service.py
          ├─ enqueue()          file `email_outbox` (event_key unique)
          ├─ dispatch()         réservation atomique → SMTP → statut
          ├─ relance            1 min, 5 min, 30 min, 2 h, 6 h puis « dead »
          └─ transport          SMTP authentifié IONOS (SSL 465 ou STARTTLS 587)
```

Principes :

- **Aucune perte** : la demande et ses emails sont enregistrés ensemble ; une panne SMTP laisse les emails en file (`failed`, relance planifiée) sans toucher à la demande. Sans configuration SMTP, ils restent `pending` et partent dès que la configuration existe.
- **Aucun doublon** : `request_id` (un par ouverture de formulaire) et empreinte email + type + contenu sur 10 minutes côté demandes ; `event_key` unique côté emails (`lead:{id}:internal`, `lead:{id}:ack`, `order:{session}:ack`, `order:{session}:internal`). Un webhook Stripe rejoué ne renvoie rien.
- **Aucune fausse confirmation de paiement** : les emails de commande ne partent que sur un événement Stripe dont la signature est vérifiée **et** dont `payment_status` vaut `paid` (`checkout.session.completed` ou `checkout.session.async_payment_succeeded`). La page de retour Stripe ne déclenche aucun email.
- **Expéditeur authentifié** : `From` = compte SMTP (`contact@pulse-locale-pme.fr`) ; une autre adresse n'est utilisée que si elle est listée dans `SMTP_ALLOWED_FROM` et appartient au domaine. `Reply-To` = client (notification interne) ou boîte du service (accusé client), après validation stricte de la syntaxe.
- **Pas de secret dans le code** : tout passe par variables d'environnement / Secret Manager. Les journaux masquent les adresses (`m***@domaine`) et n'affichent jamais de mot de passe.

## Fonctions du module (`backend/services/email_service.py`)

| Fonction | Rôle |
|---|---|
| `send_email()` | Envoi direct (lien de connexion, alertes, rapport mensuel) avec 2 nouvelles tentatives rapprochées sur erreur temporaire |
| `send_internal_notification(db, lead)` | Notification à la boîte du type de demande |
| `send_customer_confirmation(db, lead)` | Accusé de réception (contact, devis, démo, audit, support) |
| `send_audit_confirmation` / `send_support_confirmation` | Raccourcis (type forcé) |
| `send_order_confirmation(db, order)` | Commande payée : client + commandes@ |
| `dispatch(db, ids)` / `dispatch_in_new_session` | Envoi des emails en file, réservation atomique (jamais deux fois) |
| `purge_outbox(db, days=90)` | Conservation limitée des copies d'emails |
| `config_status()` | Diagnostic sans secret (route admin `/admin/email/status`) |

## Données

- `inbound_leads` (CRM existant, enrichi) : `kind`, `site`, `request_id`, `dedupe_key`.
- `email_outbox` (nouvelle) : `event_key` unique, `category` (internal / customer), `kind`, `to_addr`, `reply_to`, `subject`, `body_text`, `body_html`, `status` (pending / sending / sent / failed / dead), `attempts`, `next_attempt_at`, `last_error`, `lead_id`, `ref`.
- Migrations automatiques au démarrage (`run_migrations()` dans `backend/main.py`).

## Statuts CRM (cockpit, onglet Leads)

Nouveau (`new`) → À contacter (`to_call`) → Contacté (`contacted`) → Devis envoyé (`quote_sent`) → Converti (`won`) / Clos (`lost`). Aucune fusion automatique de contacts.

## Observabilité

Journaux structurés (logger `pulse.leads` et `pulse.email`) :

| Événement | Message |
|---|---|
| Demande soumise et enregistrée | `leads.created lead=… kind=… site=…` |
| Abus | `leads.abuse reason=honeypot|too_fast|foreign_origin|rate_limited` |
| Doublon | `leads.duplicate reason=request_id|same_request` |
| Base indisponible | `leads.store_failed` (réponse 503, aucun email) |
| Email en file / envoyé | `email.queued`, `email.sent` |
| Échec + relance | `email.retry_scheduled … in=…s`, puis `email.dead` |
| SMTP non configuré | `email.waiting_config` |

Cockpit / API admin : `GET /admin/email/status` (configuration sans secret, compteurs par statut, 20 derniers échecs), `POST /admin/email/flush` (relance immédiate).

## Exploitation Cloud Run

La boucle de relance tourne toutes les 5 minutes dans l'instance (désactivable : `EMAIL_OUTBOX_LOOP=false`). Avec le CPU bridé hors requêtes, une relance peut être retardée jusqu'à la requête suivante ; chaque nouvelle demande déclenche aussi l'envoi de ses propres emails. Recommandation : `--no-cpu-throttling` ou un Cloud Scheduler appelant `POST /admin/email/flush` toutes les 5 minutes.
