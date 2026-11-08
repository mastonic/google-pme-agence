import type { Metadata } from 'next'

/** URL canonique du site. Passer NEXT_PUBLIC_SITE_URL=https://pulse-locale-pme.fr quand le domaine pointe sur Firebase. */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || 'https://pme-local-pulse.web.app').replace(/\/$/, '')
export const BRAND = 'Pulse Locale PME'
export const OG_IMAGE = '/og-pulse-pro.png'
export const abs = (path: string) => SITE_URL + path

/** Métadonnées complètes d'une page (title, description, canonical, Open Graph, Twitter). */
export function pageMeta({ title, description, path, type = 'website' }: { title: string; description: string; path: string; type?: 'website' | 'article' }): Metadata {
  return {
    title,
    description,
    alternates: { canonical: path },
    openGraph: { type, locale: 'fr_FR', url: path, siteName: BRAND, title, description, images: [{ url: OG_IMAGE, width: 1200, height: 630, alt: title }] },
    twitter: { card: 'summary_large_image', title, description, images: [OG_IMAGE] },
  }
}

export const ORG_ID = abs('/#organisation')

/** Fondateur et auteur des contenus (E-E-A-T : une personne identifiée signe les guides). */
export const AUTHOR_PATH = '/info/auteur/ludovic-rigah/'
export const FOUNDER_ID = abs(AUTHOR_PATH + '#personne')
export const FOUNDER = {
  '@type': 'Person',
  '@id': FOUNDER_ID,
  name: 'Ludovic Rigah',
  jobTitle: 'Président et fondateur',
  url: abs(AUTHOR_PATH),
  worksFor: { '@id': ORG_ID },
  knowsAbout: ['Référencement local', 'Google Business Profile', 'Google Maps', 'Visibilité dans les assistants IA', 'Réceptionniste IA'],
}

export const ORGANIZATION = {
  '@type': 'Organization',
  '@id': ORG_ID,
  name: 'HoldMasto',
  brand: { '@type': 'Brand', name: BRAND },
  url: abs('/'),
  logo: abs('/icon.svg'),
  identifier: 'RCS Fort-de-France 106 121 536',
  email: 'contact-plp@holdmasto.fr',
  areaServed: { '@type': 'Country', name: 'France' },
  founder: { '@id': FOUNDER_ID },
  sameAs: ['https://holdmasto.fr'],
  contactPoint: { '@type': 'ContactPoint', contactType: 'customer service', email: 'contact-plp@holdmasto.fr', availableLanguage: 'fr' },
}

export function breadcrumbs(items: [string, string][]) {
  return {
    '@type': 'BreadcrumbList',
    itemListElement: items.map(([name, path], i) => ({ '@type': 'ListItem', position: i + 1, name, item: abs(path) })),
  }
}

export function article({ path, title, description, published, section, modified, about }: { path: string; title: string; description: string; published: string; section: string; modified?: string; about?: string }) {
  return {
    '@type': 'Article',
    '@id': abs(path) + '#article',
    mainEntityOfPage: abs(path),
    headline: title,
    description,
    inLanguage: 'fr-FR',
    articleSection: section,
    datePublished: published,
    dateModified: modified || published,
    ...(about ? { about: { '@type': 'Thing', name: about }, audience: { '@type': 'BusinessAudience', audienceType: about } } : {}),
    image: abs(OG_IMAGE),
    author: { '@id': FOUNDER_ID },
    publisher: { '@id': ORG_ID },
  }
}

export function faqPage(faqs: [string, string][]) {
  return {
    '@type': 'FAQPage',
    mainEntity: faqs.map(([q, a]) => ({ '@type': 'Question', name: q, acceptedAnswer: { '@type': 'Answer', text: a } })),
  }
}


/** Étapes d'un guide (HowTo) : aide Google et les assistants IA à extraire la marche à suivre. */
export function howTo({ path, name, steps }: { path: string; name: string; steps: [string, string][] }) {
  return {
    '@type': 'HowTo',
    '@id': abs(path) + '#howto',
    name,
    inLanguage: 'fr-FR',
    step: steps.map(([title, text], i) => ({ '@type': 'HowToStep', position: i + 1, name: title, text, url: abs(path) + '#etape-' + (i + 1) })),
  }
}

export function itemList(name: string, items: [string, string][]) {
  return {
    '@type': 'ItemList',
    name,
    itemListElement: items.map(([n, path], i) => ({ '@type': 'ListItem', position: i + 1, name: n, url: abs(path) })),
  }
}

/** Service rendu sur une zone géographique (pages locales) : zones desservies sans adresse fictive. */
export function localService({ path, name, description, areas, region }: { path: string; name: string; description: string; areas: string[]; region: string }) {
  return {
    '@type': 'Service',
    '@id': abs(path) + '#service',
    name,
    description,
    serviceType: 'Visibilité locale : fiche Google, site internet, avis et réceptionniste IA',
    provider: { '@id': ORG_ID },
    url: abs(path),
    areaServed: areas.map((n) => ({ '@type': 'City', name: n, containedInPlace: { '@type': 'AdministrativeArea', name: region } })),
    audience: { '@type': 'BusinessAudience', audienceType: 'Artisans, commerçants et TPE' },
    offers: { '@type': 'Offer', price: '49', priceCurrency: 'EUR', description: 'À partir de 49 € HT par mois, sans engagement', url: abs('/#offres') },
  }
}
