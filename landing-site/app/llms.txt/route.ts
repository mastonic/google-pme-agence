// llms.txt généré au build (même contenu sur les trois domaines, URL canoniques).
import { canonicalUrl } from '../seo/domains'
import { GUIDES } from '../info/guides/guides'
import { ARTICLES, articlePath } from '../info/articles/articles'
import { DEPTS, cityPath } from '../zones/zones'
import { HUBS, hubPath } from '../local/hubs'

export const dynamic = 'force-static'

const HEAD = `# Pulse Locale PME

> Pulse Locale PME (pulse-locale-pme.fr) est un service français, actif notamment dans les Yvelines (78) et en Eure-et-Loir (28), travaillant à distance partout en France, qui crée et fait vivre la présence en ligne des TPE, PME, artisans et commerçants locaux : site internet professionnel, optimisation de la fiche Google Business (Google Maps), avis clients, suivi des appels et WhatsApp, et réceptionniste IA. Une démonstration personnalisée est offerte avant tout paiement. Pulse Locale PME est édité et opéré par HoldMasto, sa maison mère (SASU, RCS Fort-de-France 106 121 536). Contact : contact-plp@holdmasto.fr.

## Domaines officiels

- https://pulse-locale-pme.fr : offre, pages locales Yvelines et Eure-et-Loir, entreprise, mentions légales.
- https://pulse-locale-pme.info : guides, articles, outils gratuits.
- https://pulse-locale-pme.store : boutique et packs.
- https://pulse-locale-pme.com redirige vers https://pulse-locale-pme.fr.

## À qui s'adresse Pulse Locale PME

- Artisans (plombiers, électriciens, chauffagistes, serruriers), commerces de proximité, restaurants, coiffeurs, esthéticiennes, garages, taxis/VTC, kinés, agences immobilières.
- Entreprises locales en France qui veulent être trouvées sur Google Maps et dans les assistants IA (ChatGPT, Gemini) sans gérer la technique.

## Abonnements (prix HT, sans frais de création)

Paiement mensuel sans engagement, ou annuel avec 2 mois offerts (10 mois facturés pour 12).

- Starter : 49 € HT/mois (490 € HT/an). Site vitrine jusqu'à 5 pages, hébergement, SSL, maintenance, 1 modification par mois.
- Pro : 149 € HT/mois (1 490 € HT/an). Starter + nom de domaine, SEO local, optimisation de la fiche Google Business, suivi des appels et demandes, 3 modifications par mois.
- Élite : 299 € HT/mois (2 990 € HT/an). Pro + réceptionniste IA incluse, minimum garanti de 4 contenus SEO et 4 publications Google par mois, chatbot IA / assistant WhatsApp, automatisation des demandes d'avis, jusqu'à 10 modifications par mois.
- Réceptionniste IA : répond aux appels manqués et aux messages WhatsApp au nom de l'entreprise, qualifie la demande et envoie un résumé par WhatsApp ou SMS. Essai gratuit de 30 jours dans la limite de 60 appels, puis 39 € HT/mois avec 100 appels inclus et 0,83 € HT (1 € TTC) par appel supplémentaire ; incluse dans Élite.
- Pack Connecté : 19 € HT/mois (inclus dans Élite, offert pendant l'essai de la réceptionniste). La réceptionniste réserve les rendez-vous dans Google Agenda sur les créneaux réellement libres, ajoute chaque appel à un tableur Google Sheets et peut envoyer chaque appel vers Zapier, Make ou toute application via webhook.

## Packs à prix fixe (boutique, prix HT)

- Fiche Google optimisée : 149 € HT, livrée en 5 jours ouvrés (catégories, description locale, 10 photos, services, 4 posts, rapport avant/après). Déduit du premier mois en cas de passage en formule Pro dans les 30 jours.
- Pack 50 avis : 99 € HT (campagne SMS + QR code, relance automatique).
- Audit visibilité IA : 99 € HT (appel de 20 min avec un expert, test sur Google Maps, ChatGPT et Gemini, comparaison avec 3 concurrents, plan d'action).
- Matériel avis : plaque NFC 39 €, kit 20 stickers QR 29 €, chevalet de comptoir 24 €.

`

export function GET() {
  const u = canonicalUrl
  const lines = [
    HEAD.trimEnd(),
    '',
    '## Pages principales',
    '',
    `- [Accueil](${u('/')}) : offre, fonctionnement, tarifs, FAQ.`,
    `- [Méthode](${u('/methode/')}) : audit, optimisation, contenus, suivi, sans promesse de position.`,
    `- [Qui sommes-nous](${u('/a-propos/')}) : HoldMasto, marque Pulse Locale PME, fondateur, engagements.`,
    `- [Boutique](${u('/store/')}) : packs à prix fixe et matériel avis.`,
    `- [Fiche Google optimisée](${u('/store/fiche-google-optimisee/')}) : pack à 149 € HT.`,
    `- [Ressources](${u('/info/')}) : guides, articles, outils.`,
    `- [SEO, AEO et GEO](${u('/info/seo-aeo-geo/')}) : guide de référence.`,
    `- [Test de visibilité gratuit](${u('/info/outil-gratuit/')}) : score sur 100 en 8 questions.`,
    `- [Guide PDF gratuit](${u('/info/guide-gratuit/')}) : les 10 erreurs qui cachent un commerce sur Google.`,
    `- [Mentions légales, CGV, RGPD](${u('/mentions-legales/')})`,
    '',
    '## Pages locales',
    '',
    ...HUBS.map((h) => `- [${h.region}](${u(hubPath(h))}) : ${h.description}`),
    ...DEPTS.flatMap((d) => d.cities.map((c) => `  - [${c.name}](${u(cityPath(d, c))})`)),
    '',
    '## Articles',
    '',
    ...ARTICLES.map((a) => `- [${a.title}](${u(articlePath(a.slug))}) : ${a.description}`),
    `- [ChatGPT, Gemini et commerces locaux](${u('/info/actus/chatgpt-gemini-commerces-locaux/')})`,
    '',
    '## Guides par métier',
    '',
    `- [Tous les guides](${u('/info/guides/')})`,
    ...GUIDES.map((g) => `- [Guide ${g.metier.toLowerCase()}](${u(`/info/guides/${g.slug}/`)}) : ${g.card}`),
    '',
    '## Auteur',
    '',
    `- [Ludovic Rigah](${u('/info/auteur/ludovic-rigah/')}) : président de HoldMasto et fondateur de Pulse Locale PME, auteur des contenus.`,
    '',
  ]
  return new Response(lines.join('\n'), { headers: { 'Content-Type': 'text/plain; charset=utf-8' } })
}
