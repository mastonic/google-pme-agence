# Tests du système email

## Tests automatisés (aucun email réel : transport SMTP simulé)

Commande : `python -m pytest -q tests/test_email_system.py tests/test_leads.py`

| # | Scénario | Test | Résultat |
|---|---|---|---|
| 1 | Formulaire contact → contact@ + accusé | `test_routing_and_customer_confirmation[contact]` | ✅ |
| 2 | Demande de devis → devis@ | `test_routing_and_customer_confirmation[devis]` | ✅ |
| 3 | Demande de démonstration → devis@ | `test_routing_and_customer_confirmation[demo]` | ✅ |
| 4 | Demande d'audit (test de visibilité) → audit@ | `test_routing_and_customer_confirmation[audit]` | ✅ |
| 5 | Commande Stripe payée → client + commandes@, une seule fois malgré un webhook rejoué | `test_stripe_paid_order_sends_once_and_unpaid_sends_nothing` | ✅ |
| 6 | Commande Stripe non payée → aucun email | idem | ✅ |
| 7 | Demande de support → support@ + référence SUP-… | `test_routing_and_customer_confirmation[support]`, `test_templates_subjects_and_support_reference` | ✅ |
| 8 | Adresse email invalide / injection d'en-tête | `test_invalid_email_rejected` | ✅ |
| 9 | Spam : pot de miel, remplissage trop rapide, origine étrangère, message trop long | `test_spam_protections` | ✅ |
| 10 | Double soumission | `test_double_submission_creates_one_lead_and_one_pair_of_emails` | ✅ |
| 11 | SMTP indisponible : demande conservée, relance planifiée | `test_smtp_down_keeps_lead_and_schedules_retry_then_sends` | ✅ |
| 12 | Relance après erreur → envoyé | idem | ✅ |
| 13 | CRM (base) indisponible → 503, aucun email orphelin, nouvel essai OK | `test_crm_unavailable_returns_503_without_orphan_email` | ✅ |
| 14 | Absence de secrets : file en attente, diagnostic sans mot de passe, route admin protégée | `test_without_smtp_config_requests_are_kept_and_no_secret_leaks` | ✅ |
| 15 | Expéditeur non autorisé → repli sur le compte SMTP ; injection d'en-têtes impossible | `test_unauthorized_sender_falls_back_and_headers_cannot_be_injected` | ✅ |
| + | Erreur SMTP définitive → `dead` sans relance infinie | `test_permanent_smtp_error_is_dead_not_retried` | ✅ |
| + | Deux relances simultanées → jamais deux envois | `test_concurrent_dispatch_never_sends_twice` | ✅ |
| + | Conservation : purge des demandes > 3 ans et des copies d'emails > 90 jours | `test_retention_purges_old_leads_and_sent_emails` | ✅ |

Vérification navigateur (Chromium, API simulée) : le formulaire de support de la boutique envoie `kind=support`, un `request_id`, `elapsed_ms` > 1,5 s, un seul envoi malgré un double clic, et affiche la référence renvoyée.

## Test manuel contrôlé (après configuration SMTP réelle)

À faire une fois les identifiants dans Secret Manager et le déploiement effectué, **avec vos propres adresses** :

1. `GET /admin/email/status` (en-tête `X-Admin-Token`) : `ready: true`, expéditeur `contact@pulse-locale-pme.fr`.
2. Sur https://pulse-locale-pme.fr : « Nous écrire » avec une adresse personnelle → email reçu dans contact@ (Reply-To = votre adresse) + accusé « Nous avons bien reçu votre message ».
3. « Recevoir nos tarifs » → devis@ ; « Recevoir ma démo » → devis@.
4. https://pulse-locale-pme.info/info/outil-gratuit/ → audit@.
5. https://pulse-locale-pme.store/store/#aide « Contacter le support » → support@ + référence SUP-…
6. Paiement Stripe en **mode test** (carte 4242…) → commandes@ + confirmation client. Vérifier qu'un paiement abandonné n'envoie rien.
7. Vérifier les en-têtes d'un email reçu (Gmail : « Afficher l'original ») : `SPF: PASS`, `DKIM: PASS`, `DMARC: PASS`.
8. `GET /admin/email/status` : aucun échec ; sinon `POST /admin/email/flush` après correction.
