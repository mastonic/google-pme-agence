import type { Metadata } from 'next'
import { AUTHOR_PATH, abs, breadcrumbs, ORG_ID, pageMeta } from '../seo/seo'
import { siteHref } from '../seo/domains'
import { JsonLd } from '../components/JsonLd'
import { OrderButton } from '../components/OrderButton'
import { Testimonials } from '../components/Proof'
import { SubShell } from '../components/SubShell'
import { CONTACT_EMAIL } from '../components/contact'

const PATH = '/a-propos/'
const TITLE = 'Qui sommes-nous : HoldMasto et la marque Pulse Locale PME'
const DESC = 'Pulse Locale PME est une marque de HoldMasto (SASU, RCS Fort-de-France 106 121 536) : identité, fondateur, engagements, coordonnées et zones d’intervention.'

export const metadata: Metadata = pageMeta({ title: TITLE, description: DESC, path: PATH })

export default function APropos() {
  return (
    <SubShell variant="main">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Qui sommes-nous', PATH]]),
          { '@type': 'AboutPage', '@id': abs(PATH) + '#page', url: abs(PATH), name: TITLE, inLanguage: 'fr-FR', about: { '@id': ORG_ID } },
        ]}
      />
      <article className="article">
        <p className="crumbs"><a href={siteHref('/')}>Accueil</a> / Qui sommes-nous</p>
        <span className="eyebrow">Qui sommes-nous</span>
        <h1>Pulse Locale PME, une marque de HoldMasto</h1>
        <div className="callout" role="note">
          <strong className="mont">En bref</strong>
          <p>Pulse Locale PME est la marque commerciale de HoldMasto, SASU immatriculée au RCS de Fort-de-France sous le numéro 106 121 536 et présidée par Ludovic Rigah. Elle crée des sites internet, optimise les fiches Google et propose une réceptionniste IA aux artisans, commerçants et TPE, notamment dans les Yvelines (78) et en Eure-et-Loir (28), en travaillant à distance.</p>
        </div>

        <h2>L’entité juridique et la marque</h2>
        <ul>
          <li><strong>Société</strong> : HoldMasto, SASU, RCS Fort-de-France 106 121 536.</li>
          <li><strong>Siège</strong> : 2 Impasse Bacouna, 97231 Le Robert, France.</li>
          <li><strong>Président</strong> : <a href={siteHref(AUTHOR_PATH)} className="link-underline">Ludovic Rigah</a>, fondateur de Pulse Locale PME.</li>
          <li><strong>Marque</strong> : Pulse Locale PME, sites pulse-locale-pme.fr (offre), pulse-locale-pme.info (ressources) et pulse-locale-pme.store (boutique).</li>
          <li><strong>Contact</strong> : {CONTACT_EMAIL}</li>
        </ul>

        <h2>Ce que nous faisons</h2>
        <p>Sites internet en abonnement, optimisation de fiches Google Business Profile, référencement local, contenus, suivi des appels et demandes, et réceptionniste IA. Les tarifs sont publics : dès 49 € HT par mois, sans engagement en mensuel. <a href={siteHref('/#offres')} className="link-underline">Voir les formules</a> · <a href={siteHref('/store/')} className="link-underline">Voir la boutique</a>.</p>

        <h2>Où nous intervenons</h2>
        <p>Nous accompagnons les entreprises de toute la France, à distance, avec des pages dédiées aux <a href={siteHref('/agence-seo-local-yvelines/')} className="link-underline">Yvelines</a> et à l’<a href={siteHref('/agence-seo-local-eure-et-loir/')} className="link-underline">Eure-et-Loir</a>. Nous n’avons pas de bureau dans ces départements et nous ne revendiquons aucune adresse locale.</p>

        <h2>Nos engagements</h2>
        <ul>
          <li>Une démonstration de votre site avant tout paiement.</li>
          <li>Des prix affichés hors taxes, sans frais cachés, conditions présentées avant paiement.</li>
          <li>Aucune promesse de position Google ni de recommandation par une IA.</li>
          <li>Aucun faux avis, aucune contrepartie contre des avis.</li>
          <li>Votre fiche Google, votre domaine et vos contenus restent à vous.</li>
        </ul>

        <Testimonials />

        <h2>Conditions et données</h2>
        <p>Mentions légales, conditions générales de vente et d’utilisation, politique de confidentialité : <a href={siteHref('/mentions-legales/')} className="link-underline">consulter les informations légales</a>.</p>

        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>Une question sur la société ?</strong>
          <p>Écrivez-nous, réponse sous 24 h ouvrées.</p>
          <div className="hero-ctas">
            <OrderButton product="Question à HoldMasto (page à propos)" source="contact" title="Poser une question" phoneRequired={false} submitLabel="Envoyer →" className="btn btn-primary btn-sm">Nous écrire →</OrderButton>
          </div>
        </div>
      </article>
    </SubShell>
  )
}
