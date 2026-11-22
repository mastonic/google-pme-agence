import type { Metadata } from 'next'
import { abs, breadcrumbs, faqPage, ORG_ID, pageMeta } from '../../seo/seo'
import { JsonLd } from '../../components/JsonLd'
import { PageHero, SubShell } from '../../components/SubShell'
import { siteHref } from '../../seo/domains'
import { BuyButton } from './BuyButton'
import { FE_FAQ, FE_PACKS, FE_PATH, fePackPath } from './packs'

export const metadata: Metadata = pageMeta({
  title: 'Facture électronique 2027 : packs guides + modèles pour TPE et artisans',
  description: 'Prêt pour la facture électronique ? Guides PDF, checklists et modèles Excel par métier (taxi, bâtiment, libéral, commerce) dès 29 € HT. Téléchargement immédiat.',
  path: FE_PATH,
})

const CALENDAR: [string, string, string][] = [
  ['1er sept. 2026', 'Toutes les entreprises', 'Recevoir les factures électroniques via une plateforme agréée'],
  ['1er sept. 2027', 'TPE, PME, micro-entreprises', 'Émettre ses factures B2B en électronique + e-reporting + 4 nouvelles mentions'],
]

const PAINS = [
  ['« Je suis en franchise de TVA, ça ne me concerne pas. »', 'Faux : la franchise ne dispense pas de la réforme.'],
  ['« J’envoie mes factures en PDF, c’est déjà électronique. »', 'Non : un PDF par email ne sera plus valable pour vos clients pros.'],
  ['« Je verrai l’été prochain. »', 'Les plateformes seront saturées, et l’amende est de 50 € par facture non conforme.'],
]

export default function FactureElectronique() {
  const metiers = FE_PACKS.filter((p) => p.kind === 'metier')
  const others = FE_PACKS.filter((p) => p.kind !== 'metier')
  return (
    <SubShell variant="store">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Boutique', '/store/'], ['Facture électronique', FE_PATH]]),
          {
            '@type': 'OfferCatalog',
            name: 'Packs Facture Électronique Ready',
            url: abs(FE_PATH),
            itemListElement: FE_PACKS.map((p) => ({ '@type': 'Offer', name: p.name, description: p.short, price: String(p.price), priceCurrency: 'EUR', url: abs(fePackPath(p.slug)), seller: { '@id': ORG_ID } })),
          },
          faqPage(FE_FAQ),
        ]}
      />
      <PageHero
        eyebrow="Réforme 2026-2027 · Téléchargement immédiat · Dès 29 € HT"
        title="Facture électronique 2027 : soyez prêt, sans stress et sans jargon."
        lead="Guides clairs, checklists et modèles Excel adaptés à votre métier. Tout ce qu’un artisan, un commerçant ou un indépendant doit savoir et faire avant le 1er septembre 2027."
      >
        <a href="#metiers" className="btn btn-primary">Trouver le pack de mon métier →</a>
        <a href={siteHref(fePackPath('pack-complet-zero-stress'))} className="btn btn-ghost">Voir le pack complet</a>
      </PageHero>

      <section className="wrap" style={{ paddingBottom: 48 }}>
        <div className="trust" data-reveal="0">
          <div><strong>À jour</strong><span>Édition novembre 2026</span></div>
          <div><strong>Par métier</strong><span>Taxi, bâtiment, libéral, commerce</span></div>
          <div><strong>Prêt à l’emploi</strong><span>PDF + Excel, rien à installer</span></div>
          <div><strong>Société française</strong><span>Support en français</span></div>
        </div>
      </section>

      <section className="band-white">
        <div className="wrap section">
          <div className="section-head" data-reveal="0">
            <span className="eyebrow">Le calendrier</span>
            <h2 className="h2">Deux dates à connaître. La première est déjà passée.</h2>
          </div>
          <table className="compare">
            <thead><tr><th>Date</th><th>Qui</th><th>Obligation</th></tr></thead>
            <tbody>{CALENDAR.map(([d, q, o]) => <tr key={d}><th>{d}</th><td>{q}</td><td className="after">{o}</td></tr>)}</tbody>
          </table>
          <div className="grid-280" style={{ marginTop: 32 }}>
            {PAINS.map(([q, a]) => (
              <article key={q} className="card" data-reveal="stagger"><h3 style={{ fontSize: 18 }}>{q}</h3><p>{a}</p></article>
            ))}
          </div>
        </div>
      </section>

      <section id="metiers" className="wrap section">
        <div className="section-head" data-reveal="0">
          <span className="eyebrow">Packs métier · 49 € HT</span>
          <h2 className="h2">Votre métier, vos cas concrets.</h2>
          <p className="section-lead">Chaque pack métier contient le guide de votre profession, le guide général, la checklist, le modèle de facture et le kit de suivi Excel.</p>
        </div>
        <div className="grid-280">
          {metiers.map((p) => (
            <article key={p.slug} className="card" data-reveal="stagger">
              <span className={`card-tag${p.gold ? ' gold' : ''}`}>{p.gold ? 'Le plus demandé' : p.tag}</span>
              <h3>{p.name.replace('Pack ', '')}</h3>
              <p>{p.short}</p>
              <div className="price"><strong>{p.price} €</strong><span>HT · téléchargement immédiat</span></div>
              <a href={siteHref(fePackPath(p.slug))} className="btn btn-primary btn-sm">Voir le pack</a>
            </article>
          ))}
        </div>
      </section>

      <section id="packs" className="band-white">
        <div className="wrap section">
          <div className="section-head" data-reveal="0">
            <span className="eyebrow">Les autres packs</span>
            <h2 className="h2">Commencer petit, ou tout prendre d’un coup.</h2>
          </div>
          <div className="grid-280">
            {others.map((p) => (
              <article key={p.slug} className="card" data-reveal="stagger">
                <span className={`card-tag${p.gold ? ' gold' : ''}`}>{p.tag}</span>
                <h3>{p.name}</h3>
                <p>{p.short}</p>
                <ul className="ticks">{p.contents.slice(0, 4).map((c) => <li key={c}>{c}</li>)}</ul>
                <div className="price"><strong>{p.price} €</strong><span>HT · paiement unique</span></div>
                <a href={siteHref(fePackPath(p.slug))} className="btn btn-primary btn-sm">Voir le pack</a>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="faq" className="faq-band">
        <div className="faq">
          <div className="section-head"><span className="eyebrow">Avant d’acheter</span><h2 className="h2">Vos questions, nos réponses.</h2></div>
          <div className="faq-list">
            {FE_FAQ.map(([q, a]) => (
              <details key={q} className="faq-item">
                <summary className="faq-q">{q}<span className="faq-icon">+</span></summary>
                <p className="faq-a">{a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section className="final-band">
        <div className="final" data-reveal="0">
          <h2>Le 1er septembre 2027 arrive vite.</h2>
          <p>Le pack complet : tous les guides, tous les modèles, et 12 mois de mises à jour.</p>
          <BuyButton pack={FE_PACKS.find((p) => p.slug === 'pack-complet-zero-stress')!} label="Prendre le pack complet à 147 € →" className="btn btn-final" />
        </div>
      </section>
    </SubShell>
  )
}
