import type { Metadata } from 'next'
import { SubShell, mail } from '../../components/SubShell'

export const metadata: Metadata = {
  title: 'Guide gratuit : les 10 erreurs qui cachent votre commerce sur Google · Pulse‑Pro',
  description:
    'Téléchargez la checklist PDF utilisée pour auditer les fiches Google de nos clients. 14 pages, 15 minutes de lecture, des actions immédiates.',
  alternates: { canonical: '/info/guide-gratuit/' },
}

const INSIDE = [
  'Les 10 erreurs les plus fréquentes, classées par impact',
  'Pour chacune : comment la repérer et la corriger en moins de 10 min',
  'La checklist à imprimer et cocher',
  'Le modèle de SMS pour demander un avis',
]

export default function LeadMagnet() {
  return (
    <SubShell variant="info">
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
            <a href="/guide-10-erreurs-google.pdf" download className="btn btn-primary" style={{ textAlign: 'center' }}>
              Télécharger le guide gratuit (PDF) →
            </a>
            <a href={mail('Guide 10 erreurs - envoyez-le moi + conseils')} className="btn btn-outline">
              Le recevoir par email avec des conseils personnalisés
            </a>
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
