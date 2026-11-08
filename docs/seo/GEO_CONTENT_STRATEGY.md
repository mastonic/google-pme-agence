# Stratégie de contenus GEO / AEO

## Principes appliqués

1. Réponse directe de 40 à 80 mots en tête de chaque article (« La réponse courte »).
2. Sommaire, H2 explicites (souvent des questions), tableaux pour les comparaisons.
3. Faits datés et sourcés ; sources officielles (Google, OpenAI, Perplexity, Anthropic, CNIL, EUR-Lex) listées en fin d'article et dans `citation` (JSON-LD).
4. Auteur identifié (Ludovic Rigah, `Person`), éditeur (HoldMasto, `Organization`), dates `datePublished` / `dateModified` réelles.
5. Aucune promesse de position ni de citation par une IA. Aucune statistique inventée.
6. Tarifs issus d'une source unique (`landing-site/app/seo/offers.ts`).

## Contenus publiés (.info)

| URL | Mot-clé | Sources principales |
|---|---|---|
| `/info/articles/prix-site-internet-artisan-yvelines/` | prix site internet artisan Yvelines | Offres publiques datées (Web Ranker, Dix Mille Heures, Refonte Up), Google |
| `/info/articles/visibilite-google-maps-chartres/` | visibilité Google Maps Chartres | Aide Google Business Profile (classement local, consignes, zone de service, avis) |
| `/info/articles/choisir-agence-seo-local-yvelines/` | agence SEO local Yvelines | Google « Do you need an SEO? », Search Essentials |
| `/info/articles/apparaitre-chatgpt-gemini-perplexity/` | apparaître dans ChatGPT | Google AI features, OpenAI / Perplexity / Anthropic bots, Bing |
| `/info/articles/prix-optimisation-fiche-google-business-profile/` | prix optimisation fiche Google | Google, Web Ranker, ComeUp |
| `/info/articles/receptionniste-ia-artisan/` | réceptionniste IA artisan | CGV/RGPD Pulse Locale PME, CNIL, règlement (UE) 2024/1689 |
| `/info/seo-aeo-geo/` | SEO AEO GEO | 10 sources officielles, glossaire `DefinedTermSet` |

## Mise à jour

- Modifier `modified` dans `app/info/articles/articles.ts` **uniquement** si le contenu change (le sitemap et le JSON-LD suivent).
- Re-vérifier tous les 6 mois les prix publics cités et les documentations des robots IA.

## Prochains contenus suggérés

Questions issues du suivi GEO (`geo-monitoring/questions.json`) sans réponse satisfaisante : une page par question fréquente, avec réponse directe et sources.
