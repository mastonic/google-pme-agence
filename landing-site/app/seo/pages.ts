// Registre des pages publiques indexables, avec leur date de dernière modification réelle
// (date du contenu, pas date du build). Source unique pour les sitemaps des trois domaines.
// N'y figurent ni l'admin, ni le cockpit (/app), ni l'espace client (/espace), ni les routes API.

import { GUIDES, UPDATED as GUIDES_UPDATED } from '../info/guides/guides'
import { ARTICLES, articlePath } from '../info/articles/articles'
import { DEPTS, ZONES_UPDATED, cityPath } from '../zones/zones'
import { HUBS, HUB_UPDATED, hubPath } from '../local/hubs'

export type PublicPage = { path: string; lastmod: string; priority: number; changeFrequency: 'weekly' | 'monthly' | 'yearly' }

const D = '2026-11-08' // dernière révision des pages statiques ci-dessous

export const PUBLIC_PAGES: PublicPage[] = [
  // pulse-locale-pme.fr
  { path: '/', lastmod: D, priority: 1, changeFrequency: 'weekly' },
  ...HUBS.map((h) => ({ path: hubPath(h), lastmod: HUB_UPDATED, priority: 0.9, changeFrequency: 'monthly' as const })),
  ...DEPTS.flatMap((d) => d.cities.map((c) => ({ path: cityPath(d, c), lastmod: ZONES_UPDATED, priority: 0.7, changeFrequency: 'monthly' as const }))),
  { path: '/zones/', lastmod: ZONES_UPDATED, priority: 0.6, changeFrequency: 'monthly' },
  { path: '/methode/', lastmod: D, priority: 0.6, changeFrequency: 'monthly' },
  { path: '/a-propos/', lastmod: D, priority: 0.5, changeFrequency: 'yearly' },
  { path: '/mentions-legales/', lastmod: D, priority: 0.2, changeFrequency: 'yearly' },
  // pulse-locale-pme.store
  { path: '/store/', lastmod: D, priority: 1, changeFrequency: 'weekly' },
  { path: '/store/fiche-google-optimisee/', lastmod: D, priority: 0.9, changeFrequency: 'monthly' },
  // pulse-locale-pme.info
  { path: '/info/', lastmod: D, priority: 1, changeFrequency: 'weekly' },
  { path: '/info/seo-aeo-geo/', lastmod: D, priority: 0.9, changeFrequency: 'monthly' },
  { path: '/info/articles/', lastmod: D, priority: 0.8, changeFrequency: 'weekly' },
  ...ARTICLES.map((a) => ({ path: articlePath(a.slug), lastmod: a.modified, priority: 0.8, changeFrequency: 'monthly' as const })),
  { path: '/info/outil-gratuit/', lastmod: D, priority: 0.8, changeFrequency: 'monthly' },
  { path: '/info/guide-gratuit/', lastmod: D, priority: 0.7, changeFrequency: 'monthly' },
  { path: '/info/guides/', lastmod: GUIDES_UPDATED, priority: 0.8, changeFrequency: 'monthly' },
  ...GUIDES.map((g) => ({ path: `/info/guides/${g.slug}/`, lastmod: GUIDES_UPDATED, priority: 0.7, changeFrequency: 'monthly' as const })),
  { path: '/info/actus/chatgpt-gemini-commerces-locaux/', lastmod: '2026-11-07', priority: 0.6, changeFrequency: 'monthly' },
  { path: '/info/auteur/ludovic-rigah/', lastmod: D, priority: 0.4, changeFrequency: 'yearly' },
]
