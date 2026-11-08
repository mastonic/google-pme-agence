import { AUTHOR_PATH } from '../seo/seo'
import { siteHref } from '../seo/domains'

/** Signature des contenus : renvoie vers la page auteur (signal E-E-A-T pour Google et les IA). */
export function Byline() {
  return (
    <span>
      Par <a href={siteHref(AUTHOR_PATH)} rel="author" className="link-underline">Ludovic Rigah</a>, fondateur de Pulse Locale PME
    </span>
  )
}
