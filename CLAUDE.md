# CLAUDE.md

## Extraction de données web — skills toujours actifs

Trois skills sont installés dans `.claude/skills/`. Si un outil manque, l'installer
avant usage (hors du dépôt) :

```bash
pip install https://github.com/Panniantong/agent-reach/archive/main.zip   # agent-reach
pip install "scrapling[fetchers]>=0.4.15"                                  # scrapling
pip install patchright                                                     # patchright
```

Dès qu'une tâche demande de chercher, lire, surveiller ou extraire des données
sur internet, utilise-les systématiquement au lieu d'improviser :

| Besoin | Skill |
|---|---|
| X/Twitter, YouTube, Reddit, GitHub, LinkedIn, RSS, recherche web | `agent-reach` |
| N'importe quelle page web, protections anti-bot, crawl de plusieurs pages | `scrapling` |
| Site sans API dont les données sont chargées en JS (capturer ses requêtes réseau) | `patchright` |

Méthode : l'utilisateur dit quelles données il veut → écrire le script → collecter →
livrer un résultat structuré + une synthèse (thèmes, plaintes récurrentes, tendances…).

Règles :
- Fichiers temporaires et exports dans `/tmp/`, jamais dans le dépôt.
- Lecture seule : ne rien publier, liker ou poster sans demande explicite.
- Rester raisonnable en volume et en fréquence ; respecter les CGU des sites et le RGPD.
