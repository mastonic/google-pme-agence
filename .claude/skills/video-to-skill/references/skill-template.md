# Template for the generated skill

## SKILL.md

```markdown
---
name: <topic-kebab-case>
description: <Domain> expertise built from <N> videos (<main authors/channels>). Use for <concrete tasks: create X, audit Y, choose Z, write W…>, and whenever the user mentions <keywords and synonyms, in the user's language>.
---

# <Topic>

<2-3 lines: what this skill lets you do and for whom.>

## Core principles
The 5-10 ideas that recur across the most videos, each one stated as a rule.
- **<rule>** — why, and when it applies. [NNN @mm:ss]

## Decision rules
| Situation | Do | Avoid | Source |
|---|---|---|---|

## Workflows
### <Main task 1>
1. … (details: [references/<theme>.md](references/<theme>.md))

## Checklists
- [ ] …

## Points of disagreement between authors
- <subject>: A says … [001], B says … [007]. Use A when …, B when …

## Reference files
- [references/<theme>.md](references/<theme>.md): <what it contains, when to read it>
- [sources.md](sources.md): list of the videos
```

## references/<theme>.md
One file per major theme (for example, for marketing: positioning, offer, copywriting,
paid ads, SEO, social media, emailing, funnel and conversion, analytics and KPIs, budget).
Put the full frameworks there, plus the detailed examples, figures with their
context, scripts and templates to reuse, each with its `[NNN @mm:ss]` sources.
Add a table of contents at the top when a file runs over 100 lines.

## sources.md
| N° | Title | Author | URL | Duration | Main contribution |
|---|---|---|---|---|---|
