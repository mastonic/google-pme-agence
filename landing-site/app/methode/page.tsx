import type { Metadata } from 'next'
import { abs, breadcrumbs, howTo, pageMeta } from '../seo/seo'
import { siteHref } from '../seo/domains'
import { JsonLd } from '../components/JsonLd'
import { OrderButton } from '../components/OrderButton'
import { CaseStudies } from '../components/Proof'
import { SubShell } from '../components/SubShell'

const PATH = '/methode/'
const TITLE = 'Notre méthode : SEO local, fiche Google et visibilité IA'
const DESC = 'Audit, recherches clients, optimisation technique et locale, contenus, suivi des demandes et de la visibilité IA : la méthode Pulse Locale PME.'

export const metadata: Metadata = pageMeta({ title: TITLE, description: DESC, path: PATH })

const STEPS: [string, string, string][] = [
  ['audit', 'Audit initial', 'On examine votre fiche Google, votre site s’il existe, vos informations sur les annuaires et les entreprises qui sortent devant vous sur vos recherches principales. Le test de visibilité gratuit en donne un premier aperçu.'],
  ['recherches', 'Analyse des recherches', 'On liste les recherches réelles de vos clients (« plombier urgence Versailles », « coiffeur Chartres ouvert lundi »…) et les communes où vous voulez être visible.'],
  ['technique', 'Optimisation technique', 'Site rapide et lisible sur mobile, pages explorables, canoniques, sitemap, données structurées conformes au contenu, robots.txt ouvert aux moteurs de recherche et de réponse.'],
  ['locale', 'Optimisation locale', 'Fiche Google : catégories, zone d’intervention, services, photos, horaires ; cohérence du nom, de l’adresse et du téléphone sur toutes vos présences en ligne ; méthode de demande d’avis.'],
  ['contenus', 'Production de contenus', 'Pages de services, réponses directes aux questions fréquentes, publications Google. Rédaction validée par vous avant publication.'],
  ['conversions', 'Suivi des conversions', 'Appels, messages WhatsApp, formulaires : vous suivez les demandes reçues depuis votre espace client. La réceptionniste IA évite de perdre les appels manqués.'],
  ['ia', 'Suivi de la visibilité IA', 'Une liste fixe de questions posées régulièrement à ChatGPT, Gemini et Perplexity, pour noter si votre entreprise est citée et avec quelle source.'],
  ['amelioration', 'Amélioration continue', 'Chaque mois, on ajuste selon les données : nouvelles questions de clients, communes à renforcer, contenus à mettre à jour.'],
]

export default function Methode() {
  return (
    <SubShell variant="main">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Méthode', PATH]]),
          { '@type': 'WebPage', '@id': abs(PATH) + '#page', url: abs(PATH), name: TITLE, inLanguage: 'fr-FR' },
          howTo({ path: PATH, name: 'La méthode Pulse Locale PME', steps: STEPS.map(([, t, d]) => [t, d]) }),
        ]}
      />
      <article className="article">
        <p className="crumbs"><a href={siteHref('/')}>Accueil</a> / Méthode</p>
        <span className="eyebrow">Notre méthode</span>
        <h1>Notre méthode, étape par étape</h1>
        <div className="callout" role="note">
          <strong className="mont">En bref</strong>
          <p>Pulse Locale PME part d’un audit et des recherches réelles de vos clients, corrige la technique et la fiche Google, produit des contenus utiles, puis suit les demandes reçues et la visibilité dans les assistants IA pour ajuster chaque mois. Nous ne promettons aucune position : nous rendons compte de ce qui est fait et mesuré.</p>
        </div>
        {STEPS.map(([id, t, d], i) => (
          <div key={id}>
            <h2 id={`etape-${i + 1}`}>{i + 1}. {t}</h2>
            <p>{d}</p>
          </div>
        ))}
        <h2>Ce que nous ne faisons pas</h2>
        <ul>
          <li>Garantir une première position sur Google ou une recommandation par une IA.</li>
          <li>Acheter des avis, publier de faux avis ou offrir des contreparties contre des avis.</li>
          <li>Créer des fiches Google pour des adresses où vous n’avez pas d’établissement.</li>
          <li>Garder vos accès : votre fiche Google et vos contenus restent à vous.</li>
        </ul>
        <h2>Résultats clients</h2>
        <p>Nous publierons ici des études de cas réelles, avec l’accord écrit des clients concernés et des chiffres vérifiables. Aucune n’est publiée à ce jour.</p>
        <CaseStudies />
        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>Commencer par le diagnostic</strong>
          <p>Démonstration de votre futur site offerte avant tout paiement.</p>
          <div className="hero-ctas">
            <OrderButton product="Démo gratuite (page méthode)" source="callback" title="Recevoir ma démo gratuite" className="btn btn-primary btn-sm">Recevoir ma démo gratuite →</OrderButton>
            <a href={siteHref('/info/outil-gratuit/')} className="btn btn-ghost btn-sm">Test de visibilité gratuit</a>
          </div>
        </div>
        <p>Pages locales : <a href={siteHref('/agence-seo-local-yvelines/')} className="link-underline">Yvelines (78)</a> · <a href={siteHref('/agence-seo-local-eure-et-loir/')} className="link-underline">Eure-et-Loir (28)</a> · Comprendre les notions : <a href={siteHref('/info/seo-aeo-geo/')} className="link-underline">SEO, AEO et GEO</a></p>
      </article>
    </SubShell>
  )
}
