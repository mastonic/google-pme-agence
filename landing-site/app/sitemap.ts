import type { MetadataRoute } from 'next'
import { CURRENT_SITE, canonicalUrl, ownerOf } from './seo/domains'
import { PUBLIC_PAGES } from './seo/pages'

export const dynamic = 'force-static'

/** Sitemap du domaine en cours de construction : uniquement ses propres pages canoniques. */
export default function sitemap(): MetadataRoute.Sitemap {
  return PUBLIC_PAGES.filter((p) => ownerOf(p.path) === CURRENT_SITE).map((p) => ({
    url: canonicalUrl(p.path),
    lastModified: p.lastmod,
    changeFrequency: p.changeFrequency,
    priority: p.priority,
  }))
}
