# Journal des modifications — système email

## 2026-11-08 — branche feat/pulse-locale-email-system

| Problème | Fichier(s) | Modification | Test |
|---|---|---|---|
| Trois implémentations SMTP dupliquées (alertes, lien de connexion, rapport), expéditeur de repli `contact@pulsepro.fr` hors domaine | `backend/services/email_service.py`, `alerts.py`, `monthly_report.py`, `client_space_api.py` | Transport unique (SSL ou STARTTLS, timeout, nouvelles tentatives, expéditeur autorisé) | suite complète |
| Toutes les demandes envoyées à une seule adresse (`ALERT_EMAIL`), sans accusé client | `backend/lead_api.py` | Routage par type vers contact@ / devis@ / audit@ / support@ + accusé de réception | 1-4, 7 |
| Email perdu si le SMTP tombe | `email_service.py`, `models/database.py` | File `email_outbox` dans la même transaction que la demande, relances 1 min → 6 h | 11, 12 |
| Aucun email de commande | `backend/main.py` | Confirmation client + commandes@ sur événement Stripe signé et payé, idempotent | 5, 6 |
| Doublons (double clic, retry) | `lead_api.py`, `OrderButton.tsx`, `LeadForm.tsx`, `leads.ts` | `request_id` + empreinte 10 min | 10 |
| Anti-spam limité | `lead_api.py`, formulaires | Origine, temps de remplissage, pot de miel, limite de débit, journalisation des abus | 9 |
| Pas de formulaire de support ni de question produit | `app/store/page.tsx`, `app/store/fiche-google-optimisee/page.tsx` | Deux formulaires (support@, contact@) | 7 + navigateur |
| Statuts CRM incomplets | `lead_api.py`, `frontend/src/components/LeadsView.jsx` | Ajout « Devis envoyé » ; libellés Contacté / Converti / Clos ; type et site affichés | suite |
| Information RGPD incomplète, « désinscription en un clic » inexistante | `PrivacyNotice.tsx`, formulaires, `mentions-legales/page.tsx` | Finalité, responsable, durée, droits, sous-traitants (dont IONOS) ; durées de conservation | — |
| Pas de politique de conservation | `lead_api.py`, `email_service.py`, `main.py` | Purge quotidienne : demandes > 3 ans, copies d'emails > 90 jours | + |
| Base indisponible : erreur 500 brute | `lead_api.py` | 503 explicite, aucune file orpheline | 13 |
| Migrations non appliquées en test | `backend/main.py` (`run_migrations`), `tests/conftest.py` | Migrations exécutées au démarrage des tests | suite |
| Variables email non documentées | `.env.example`, `deploy.sh` | SMTP_SECURE, SMTP_ALLOWED_FROM, EMAIL_* ; délimiteur gcloud compatible virgules | — |
