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

### 💡 Astuces & Dépannage
*   **Redémarrage** : Si vous sentez que l'app est lente sur votre VPS, lancez cette commande dans votre terminal :
    `./start.sh`
*   **Mise à jour** : Pour récupérer mes dernières corrections (photos prioritaires, fluidité), faites toujours :
    `git pull`
*   **Photos** : Si un site web affiche des images vides, c'est souvent que le commerce n'avait aucune photo sur Google Maps. Relancez une génération sur un commerce qui a au moins quelques avis avec photos !
