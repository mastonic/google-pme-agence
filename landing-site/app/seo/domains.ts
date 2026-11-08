// Architecture multi-domaines de Pulse Locale PME : une seule base de code, trois sites Firebase.
// Chaque page publique appartient à UN domaine (son « propriétaire »). La canonique, le sitemap
// et les liens internes sont calculés à partir de cette règle, pour qu'aucun domaine n'indexe
// une copie des pages d'un autre.
//
//   pulse-locale-pme.fr     → accueil, offres, pages locales 78 / 28, entreprise, légal
//   pulse-locale-pme.info   → tout ce qui est sous /info/ (guides, articles, outils, auteur)
//   pulse-locale-pme.store  → tout ce qui est sous /store/ (boutique, packs)
//   pulse-locale-pme.com    → redirection 301 vers .fr (gérée côté Firebase / IONOS, pas ici)

export type SiteKey = 'fr' | 'info' | 'store'

export const ORIGINS: Record<SiteKey, string> = {
  fr: 'https://pulse-locale-pme.fr',
  info: 'https://pulse-locale-pme.info',
  store: 'https://pulse-locale-pme.store',
}

/** Préfixe de chemin réservé à chaque domaine secondaire (le reste appartient au .fr). */
export const SECTION: Record<Exclude<SiteKey, 'fr'>, string> = { info: '/info/', store: '/store/' }

/** Domaine propriétaire d'un chemin (sans tenir compte de l'ancre ni de la query). */
export function ownerOf(path: string): SiteKey {
  const p = path.split(/[?#]/)[0] || '/'
  if (p === '/info' || p.startsWith('/info/')) return 'info'
  if (p === '/store' || p.startsWith('/store/')) return 'store'
  return 'fr'
}

/**
 * Site en cours de construction. Chaque domaine est construit séparément :
 *   NEXT_PUBLIC_SITE=info|store|fr (prioritaire), sinon déduit de NEXT_PUBLIC_SITE_URL.
 * Par défaut : le site principal .fr.
 */
function resolveSite(): SiteKey {
  const explicit = process.env.NEXT_PUBLIC_SITE
  if (explicit === 'fr' || explicit === 'info' || explicit === 'store') return explicit
  const url = process.env.NEXT_PUBLIC_SITE_URL || ''
  if (/pulse-locale-pme\.info|pulse-locale-info/.test(url)) return 'info'
  if (/pulse-locale-pme\.store|pulse-locale-store/.test(url)) return 'store'
  return 'fr'
}

export const CURRENT_SITE: SiteKey = resolveSite()
export const CURRENT_ORIGIN = ORIGINS[CURRENT_SITE]

/** URL canonique absolue d'un chemin : toujours sur le domaine propriétaire. */
export const canonicalUrl = (path: string) => ORIGINS[ownerOf(path)] + path

/**
 * Lien interne : relatif si la page cible appartient au site en cours, absolu vers le bon
 * domaine sinon. La valeur est figée au build (variable NEXT_PUBLIC_*), donc identique côté
 * serveur et navigateur : aucune différence d'hydratation.
 */
export function siteHref(path: string): string {
  if (!path.startsWith('/') || path.startsWith('//')) return path
  const owner = ownerOf(path)
  return owner === CURRENT_SITE ? path : ORIGINS[owner] + path
}
