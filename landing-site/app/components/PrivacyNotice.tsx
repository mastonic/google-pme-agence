import { siteHref } from '../seo/domains'

/** Information RGPD affichée sous chaque formulaire (art. 13) : finalité, responsable, durée, droits. */
export function PrivacyNotice({ style }: { style?: React.CSSProperties }) {
  return (
    <p style={{ fontSize: 12, lineHeight: 1.5, color: '#64748B', margin: 0, ...style }}>
      Vos données servent uniquement à traiter votre demande et à vous recontacter à ce sujet. Responsable :
      HoldMasto (Pulse Locale PME). Conservation : 3 ans après notre dernier échange. Hébergement et envoi des
      emails : Google Cloud et IONOS. Vous pouvez accéder à vos données, les rectifier, les effacer ou vous opposer
      à leur traitement en écrivant à contact@pulse-locale-pme.fr. Aucune inscription à une newsletter.{' '}
      <a href={siteHref('/mentions-legales/#rgpd')} style={{ textDecoration: 'underline' }}>En savoir plus</a>
    </p>
  )
}
