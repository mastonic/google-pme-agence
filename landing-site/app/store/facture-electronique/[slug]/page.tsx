import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { abs, breadcrumbs, ORG_ID, pageMeta } from '../../../seo/seo'
import { JsonLd } from '../../../components/JsonLd'
import { SubShell } from '../../../components/SubShell'
import { OrderButton } from '../../../components/OrderButton'
import { siteHref } from '../../../seo/domains'
import { BuyButton } from '../BuyButton'
import { FE_PACKS, FE_PATH, fePackPath } from '../packs'

export const dynamicParams = false
export function generateStaticParams() {
  return FE_PACKS.map((p) => ({ slug: p.slug }))
}

const get = (slug: string) => FE_PACKS.find((p) => p.slug === slug)

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const p = get(params.slug)
  if (!p) return {}
  return pageMeta({ title: p.seoTitle, description: p.seoDescription, path: fePackPath(p.slug) })
}

const MENTIONS: [string, string][] = [
  ['SIREN du client', 'Les 9 chiffres de votre client professionnel'],
  ['Adresse de livraison', 'Si elle diffère de l’adresse de facturation'],
  ['Catégorie d’opération', 'Biens, services ou les deux'],
  ['Option TVA sur les débits', 'Si vous avez choisi cette option'],
]

export default function FePackPage({ params }: { params: { slug: string } }) {
  const p = get(params.slug)
  if (!p) notFound()
  const complet = FE_PACKS.find((x) => x.slug === 'pack-complet-zero-stress')!
  return (
    <SubShell variant="store">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Boutique', '/store/'], ['Facture électronique', FE_PATH], [p.name, fePackPath(p.slug)]]),
          {
            '@type': 'Product',
            name: p.name,
            description: p.seoDescription,
            brand: { '@id': ORG_ID },
            offers: { '@type': 'Offer', price: String(p.price), priceCurrency: 'EUR', url: abs(fePackPath(p.slug)), availability: 'https://schema.org/InStock', seller: { '@id': ORG_ID } },
          },
        ]}
      />
      <div className="wrap" style={{ paddingTop: 28 }}>
        <p className="crumbs"><a href={siteHref('/store/')}>Boutique</a> / <a href={siteHref(FE_PATH)}>Facture électronique</a> / {p.name}</p>
      </div>
      <section className="wrap product">
        <div className="stack" style={{ gap: 28 }}>
          <span className={`card-tag${p.gold ? ' gold' : ''}`}>{p.tag}</span>
          <h1 className="h2" style={{ fontSize: 'clamp(34px,5vw,54px)' }}>{p.title}</h1>
          <p className="hero-lead">{p.lead}</p>

          {p.situations && (
            <>
              <h2 className="mont" style={{ fontSize: 26 }}>Vos situations, expliquées</h2>
              <table className="compare">
                <thead><tr><th>Situation</th><th>Ce que vous devez faire</th></tr></thead>
                <tbody>{p.situations.map(([a, b]) => <tr key={a}><th>{a}</th><td className="after">{b}</td></tr>)}</tbody>
              </table>
            </>
          )}

          <h2 className="mont" style={{ fontSize: 26 }}>Ce que vous téléchargez</h2>
          <ul className="ticks">{p.contents.map((c) => <li key={c}>{c}</li>)}</ul>

          <h2 className="mont" style={{ fontSize: 26 }}>Les 4 nouvelles mentions, déjà dans le modèle</h2>
          <table className="compare">
            <tbody>{MENTIONS.map(([a, b]) => <tr key={a}><th>{a}</th><td>{b}</td></tr>)}</tbody>
          </table>

          <h2 className="mont" style={{ fontSize: 26 }}>Pour qui ?</h2>
          <ul className="ticks">{p.forWho.map((c) => <li key={c}>{c}</li>)}</ul>

          <div className="callout">
            <strong className="mont" style={{ fontSize: 20 }}>Ce que ce pack n’est pas</strong>
            <p>
              Ce n’est pas un logiciel de facturation : la loi impose une plateforme agréée pour émettre vos factures.
              Le pack vous aide à comprendre la réforme, choisir la bonne plateforme et préparer vos données. Informations
              générales à jour en novembre 2026, qui ne remplacent pas votre expert-comptable.
            </p>
          </div>
        </div>

        <aside className="buybox" aria-label="Acheter ce pack">
          <h2 className="mont" style={{ fontSize: 22 }}>{p.name}</h2>
          <div className="price"><strong>{p.price} €</strong><span>HT · paiement unique</span></div>
          <ul className="ticks">{p.contents.slice(0, 5).map((c) => <li key={c}>{c.split(' (')[0]}</li>)}</ul>
          <BuyButton pack={p} label="Acheter maintenant →" style={{ width: '100%' }} />
          <p className="small muted">Téléchargement immédiat · Facture automatique · Sans abonnement</p>
          <OrderButton product={`Question : ${p.name}`} kind="product_info" source="store" title="Une question sur ce pack ?" phoneRequired={false}
            intro="Posez votre question : on vous répond par email, sans engagement." submitLabel="Envoyer ma question →"
            className="btn btn-ghost btn-sm" style={{ width: '100%' }}>
            Une question sur ce pack ?
          </OrderButton>
          {p.slug !== complet.slug && (
            <>
              <hr style={{ border: 0, borderTop: '1px solid #E2E8F0', width: '100%' }} />
              <p className="small muted">
                <strong style={{ color: '#1E293B' }}>Besoin de tout ?</strong> Le{' '}
                <a href={siteHref(fePackPath(complet.slug))}>pack complet à {complet.price} €</a> réunit les 4 métiers,
                l’automatisation et 12 mois de mises à jour.
              </p>
            </>
          )}
        </aside>
      </section>
    </SubShell>
  )
}
