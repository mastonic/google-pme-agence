import { AUTHOR_PATH } from '../seo/seo'

/** Signature des contenus : renvoie vers la page auteur (signal E-E-A-T pour Google et les IA). */
export function Byline() {
  return (
    <span>
      Par <a href={AUTHOR_PATH} rel="author" className="link-underline">Ludovic Rigah</a>, fondateur de Pulse Locale PME
    </span>
  )
}
