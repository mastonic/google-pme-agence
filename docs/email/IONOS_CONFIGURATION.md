# Configuration IONOS (messagerie, SMTP, DNS)

> Aucune modification DNS n'a été faite automatiquement. Les valeurs ci-dessous ont été relevées en lecture (DNS publics) le 8 novembre 2026 ; les paramètres SMTP sont à confirmer dans votre espace IONOS.

## 1. Boîte et alias

| Adresse | Type | Action dans IONOS |
|---|---|---|
| contact@pulse-locale-pme.fr | **Boîte** (compte SMTP d'envoi) | Créer la boîte, mot de passe fort |
| devis@, commandes@, support@, audit@ | **Alias / redirections** vers contact@ | Créer comme alias de la boîte contact@ |
| notifications@ (facultatif) | Boîte ou alias | À n'utiliser comme expéditeur qu'après vérification qu'IONOS l'autorise (même domaine) et ajout dans `SMTP_ALLOWED_FROM` |

Un alias ne possède pas ses propres identifiants SMTP : tous les envois partent du compte `contact@`.

## 2. Paramètres SMTP

| Paramètre | Valeur | Source |
|---|---|---|
| Serveur | `smtp.ionos.fr` (comptes IONOS France ; vos MX sont `mx00/mx01.ionos.fr`). `smtp.ionos.com` est indiqué par l'aide IONOS internationale. **À confirmer dans IONOS > Email > Paramètres de la boîte** | DNS publics, aide IONOS |
| Port / sécurité | 465 + SSL/TLS (`SMTP_SECURE=ssl`) ou 587 + STARTTLS (`SMTP_SECURE=starttls`) | Aide IONOS |
| Identifiant | adresse complète `contact@pulse-locale-pme.fr` | Aide IONOS |
| Mot de passe | celui de la boîte (chaque adresse a son propre mot de passe) | Aide IONOS |
| Expéditeur | adresse du même domaine que le compte (règle IONOS depuis le 29/01/2024) | Aide IONOS |
| Limite d'envoi | IONOS limite l'envoi en masse par heure (de l'ordre de quelques centaines d'emails/heure selon l'ancienneté du contrat) ; en cas de dépassement, erreur 450 — le service la traite comme temporaire et relance | Aide IONOS « restrictions d'envoi en masse » |

Volume attendu (accusés + notifications de formulaires) : très inférieur à ces limites ; SMTP IONOS convient. Si le volume devenait important (campagnes, milliers d'emails/jour), passer à un service transactionnel (ex. Brevo, Postmark, Amazon SES) — à chiffrer avant toute migration.

## 3. Variables à créer (Secret Manager / .env)

```
SMTP_HOST=smtp.ionos.fr          # à confirmer
SMTP_PORT=465
SMTP_SECURE=ssl
SMTP_USER=contact@pulse-locale-pme.fr
SMTP_PASSWORD=********            # Secret Manager uniquement
SMTP_FROM=contact@pulse-locale-pme.fr
```

`./deploy.sh` synchronise `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` dans Secret Manager depuis `.env` et transmet `SMTP_SECURE`, `SMTP_ALLOWED_FROM`, `EMAIL_*` comme variables simples.

## 4. DNS de délivrabilité — état relevé

| Enregistrement | Valeur publiée | État |
|---|---|---|
| MX | `mx00.ionos.fr`, `mx01.ionos.fr` (priorité 10) | ✅ |
| SPF (TXT @) | `v=spf1 include:_spf-eu.ionos.com ~all` | ✅ un seul SPF, couvre les serveurs IONOS |
| DKIM | `s1-ionos._domainkey` → CNAME `s1.dkim.ionos.com`, `s2-ionos._domainkey` → CNAME `s2.dkim.ionos.com` | ✅ présents |
| DMARC (`_dmarc`) | `v=DMARC1; p=none;` (via `dmarc.ionos.fr`) | ⚠️ surveillance seulement, sans rapport |

## 5. Checklist IONOS

- [ ] Créer la boîte contact@ et noter le mot de passe dans Secret Manager (jamais dans GitHub).
- [ ] Créer les alias devis@, commandes@, support@, audit@ vers contact@.
- [ ] Vérifier dans IONOS le serveur SMTP exact et le port.
- [ ] Vérifier que **DKIM est activé** pour le domaine dans IONOS (les CNAME existent ; l'activation se voit dans l'espace Email).
- [ ] Ne **pas** ajouter un second enregistrement SPF. Si un autre service d'envoi est ajouté un jour, l'inclure dans l'enregistrement existant (`v=spf1 include:_spf-eu.ionos.com include:… ~all`).
- [ ] DMARC, progression prudente :
  1. maintenant : `v=DMARC1; p=none; rua=mailto:dmarc@pulse-locale-pme.fr` (créer l'alias dmarc@) pour recevoir les rapports ;
  2. après 2 à 4 semaines de rapports propres : `p=quarantine; pct=25`, puis `pct=100` ;
  3. ensuite seulement : `p=reject`.
  Vérifier dans IONOS si l'enregistrement `_dmarc` est géré par IONOS (CNAME vers `dmarc.ionos.fr`) avant de le modifier.
- [ ] Test manuel contrôlé (voir `EMAIL_TESTS.md`).
