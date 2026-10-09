# 📖 Guide d'Utilisation : Local-Pulse Cockpit

Local-Pulse est conçu pour automatiser votre prospection de A à Z : de la recherche d'un commerce mal noté sur Google Maps jusqu'à la création d'une démo de site web ultra-personnalisée et d'un email de vente.

---

### 1️⃣ Étape 1 : Prospection (Menu "Campaigns")
C'est ici que tout commence. Vous cherchez vos "cibles" sur la carte.

*   **Recherche** : Saisissez une ville ou un code postal (ex: `97200` ou `Paris`) dans la zone de recherche en bas à gauche.
*   **Navigation** : Naviguez librement sur la carte. Elle est maintenant fluide et ne saute plus.
*   **Scan** : Une fois sur la zone voulue, cliquez sur **"🔍 Scanner cette zone"**. Le système récupère alors les 20 commerces les plus pertinents via Google Maps.
*   **Identification** : 
    *   🔴 **Marqueur Rouge** : Très haut potentiel (Note < 4/5, pas de site web).
    *   🟠 **Marqueur Orange** : Potentiel moyen.
    *   🔵 **Marqueur Bleu** : Déjà bien établi.

---

### 2️⃣ Étape 2 : Lancement de l'IA (Diagnostic)
*   **Sélection** : Cliquez sur un marqueur sur la carte. Sa fiche apparaît instantanément sur la droite.
*   **Analyse Rapide** : Vous voyez son score de potentiel, ses photos actuelles et s'il a déjà un site web.
*   **Action** : Cliquez sur le bouton pulsant **"🚀 Générer Média & Démo Complete"**.
    *   *L'IA va alors s'activer en arrière-plan pour créer le site, les textes et les photos.*
    *   *Vous serez automatiquement redirigé vers le Cockpit.*

---

### 3️⃣ Étape 3 : Surveillance (Menu "Cockpit")
C'est le "centre de commandement" où vous voyez vos agents travailler en temps réel.

*   **Le Scout** : Il fouille Google Maps pour trouver les meilleures photos (Propriétaire et Clients) et analyse les avis.
*   **Le Stratège** : Il écrit les textes persuasifs (Slogans, bénéfices).
*   **Le Designer** : Il choisit le meilleur template (Bento, Luxe, Médical).
*   **L'Ingénieur** : Il assemble le code et déploie le site sur **Vercel**.
*   **Le Closer** : Il prépare le brouillon de l'email de vente dans votre Gmail.

---

### 4️⃣ Étape 4 : Closing & Vente (Menu "CRM")
C'est ici que vous récupérez vos "munitions" pour contacter le client.

