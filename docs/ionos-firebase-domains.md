# Pulse Locale PME — domaines IONOS / Firebase

## Domaines
| Domaine | Rôle | Route existante |
|---|---|---|
| pulse-locale-pme.fr | site principal | / |
| pulse-locale-pme.com | redirection vers .fr | / |
| pulse-locale-pme.info | page dédiée | /info/ |
| pulse-locale-pme.store | boutique dédiée | /store/ (ancre #materiel) |

## État vérifié
- Projet web actuel : https://pme-local-pulse.web.app/
- Dépôt : mastonic/google-pme-agence
- Firebase Hosting actuel : public = landing-site/out
- Firebase Hosting contient des rewrites vers Cloud Run (local-pulse-api, europe-west1).
- Aucun changement DNS, Firebase Console ni déploiement effectué.

## Plan de mise en œuvre (à valider avant activation)
1. Vérifier la présence des fichiers exportés landing-site/out/info/index.html et landing-site/out/store/index.html ainsi que leurs ressources CSS/JS, chemins absolus, navigation et appels API.
2. Préparer trois cibles Firebase Hosting dans le même projet : principale, info, store. Conserver les rewrites API nécessaires. Adapter le build/export pour publier les bons fichiers et assets sur chaque cible. Ne pas publier un sous-dossier sans vérifier les assets absolus.
3. Configurer les domaines personnalisés depuis Firebase Console, puis recopier exactement les enregistrements DNS demandés chez IONOS (A/AAAA/TXT selon l'assistant). Ne pas supprimer les MX/SPF/DKIM des emails.
4. Rediriger .com vers https://pulse-locale-pme.fr/ (301/308, en conservant les chemins si pertinent).
5. Vérifier HTTPS, navigation, boutique, paiements, authentification, appels API, SEO et redirections.
6. Déployer sur la branche de préparation, puis valider avant fusion dans main.

## Attention
Les domaines personnalisés sont configurés côté Firebase/IONOS, pas uniquement par un changement de firebase.json. Le fragment #materiel n'est pas transmis au serveur : l'ancre doit être gérée côté navigateur. Les domaines info et store doivent afficher leur page dédiée à la racine.
