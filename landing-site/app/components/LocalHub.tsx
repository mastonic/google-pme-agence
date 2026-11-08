import { abs, breadcrumbs, faqPage, localService } from '../seo/seo'
import { siteHref } from '../seo/domains'
import { PLANS_HT, PACKS_HT } from '../seo/offers'
import { DEPTS, cityPath, deptBySlug } from '../zones/zones'
import { guideBySlug, type Guide } from '../info/guides/guides'
import { HUB_UPDATED, hubPath, type Hub } from '../local/hubs'
import { Byline } from './Byline'
import { JsonLd } from './JsonLd'
import { OrderButton } from './OrderButton'
import { PricingTable } from './Pricing'
import { SubShell } from './SubShell'

const DATE_FR = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(HUB_UPDATED))

const SECTIONS: [string, string][] = [
  ['accompagnement', 'Notre accompagnement'],
  ['problemes', 'Les problèmes que l’on règle'],
  ['site', 'Création de site internet'],
  ['fiche-google', 'Optimisation Google Business Profile'],
  ['seo-local', 'Référencement local'],
  ['ia', 'Visibilité dans les moteurs de réponse IA'],
  ['receptionniste', 'Réceptionniste IA et automatisations'],
  ['tarifs', 'Tarifs'],
  ['methode', 'Méthode de travail'],
  ['villes', 'Villes desservies'],
  ['faq', 'Questions fréquentes'],
]

