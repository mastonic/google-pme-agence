# Google Search Console et Bing Webmaster Tools

> Aucun accès à ces outils n'a été utilisé : les domaines **ne sont pas** confirmés comme vérifiés. Toutes les étapes ci-dessous sont à réaliser par le propriétaire.

## Google Search Console

1. https://search.google.com/search-console → « Ajouter une propriété » → **Domaine** : `pulse-locale-pme.fr`, puis `pulse-locale-pme.info`, puis `pulse-locale-pme.store` (une propriété « Domaine » couvre http/https et sous-domaines).
2. Vérification par enregistrement **TXT** chez IONOS (DNS du domaine). Ne pas toucher aux enregistrements A/AAAA, MX, SPF, DKIM existants.
3. Soumettre un sitemap par propriété (Indexation → Sitemaps) :
   - `https://pulse-locale-pme.fr/sitemap.xml`
   - `https://pulse-locale-pme.info/sitemap.xml`
   - `https://pulse-locale-pme.store/sitemap.xml`
4. Inspection d'URL : demander l'indexation de l'accueil, des deux pages piliers et de `/info/seo-aeo-geo/`.
5. Optionnel : propriété `pulse-locale-pme.com` pour suivre les redirections.

## Bing Webmaster Tools (Bing, Copilot)

1. https://www.bing.com/webmasters → importer les propriétés depuis Search Console (le plus simple) ou vérifier par TXT/CNAME.
2. Soumettre les trois sitemaps.

## Contrôles mensuels

| Contrôle | Où | Seuil d'alerte |
|---|---|---|
| Pages indexées par domaine | GSC → Pages | Page de sitemap « Explorée, non indexée » ou « Dupliquée » |
| Canonique choisie par Google | GSC → Inspection d'URL | Canonique Google ≠ canonique déclarée |
| Impressions / clics organiques | GSC → Performances (type « Web », inclut les fonctionnalités IA de Google) | Baisse > 30 % sur 28 jours |
| Requêtes locales | GSC → Performances → filtre requête contient « yvelines », « versailles », « chartres », « dreux »… | — |
| Erreurs d'exploration | GSC → Paramètres → Statistiques d'exploration ; Bing → Site Explorer | Hausse des 4xx/5xx |
| Redirections | `curl -I https://pulse-locale-pme.info/agence-seo-local-yvelines/` → 301 vers .fr | Autre code |

## Fichier de reporting

Remplir `docs/seo/geo-monitoring/search-console-report.csv` chaque mois (une ligne par domaine).
