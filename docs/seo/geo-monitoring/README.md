# Suivi de la visibilité dans les assistants IA (GEO)

## Fichiers

- `questions.json` : 20 questions représentatives (zones 78 / 28, national, marque). Ne pas les modifier d'un mois à l'autre pour garder des séries comparables ; en ajouter plutôt.
- `results-template.csv` : modèle d'enregistrement. Copier en `results-AAAA-MM.csv` chaque mois.
- `search-console-report.csv` : reporting mensuel Search Console / Bing (voir `../SEARCH_CONSOLE_SETUP.md`).

## Protocole (manuel, sans automatisation)

1. Une fois par mois, même semaine.
2. Assistants : ChatGPT (recherche activée), Gemini, Perplexity, Claude (recherche activée), Copilot, Google (mode IA / aperçu IA si affiché).
3. Navigation privée, sans être connecté au compte de l'entreprise si possible ; noter la ville d'où le test est fait.
4. Poser chaque question telle quelle. Enregistrer : date, assistant, modèle / mode, présence de Pulse Locale PME (oui / non), URL citée, position (1er, 2e… ou « mentionné sans lien »), concurrents cités, commentaire.
5. **N'inventer aucun résultat** : laisser vide si le test n'a pas été fait.

## Lecture

- Indicateur principal : part des questions où Pulse Locale PME est citée **avec une URL** du site.
- Comparer les mois entre eux, jamais un seul test : les réponses varient selon le moment, le mode et la formulation.

## Automatisation (optionnelle, non mise en place)

Une automatisation n'est envisageable que via des **API officielles** (par exemple les API de recherche web proposées par les éditeurs), dans le respect de leurs conditions d'utilisation, avec un budget plafonné et validé au préalable. Ne pas automatiser les interfaces grand public (scraping), ce qui contreviendrait aux conditions d'utilisation. Architecture possible : tâche mensuelle (Cloud Scheduler → Cloud Run) qui lit `questions.json`, appelle les API autorisées, écrit un CSV dans Cloud Storage. Non implémentée : aucune dépense automatique.
