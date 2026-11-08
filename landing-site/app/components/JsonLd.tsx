import { FOUNDER, ORGANIZATION } from '../seo/seo'

/** Données structurées schema.org d'une page (l'organisation est toujours incluse). */
export function JsonLd({ items }: { items: object[] }) {
  const data = { '@context': 'https://schema.org', '@graph': [ORGANIZATION, FOUNDER, ...items] }
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, '\\u003c') }} />
}
