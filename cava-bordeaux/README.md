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
- Identité visuelle réelle : logo et photo d'équipe (salon du vin, drapeau
  français) extraits des publications Instagram de la marque
  (`public/brand/`), section de crédibilité B2B/B2C sur l'accueil, CTA
  "Para negocios" pour les demandes de cotisation en gros
- Motion design fonctionnel (`motion`/Framer Motion, GSAP + ScrollTrigger,
  Lenis) : un seul moment signature (titre du hero qui se compose au
  chargement), reveal en stagger des grilles produits à l'entrée dans le
  viewport, header qui se contracte au scroll, léger parallax sur la photo
  de la feria, micro-interaction hover sur les cartes produit. `Lenis` est
  synchronisé au ticker GSAP pour que `ScrollTrigger` reste cohérent.
  `prefers-reduced-motion` est respecté partout (`useReducedMotion`,
  classes `motion-safe:`/`motion-reduce:`, et Lenis/ScrollTrigger ne
  s'initialisent pas du tout) ; aucun `pin` GSAP n'est utilisé (pas de
  scroll-jacking).

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
