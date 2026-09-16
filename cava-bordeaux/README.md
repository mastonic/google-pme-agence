# Cava de Bordeaux — MVP

Boutique en ligne de vins français importés (Bordeaux), vendue depuis Mexico
(CDMX) à des particuliers au Mexique. Pack "Site Essentiel".

## État actuel (phase 1)

- Scaffold Next.js 14 (App Router) + TypeScript + Tailwind CSS
- Firebase configuré (`lib/firebase.ts`) mais **optionnel** : sans clés dans
  `.env.local`, le site tourne avec le catalogue de démonstration
  (`lib/products.ts`, 8 vins réalistes couvrant rouge/blanc/rosé/effervescent)
- Mur de vérification d'âge (18+) avec cookie de session (30 jours),
  `components/AgeGate.tsx`
- Page d'accueil (histoire de la marque + sélection destacada)
- Page Tienda avec filtres couleur / région / prix
- Fiches produit avec accord mets-vin, JSON-LD `schema.org/Product`,
  meta title/description par page
- `sitemap.xml` et `robots.txt` générés automatiquement

**Volontairement hors scope à ce stade** (phase 2, une fois le lien de
preview validé) : panier, checkout, paiement Stripe, comptes clients
(Firebase Auth), pages À propos / Contact / Mentions légales, newsletter.

## Démarrer en local

```bash
cd cava-bordeaux
npm install
npm run dev
```

## Connecter Firebase (quand le vrai catalogue sera prêt)

1. Créer un projet Firebase, activer Firestore.
2. Copier `.env.local.example` vers `.env.local` et renseigner les clés
   `NEXT_PUBLIC_FIREBASE_*`.
3. `isFirebaseConfigured` (dans `lib/firebase.ts`) passera automatiquement à
   `true` — il restera à brancher la lecture du catalogue sur Firestore à la
   place de `lib/products.ts`.

## Note Stripe / Mexique

Stripe accepte aujourd'hui les entreprises basées au Mexique (activation
progressive depuis 2023) ainsi que les entreprises françaises facturant à
l'international. À vérifier au moment du choix définitif : le pays
d'immatriculation légal de l'entité qui vendra (française ou mexicaine)
conditionne quel compte Stripe ouvrir. Si un blocage apparaît à ce moment-là,
Lemon Squeezy reste le plan B mentionné dans le brief. Ce point n'a pas
d'impact sur le scaffold actuel : le checkout et le paiement sont prévus en
phase 2.
