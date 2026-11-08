import type { Metadata } from 'next'
import { abs, breadcrumbs, ORG_ID, pageMeta } from '../../seo/seo'
import { JsonLd } from '../../components/JsonLd'
import { SubShell } from '../../components/SubShell'
import { LeadForm } from '../../components/LeadForm'

export const metadata: Metadata = pageMeta({
  title: 'Guide PDF gratuit : les 10 erreurs qui cachent votre commerce sur Google | Pulse Locale PME',
  description: 'Checklist PDF gratuite de 14 pages : les 10 erreurs de fiche Google les plus fréquentes chez les artisans et commerçants, et comment les corriger en 10 minutes chacune.',
  path: '/info/guide-gratuit/',
})

const INSIDE = [
  'Les 10 erreurs les plus fréquentes, classées par impact',
  'Pour chacune : comment la repérer et la corriger en moins de 10 min',
  'La checklist à imprimer et cocher',
  'Le modèle de SMS pour demander un avis',
]

export default function LeadMagnet() {
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Ressources', '/info/'], ['Guide PDF gratuit', '/info/guide-gratuit/']]),
          {
            '@type': 'DigitalDocument',
            name: 'Les 10 erreurs qui cachent votre commerce sur Google',
            description: 'Checklist pratique de 14 pages pour TPE, artisans et commerçants.',
            inLanguage: 'fr-FR',
            isAccessibleForFree: true,
            encodingFormat: 'application/pdf',
            url: abs('/guide-10-erreurs-google.pdf'),
            publisher: { '@id': ORG_ID },
          },
        ]}
      />
      <section className="wrap lm">
        <div className="cover" data-reveal="0" aria-hidden="true">
          <small>PULSE‑PRO · GUIDE GRATUIT</small>
          <div>
            <div className="big">10</div>
            <h2>erreurs qui cachent votre commerce sur Google</h2>
          </div>
          <small>Checklist pratique pour TPE, artisans et commerçants</small>
        </div>

        <div className="stack" style={{ gap: 22 }}>
          <span className="eyebrow">Guide PDF gratuit · 14 pages</span>
          <h1 className="h2">Vos clients vous cherchent. Ce guide vous dit pourquoi ils ne vous trouvent pas.</h1>
          <p className="hero-lead">
            La plupart des commerces perdent des clients à cause de détails : une catégorie mal choisie, des horaires
            faux, des avis sans réponse. On a regroupé les 10 erreurs qu’on corrige le plus souvent.
          </p>
          <ul className="ticks">{INSIDE.map((i) => <li key={i}>{i}</li>)}</ul>

          <div className="form-card">
            <strong className="mont" style={{ fontSize: 18 }}>Recevez le guide gratuit</strong>
            <LeadForm
              source="guide_pdf"
              askName
              cta="Télécharger le guide gratuit (PDF) →"
              downloadOnSuccess="/guide-10-erreurs-google.pdf"
              successText={<p><strong>Merci !</strong> Le téléchargement a démarré. Rien ne s’ouvre ? <a href="/guide-10-erreurs-google.pdf" download style={{ textDecoration: 'underline' }}>Cliquez ici</a>.</p>}
            />
            <p className="small muted">Gratuit, sans engagement. Vos données ne sont jamais revendues.</p>
          </div>

          <div className="chips">
            <a href="/info/outil-gratuit/">Faire le test de visibilité</a>
            <a href="/info/guides/plombier/">Guide plombier</a>
            <a href="/store/">Boutique</a>
          </div>
        </div>
      </section>
    </SubShell>
  )
}
