import type { MetadataRoute } from 'next'
import { abs } from './seo/seo'

export const dynamic = 'force-static'

const PAGES: [string, number, MetadataRoute.Sitemap[number]['changeFrequency']][] = [
  ['/', 1, 'weekly'],
  ['/store/', 0.9, 'weekly'],
  ['/store/fiche-google-optimisee/', 0.8, 'monthly'],
  ['/info/', 0.8, 'weekly'],
  ['/info/outil-gratuit/', 0.8, 'monthly'],
  ['/info/guide-gratuit/', 0.7, 'monthly'],
  ['/info/guides/plombier/', 0.7, 'monthly'],
  ['/info/actus/chatgpt-gemini-commerces-locaux/', 0.6, 'monthly'],
  ['/mentions-legales/', 0.2, 'yearly'],
]

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date()
  return PAGES.map(([path, priority, changeFrequency]) => ({ url: abs(path), lastModified, priority, changeFrequency }))
}
