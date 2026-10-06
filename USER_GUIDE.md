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

#### 📱 Prescriptions électroniques (e-PMT)

Si le patient remet le **mémo d'une prescription électronique**, le déposer comme un bon papier : le numéro de prescription est lu. La prescription se récupère ensuite dans SEFi (ou sur amelipro) avec ce numéro. Voir `docs/transport-sanitaire-e-pmt.md`.

### 💡 Astuces & Dépannage
*   **Redémarrage** : Si vous sentez que l'app est lente sur votre VPS, lancez cette commande dans votre terminal :
    `./start.sh`
*   **Mise à jour** : Pour récupérer mes dernières corrections (photos prioritaires, fluidité), faites toujours :
    `git pull`
*   **Photos** : Si un site web affiche des images vides, c'est souvent que le commerce n'avait aucune photo sur Google Maps. Relancez une génération sur un commerce qui a au moins quelques avis avec photos !
