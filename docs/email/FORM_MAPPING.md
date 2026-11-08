# Cartographie des formulaires

Tous les formulaires publics utilisent le composant `OrderButton` (fenêtre modale) ou `LeadForm`, et l'endpoint unique `POST /leads` (réécrit vers Cloud Run par Firebase sur les trois domaines). Stockage : table `inbound_leads` (CRM, cockpit onglet Leads). Avant : une alerte unique vers `ALERT_EMAIL`. Désormais : notification routée + accusé de réception, en file.

| Formulaire | Domaine | Page d'origine | Composant | Type (`kind`) | Email destinataire | Endpoint | Données | Statut du test |
|---|---|---|---|---|---|---|---|---|
| Contact (pied de page, « Nous écrire », « Question à HoldMasto ») | .fr / .info / .store | toutes les pages | `OrderButton source="contact"` | contact | contact@ | POST /leads | nom, commerce, email*, téléphone, ville, message | ✅ auto |
| Demande de devis (« Recevoir nos tarifs », formules, abonnements, packs, matériel, « Suite à ma démo ») | .fr / .store | accueil, boutique, fiche Google | `OrderButton` | devis | devis@ | POST /leads | + produit, créneau de rappel | ✅ auto |
| Demande de démonstration (« Recevoir ma démo », pages locales, méthode, réceptionniste) | .fr | accueil, pages Yvelines / Eure-et-Loir, villes, méthode | `OrderButton` | demo | devis@ | POST /leads | idem | ✅ auto |
| Test de visibilité gratuit | .info | /info/outil-gratuit/ | `LeadForm source="score_tool"` | audit | audit@ | POST /leads | email*, commerce, ville, score, réponses | ✅ auto |
| Commande « Audit visibilité IA » | .store | /store/ | `OrderButton` (produit « Audit… ») | audit | audit@ | POST /leads | produit | ✅ auto (déduction du type) |
| Guide PDF gratuit | .info | /info/guide-gratuit/ | `LeadForm source="guide_pdf"` | guide | contact@ | POST /leads | email*, commerce, ville | ✅ auto |
| Question générale | .info | pied de page | `OrderButton source="contact"` | contact | contact@ | POST /leads | — | ✅ auto |
| Demande de support (**nouveau**) | .store | /store/#aide | `OrderButton kind="support"` | support | support@ | POST /leads | message, référence de commande éventuelle | ✅ auto + navigateur |
| Question sur un produit (**nouveau**) | .store | /store/#aide, fiche Google | `OrderButton kind="product_info"` | product_info | contact@ | POST /leads | question | ✅ auto |
| Commande payée | .store / espace client | Stripe Checkout | webhook Stripe | order_paid | commandes@ + client | POST /webhook/stripe | email, nom, produit, montant (aucune donnée bancaire) | ✅ auto (payée / non payée / rejouée) |
| Demande de modification (client abonné) | espace client | /espace/ | espace client | support | support@ | POST /client/space/requests | type, message | ✅ auto (existant) |

`*` obligatoire. Les autres envois existants passent aussi par le service central : lien de connexion à l'espace client (`/client/auth/request`), rapport mensuel, alertes de supervision, résumés de la réceptionniste IA.

## Risques de duplication traités

| Risque | Mesure |
|---|---|
| Double clic / renvoi du formulaire | `request_id` identique pour une même ouverture → même demande renvoyée (`duplicate: true`) |
| Même demande envoyée deux fois | empreinte email + type + produit + message sur 10 minutes |
| Retry HTTP du navigateur | idem |
| Webhook Stripe rejoué | `event_key = order:{session}:…` unique |
| Relance concurrente | réservation atomique `pending/failed → sending` avant l'envoi |
