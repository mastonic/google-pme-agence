# SEO local Yvelines (78) et Eure-et-Loir (28)

## Positionnement

Pulse Locale PME travaille **à distance** : aucune adresse locale n'est revendiquée. Les zones sont déclarées via `areaServed` (Service / Organization), jamais via un `LocalBusiness` à adresse fictive. Pas de `AggregateRating`.

## Pages

| URL | Title | Mot-clé principal |
|---|---|---|
| `https://pulse-locale-pme.fr/` | Pulse Locale PME \| Sites web, SEO local et IA dans le 78 et le 28 | site internet artisan 78 28 |
| `/agence-seo-local-yvelines/` | SEO local et création de sites dans les Yvelines (78) \| Pulse Locale PME | SEO local Yvelines |
| `/agence-seo-local-eure-et-loir/` | SEO local et création de sites en Eure-et-Loir (28) \| Pulse Locale PME | SEO local Eure-et-Loir |
| `/zones/yvelines/{versailles, saint-quentin-en-yvelines, saint-germain-en-laye, poissy, mantes-la-jolie, rambouillet}/` | Fiche Google et réceptionniste IA à {ville} | fiche Google {ville} |
| `/zones/eure-et-loir/{chartres, dreux, chateaudun, nogent-le-rotrou}/` | idem | fiche Google {ville} |
| `/zones/` | Zones desservies : Yvelines (78) et Eure-et-Loir (28) | — |

Les anciennes pages département `/zones/yvelines/` et `/zones/eure-et-loir/` (jamais mises en production) sont remplacées par les pages piliers.

## Différenciation éditoriale 78 / 28

- **Yvelines** : concurrence dense dans les pôles (Versailles, Saint-Germain), recherches par commune de l'agglomération de Saint-Quentin, visibilité « à 5 km ».
- **Eure-et-Loir** : couverture des communes rurales (Beauce, Perche, Dunois), fiches non revendiquées, clientèle mixte habitants / visiteurs, limites départementales (Eure, Orne, Sarthe).

## Maillage

Accueil → pages piliers → pages villes → guides métier (.info) / pack Fiche Google (.store) / méthode. Chaque page ville renvoie vers sa page pilier (fil d'Ariane) et vers les villes voisines.

## Données structurées

`Organization` (HoldMasto, `alternateName` Pulse Locale PME, adresse légale réelle, `areaServed` 78 / 28 / France, `founder`), `Service` + `OfferCatalog` (prix réels de `app/seo/offers.ts`), `BreadcrumbList`, `FAQPage`, `WebPage`.

## Actions manuelles

- Fiche Google Business Profile de Pulse Locale PME : **à ne créer que si l'éligibilité est vérifiée** (établissement réel avec contact en personne ou zone de service réelle). En l'état (travail à distance, siège en Martinique), l'éligibilité pour les Yvelines / l'Eure-et-Loir n'est pas établie. À VALIDER.
- Citations locales : voir `local-citations-plan.md`.
