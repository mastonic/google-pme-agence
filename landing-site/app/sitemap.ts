import type { MetadataRoute } from 'next'
import { abs } from './seo/seo'
import { GUIDES } from './info/guides/guides'
import { DEPTS, cityPath, deptPath } from './zones/zones'

export const dynamic = 'force-static'

const PAGES: [string, number, MetadataRoute.Sitemap[number]['changeFrequency']][] = [
  ['/', 1, 'weekly'],
  ['/store/', 0.9, 'weekly'],
  ['/store/fiche-google-optimisee/', 0.8, 'monthly'],
  ['/info/', 0.8, 'weekly'],
  ['/info/outil-gratuit/', 0.8, 'monthly'],
  ['/info/guide-gratuit/', 0.7, 'monthly'],
  ['/info/guides/', 0.8, 'monthly'],
  ...GUIDES.map((g) => [`/info/guides/${g.slug}/`, 0.7, 'monthly'] as [string, number, 'monthly']),
  ['/info/auteur/ludovic-rigah/', 0.5, 'monthly'],
  ['/zones/', 0.7, 'monthly'],
  ...DEPTS.flatMap((d) => [[deptPath(d), 0.8, 'monthly'] as [string, number, 'monthly'], ...d.cities.map((c) => [cityPath(d, c), 0.7, 'monthly'] as [string, number, 'monthly'])]),
  ['/info/actus/chatgpt-gemini-commerces-locaux/', 0.6, 'monthly'],
  ['/mentions-legales/', 0.2, 'yearly'],
]

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date()
  return PAGES.map(([path, priority, changeFrequency]) => ({ url: abs(path), lastModified, priority, changeFrequency }))
}