*   **Liste des Dossiers** : Cliquez sur **"Ouvrir Dossier"** pour le commerce que vous venez de générer.
*   **Onglets du Dossier** :
    *   **📝 Rapport & Copy** : Les arguments de vente basés sur les points faibles du concurrent.
    *   **🖼️ Photos** : Les photos réelles récupérées (ou les photos IA si aucune n'existait).
    *   **📧 Email Draft** : Le texte de l'email personnalisé. *Copiez-le et envoyez-le !*
    *   **🌐 Site Web** : **L'élément le plus puissant**. Vous avez une URL Vercel live montrant au commerçant à quoi ressemblerait son site idéal avec SES vraies photos.

---

### 🚑 Bons de transport (clients ambulanciers)

Menu **« Bons de transport »**. Gère la prescription médicale de transport papier (Cerfa 11574\*04, volets 1 et 2).

1. **Déposer le scan** (PDF ou photo prise au téléphone). Le bon est lu automatiquement (Gemini, puis OpenAI en secours).
2. **Corriger** les champs entourés en orange ou rouge. Modifier un champ « lecture incertaine » le marque comme vérifié.
3. **Compléter la course** : date, km aller, véhicule, équipage, référence d'accord préalable si besoin.
4. **Lire les contrôles** : NIR et sa clé, RPPS, FINESS, signature, situation de prise en charge, justification de l'ambulance, prescription datée avant le transport, accord préalable au-delà de 150 km ou pour une série de 4 transports de plus de 50 km.
5. **Valider** les dossiers « À vérifier » (impossible tant qu'il reste un point bloquant). Les dossiers « Prêt à facturer » n'ont besoin d'aucune intervention.
6. **Exporter** vers le logiciel de facturation (ISIS, Mélusine, Drivesoft, Tele Ambu, MK2i…) :
   - **CSV Excel** (recommandé), **CSV Windows-ANSI** pour les logiciels anciens qui affichent mal les accents, **Excel (.xlsx)**, **JSON** pour une intégration par API ;
   - **ZIP dossiers complets** : tableau récapitulatif + un dossier par transport avec la PMT scannée (pièce justificative à joindre via SCOR) et la fiche imprimable ;
   - **Personnaliser** : choisir, ordonner et renommer les colonnes, le séparateur, l'encodage, le format des dates et des cases pour coller au modèle d'import du logiciel du client. Le profil est enregistré pour ce client.

   Seuls les dossiers prêts (ou vérifiés) partent, et un dossier exporté ne repart pas en double. S'il est modifié après export, il repasse en brouillon.

Les indicateurs en haut d'écran montrent le **taux de dossiers prêts sans retouche** (objectif 80–90 %) et les causes d'anomalie les plus fréquentes, à remonter aux prescripteurs.

Le scan est conservé pour l'export ZIP et supprimé avec le dossier. `PMT_KEEP_SCANS=0` désactive la conservation ; `POST /pmt/scans/purge?days=90` efface les scans des dossiers exportés depuis plus de 90 jours.

⚠️ Données de santé : avant de traiter de vrais patients, il faut un hébergement certifié HDS et un fournisseur de lecture automatique couvert par contrat.

#### 🔐 Connexion (obligatoire)

Le module contient des données de santé : toutes les routes `/pmt` exigent une connexion.

- **Premier administrateur** : définir `PMT_ADMIN_EMAIL` et `PMT_ADMIN_PASSWORD` sur le serveur, il est créé au démarrage.
- **`PMT_AUTH_SECRET`** (longue chaîne aléatoire) : obligatoire en production, sinon les sessions sautent à chaque redémarrage.
- Onglet **Comptes** (admin) : un compte par ambulancier, rattaché à son entreprise. Un client ne voit que ses dossiers, ses rejets et ses profils d'export.
- 5 essais ratés bloquent la connexion 15 minutes. Changer un mot de passe ou désactiver un compte ferme ses sessions ouvertes.

#### 📉 Rejets CPAM

Onglet **Rejets CPAM**. Importer ce que renvoie la caisse :
- l'**export des rejets ou paiements** du logiciel de facturation (CSV ou Excel : les colonnes sont reconnues automatiquement) ;
- le **fichier retour du concentrateur** (format B2 à positions fixes) ;
- un **relevé PDF ou une photo** (lu automatiquement).

Chaque rejet est rattaché à son dossier (NIR + date), classé par motif avec la cause probable et l'action à mener, puis suivi : à traiter → en correction → renvoyé → récupéré / abandonné. **Rouvrir le dossier** le remet en brouillon pour le corriger ; il repart au prochain export. Un **paiement importé** clôt automatiquement les rejets du dossier (« récupéré »).

Le diagnostic indique si le rejet avait été signalé par nos contrôles avant l'envoi, ou s'il faut renforcer un contrôle.

- Les rejets sont **triés par priorité** (montant × ancienneté). Au-delà de **15 jours** sans suite, ils sont signalés en rouge : la récupération devient plus difficile.
- **Courrier au patient** : pour les motifs où la caisse ne paiera pas (transport avant la prescription, accord préalable absent, droits fermés, ALD non reconnue, refus de la mutuelle), un courrier explique au patient pourquoi on lui demande de payer et comment contester.
- **Dossier de preuve** (onglet Dossiers) : à présenter lors d'un contrôle ou contre un indu. Il reprend ce qui a été facturé, les contrôles figés au moment de l'export et l'historique des retours caisse.
- Renseigner les **km de la trace de géolocalisation certifiée** : au moindre écart avec les km facturés, la caisse rejette automatiquement.

#### 🗓️ Planning et validation départ / retour

**Gérant — onglet Planning** : les courses du jour (heure de prise en charge, patient, départ → arrivée, aller / retour / aller-retour, ambulance ou VSL, véhicule, équipiers, consignes).
- L'outil signale les **chevauchements** (même équipier ou même véhicule sur deux courses en même temps), un **équipage non conforme** (pas de DEA dans l'ambulance, AFGSU expirée…), un véhicule ou un équipage non affecté.
- **Publier** : les équipiers voient leurs missions du jour. **Valider la journée** : clôture par le gérant (refusée s'il reste des courses non terminées, sauf confirmation) ; une journée validée n'est plus modifiable.
- Indicateurs : courses en route, terminées, non terminées, **en retard au départ** (plus de 15 minutes après l'heure prévue).

**Équipier — onglet Mes missions** (téléphone) : pour chaque mission, de gros boutons **Accepter → Départ → Patient déposé → Retour**, horodatés à l'heure française (option : relevé du compteur kilométrique au départ et au retour).
- Au **retour**, le dossier de facturation est créé automatiquement avec la date, l'**heure réelle de départ**, le véhicule et l'équipage ; le bouton **Photographier le bon** complète ce même dossier (pas de doublon).
- L'heure réelle de départ sert ensuite au rattachement des traces GPS.
- Aucune position GPS n'est enregistrée par ces validations : seulement l'heure, l'auteur et, si demandé, le compteur.

#### 👥 Équipe et accès équipiers

Onglet **Équipe** (gérant et admin). Un registre des salariés avec, pour chacun : qualification (DEA, CCA, DA, auxiliaire ambulancier, conducteur…), dates de fin de validité de l'**attestation préfectorale de conduite**, de l'**AFGSU niveau 2** (4 ans), du permis et de l'aptitude médicale, contrat, date de déclaration à l'ARS.

- Statut par salarié : **en règle**, **à renouveler** (moins de 60 jours) ou **non conforme**.
- Dans un dossier, l'équipage se choisit dans le registre. Contrôles à la **date du transport** : ambulance = 2 équipiers dont au moins un DEA (ou CCA / DA) ; VSL = 1 conducteur DEA / CCA / auxiliaire ; documents valides et contrat en cours. Un équipage non en règle bloque le dossier (risque d'indu lors d'un contrôle).
- Mettre à jour une date (AFGSU renouvelée…) recontrôle automatiquement les dossiers non exportés.
- **Accès équipier** : le gérant crée un accès pour un salarié. L'équipier se connecte sur son téléphone, photographie le bon et complète sa course (il est mis d'office dans l'équipage). Il ne voit ni les exports, ni les rejets, ni les traces, ni les données RH de ses collègues, et ne peut ni valider ni supprimer. Passer un salarié en inactif coupe son accès.
- Aucune donnée médicale n'est enregistrée, seulement des dates de validité.

#### 📍 Traces GPS (géolocalisation)

Onglet **Traces GPS**. Importer l'export du boîtier de géolocalisation : **GPX** (le plus courant), **KML**, ou **CSV / Excel** (un point GPS par ligne, ou une course par ligne avec les km).

- Chaque course est détectée (les longs arrêts séparent les courses, les sauts GPS aberrants sont ignorés) et rattachée au dossier du **même véhicule, même jour, heure de départ la plus proche**. Les cas ambigus sont laissés au choix de l'utilisateur.
- Les km de la trace remplissent le dossier (« km de la trace certifiée », et les km facturés s'ils étaient vides) : **plus de saisie manuelle**. Si des km facturés existent déjà et dépassent la trace, le dossier est bloqué.
- Les **trous dans la trace** (coupures réseau) et les **dossiers sans trace** sont signalés : une course facturée sans trace complète risque le rejet.
- **Données minimisées** : les points GPS ne sont pas conservés, seulement le résumé de chaque course, effacé après 90 jours (`PMT_TRACE_RETENTION_DAYS`). Le projet de loi contre la fraude limite l'usage de ces données à la vérification des transports facturés et leur conservation à trois mois.

#### 📱 Prescriptions électroniques (e-PMT)

Si le patient remet le **mémo d'une prescription électronique**, le déposer comme un bon papier : le numéro de prescription est lu. La prescription se récupère ensuite dans SEFi (ou sur amelipro) avec ce numéro. Voir `docs/transport-sanitaire-e-pmt.md`.

### 💡 Astuces & Dépannage
*   **Redémarrage** : Si vous sentez que l'app est lente sur votre VPS, lancez cette commande dans votre terminal :
    `./start.sh`
*   **Mise à jour** : Pour récupérer mes dernières corrections (photos prioritaires, fluidité), faites toujours :
    `git pull`
*   **Photos** : Si un site web affiche des images vides, c'est souvent que le commerce n'avait aucune photo sur Google Maps. Relancez une génération sur un commerce qui a au moins quelques avis avec photos !
