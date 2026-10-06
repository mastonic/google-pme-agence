# Transport sanitaire — se positionner face à l'e-PMT

Analyse du 6 octobre 2026. À revoir à chaque étape du déploiement national.

## Comment fonctionne l'e-PMT

- **Côté prescripteur** : deux voies.
  - **SPE** : prescription en ligne sur amelipro, ouverte aux médecins libéraux (carte CPS).
  - **SPEi** : prescription intégrée au logiciel des établissements équipés d'outils de régulation des transports.
- **Côté patient** : il reçoit un **mémo imprimé** portant le numéro de la prescription.
- **Côté transporteur** :
  - **sous SEFi** (depuis son logiciel de facturation certifié), il récupère la prescription avec ce numéro et l'intègre directement à sa facture ;
  - **hors SEFi**, il la consulte sur amelipro avec sa carte professionnelle (CPE/CDE).
- **Calendrier** :
  - objectif de plateformes de régulation opérationnelles dans les 32 CHU d'ici fin 2026 ;
  - l'Assurance maladie propose d'étudier une plateforme nationale d'ici 2027.

  Le papier reste donc majoritaire pendant la transition, en particulier pour les sorties d'hôpital non équipées et pour les médecins qui n'utilisent pas SPE.

## Problèmes pour nous

| # | Problème | Gravité |
|---|---|---|
| 1 | **Pas d'accès aux données e-PMT** : SEFi et amelipro sont réservés aux logiciels certifiés CNDA et aux porteurs de carte. Nous ne pouvons pas lire la prescription électronique nous-mêmes. | Forte |
| 2 | **La lecture du papier perd de la valeur** à mesure que l'e-PMT se diffuse : la donnée arrive déjà structurée dans le logiciel de facturation. | Forte, à moyen terme |
| 3 | **Les logiciels de facturation montent en gamme** : SEFi et la géolocalisation certifiée deviennent obligatoires (2027 selon les éditeurs), et ils ajouteront des pré-contrôles. | Moyenne |
| 4 | **Période hybride** : le client reçoit des bons papier ET des mémos e-PMT, et risque de gérer deux circuits. | Moyenne |
| 5 | **Données de santé** : quel que soit le support, il faut un hébergement HDS et un contrat avec le fournisseur de lecture automatique. | Bloquant pour la production |

## Solutions

1. **Accepter les deux supports dans le même flux** (fait). Le mémo e-PMT se dépose comme un bon papier.
   - Le numéro de prescription est lu et contrôlé.
   - La signature manuscrite n'est plus exigée, puisque la prescription est signée électroniquement.
   - Une consigne rappelle de récupérer la prescription dans SEFi avec ce numéro.
   - Le dossier, les contrôles et l'export restent identiques.
2. **Déplacer la valeur vers ce qui ne dépend pas du support** :
   - les contrôles réglementaires : décret 2026-812 (ALD non exonérante), accords préalables, transport partagé, kilométrage, doublons ;
   - le taux de dossiers prêts ;
   - surtout **les rejets CPAM** (fait) : un rejet arrive aussi sur une e-PMT, et le suivi jusqu'au paiement reste notre valeur.
3. **Partenariat plutôt que certification** : proposer aux éditeurs certifiés (ou passer par une API qu'ils exposent) de pousser nos dossiers contrôlés et de nous renvoyer les retours. Devenir éditeur CNDA coûte trop cher pour ce marché.
4. **Hébergement HDS** avant le premier vrai patient, et un modèle de lecture couvert contractuellement (ou hébergé en Europe sous contrat HDS).
5. **Veille réglementaire intégrée aux contrôles** : chaque nouvelle règle de prise en charge devient un contrôle daté (comme le décret 2026-812 depuis le 1er octobre 2026).

## Sources

- Assurance maladie, transporteurs sanitaires : https://www.ameli.fr/transporteur-sanitaire/exercice-professionnel/prescription-prise-charge/prescription-medicale-transport
- GIE SESAM-Vitale, SPEi transport : https://www.sesam-vitale.fr/en/spei
- Protocole d'accord du 24 septembre 2025 (arrêté du 29 septembre 2025) : https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000052304334
- Décret 2026-812 (ALD non exonérante, 1er octobre 2026) : https://kohenavocats.com/decret-2026-812-transport-sanitaire-ald-transport-partage-remboursement-2026/