/** Page pilier locale (.fr) : contenu propre à chaque département, structure commune. */
export function LocalHub({ hub }: { hub: Hub }) {
  const path = hubPath(hub)
  const dept = deptBySlug(hub.dept)
  const areas = Array.from(new Set([...hub.cities.map((c) => c.name), ...(dept?.cities.flatMap((c) => c.communes) ?? [])]))
  const guides = hub.guides.map(guideBySlug).filter(Boolean) as Guide[]
  const other = DEPTS.find((d) => d.slug !== hub.dept)
  return (
    <SubShell variant="main">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], [hub.region, path]]),
          { '@type': 'WebPage', '@id': abs(path) + '#page', url: abs(path), name: hub.title, description: hub.description, inLanguage: 'fr-FR', dateModified: HUB_UPDATED, about: { '@type': 'AdministrativeArea', name: hub.region } },
          {
            ...localService({ path, name: `SEO local, sites internet et réceptionniste IA : ${hub.region}`, description: hub.enBref, areas, region: hub.region }),
            hasOfferCatalog: {
              '@type': 'OfferCatalog',
              name: 'Formules et packs Pulse Locale PME',
              itemListElement: [
                ...PLANS_HT.map((p) => ({ '@type': 'Offer', name: `Formule ${p.name}`, description: p.summary, price: String(p.monthly), priceCurrency: 'EUR', priceSpecification: { '@type': 'UnitPriceSpecification', price: String(p.monthly), priceCurrency: 'EUR', valueAddedTaxIncluded: false, unitCode: 'MON' }, url: abs('/#offres') })),
                { '@type': 'Offer', name: PACKS_HT.ficheGoogle.name, price: String(PACKS_HT.ficheGoogle.price), priceCurrency: 'EUR', priceSpecification: { '@type': 'PriceSpecification', price: String(PACKS_HT.ficheGoogle.price), priceCurrency: 'EUR', valueAddedTaxIncluded: false }, url: abs(PACKS_HT.ficheGoogle.path) },
              ],
            },
          },
          faqPage(hub.faqs),
        ]}
      />
      <article className="article">
        <p className="crumbs"><a href={siteHref('/')}>Accueil</a> / {hub.region}</p>
        <span className="eyebrow">{hub.region}</span>
        <h1>{hub.h1}</h1>
        <div className="meta">
          <time dateTime={HUB_UPDATED}>Mis à jour le {DATE_FR}</time>
          <Byline />
        </div>
        <p className="hero-lead" style={{ fontSize: 19 }}>{hub.lead}</p>
        <div className="callout" role="note">
          <strong className="mont">En bref</strong>
          <p>{hub.enBref}</p>
        </div>
        <div className="hero-ctas">
          <OrderButton product={`Démo gratuite – ${hub.region}`} source="callback" title="Recevoir ma démo gratuite" className="btn btn-primary">
            Recevoir ma démo gratuite →
          </OrderButton>
          <a href={siteHref('/info/outil-gratuit/')} className="btn btn-ghost">Tester ma visibilité</a>
        </div>

        <nav className="toc" aria-label="Sommaire">
          <strong className="mont">Au sommaire</strong>
          <ol>{SECTIONS.map(([id, t]) => <li key={id}><a href={`#${id}`}>{t}</a></li>)}</ol>
        </nav>

        <h2 id="accompagnement">Notre accompagnement {hub.dept === 'yvelines' ? 'dans les Yvelines' : 'en Eure-et-Loir'}</h2>
        {hub.presentation.map((p) => <p key={p.slice(0, 30)}>{p}</p>)}

        <h2 id="problemes">Les problèmes que l’on règle</h2>
        {hub.problems.map(([t, d]) => (
          <div key={t}>
            <h3>{t}</h3>
            <p>{d}</p>
          </div>
        ))}

        <h2 id="site">Création de site internet</h2>
        <p>{hub.site}</p>

        <h2 id="fiche-google">Optimisation Google Business Profile</h2>
        <p>{hub.gbp} <a href={siteHref(PACKS_HT.ficheGoogle.path)} className="link-underline">Voir le pack Fiche Google optimisée</a>.</p>

        <h2 id="seo-local">Référencement local</h2>
        <p>{hub.seo}</p>

        <h2 id="ia">Visibilité dans les moteurs de réponse IA</h2>
        <p>{hub.ia} <a href={siteHref('/info/seo-aeo-geo/')} className="link-underline">Comprendre SEO, AEO et GEO</a>.</p>

        <h2 id="receptionniste">Réceptionniste IA et automatisations</h2>
        <p>{hub.reception} <a href={siteHref('/info/articles/receptionniste-ia-artisan/')} className="link-underline">Fonctionnement, limites et tarifs</a>.</p>

        <h2 id="tarifs">Tarifs</h2>
        <p>Les tarifs sont identiques partout en France et affichés hors taxes.</p>
        <PricingTable />

        <h2 id="methode">Méthode de travail</h2>
        <p>{hub.method}</p>
        <ol>
          <li><strong>Diagnostic gratuit</strong> de votre fiche Google et de vos concurrents locaux.</li>
          <li><strong>Démonstration</strong> de votre futur site avant tout paiement.</li>
          <li><strong>Mise en place</strong> : site, fiche Google, zone d’intervention, contenus.</li>
          <li><strong>Suivi</strong> des appels, des demandes et de la visibilité, puis ajustements.</li>
        </ol>
        <p><a href={siteHref('/methode/')} className="link-underline">Le détail de notre méthode</a></p>

        <h2 id="villes">Villes desservies</h2>
        <ul>
          {hub.cities.map((c) => (
            <li key={c.name}>
              {c.slug && dept ? <a href={siteHref(cityPath(dept, dept.cities.find((x) => x.slug === c.slug)!))} className="link-underline">{c.name}</a> : <strong>{c.name}</strong>} : {c.note}
            </li>
          ))}
        </ul>
        <p>Et toutes les autres communes du département : l’accompagnement se fait entièrement à distance.</p>

        <h2 id="guides">Guides pour votre métier</h2>
        <ul>
          {guides.map((g) => (
            <li key={g.slug}><a href={siteHref(`/info/guides/${g.slug}/`)} className="link-underline">Guide {g.metier.toLowerCase()}</a> : {g.card}</li>
          ))}
        </ul>

        <h2 id="faq">Questions fréquentes : {hub.region}</h2>
        {hub.faqs.map(([q, a]) => (
          <div key={q}>
            <h3>{q}</h3>
            <p>{a}</p>
          </div>
        ))}

        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>Voyez votre futur site avant de payer</strong>
          <p>Laissez votre numéro : on vous prépare une démonstration personnalisée, gratuitement et sans engagement.</p>
          <div className="hero-ctas">
            <OrderButton product={`Démo gratuite – ${hub.region}`} source="callback" title="Recevoir ma démo gratuite" className="btn btn-primary btn-sm">
              Recevoir ma démo gratuite →
            </OrderButton>
            <a href={siteHref('/store/')} className="btn btn-ghost btn-sm">Voir les packs</a>
          </div>
        </div>

        {other && (
          <p>Vous êtes aussi en {other.name} ? <a href={siteHref(`/${other.slug === 'yvelines' ? 'agence-seo-local-yvelines' : 'agence-seo-local-eure-et-loir'}/`)} className="link-underline">Voir la page {other.name} ({other.code})</a>.</p>
        )}
      </article>
    </SubShell>
  )
}
