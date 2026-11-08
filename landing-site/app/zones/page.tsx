import type { Metadata } from 'next'
import { abs, breadcrumbs, itemList, ORG_ID, pageMeta } from '../seo/seo'
import { JsonLd } from '../components/JsonLd'
import { PageHero, SubShell } from '../components/SubShell'
import { DEPTS, cityPath, deptPath } from './zones'

const TITLE = 'Zones desservies : Yvelines (78) et Eure-et-Loir (28)'
const DESC = 'Fiche Google, site internet et réceptionniste IA pour les artisans et commerces des Yvelines et d’Eure-et-Loir : Versailles, Saint-Germain, Chartres, Dreux…'

export const metadata: Metadata = pageMeta({ title: TITLE, description: DESC, path: '/zones/' })

export default function Zones() {
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Zones desservies', '/zones/']]),
          { '@type': 'CollectionPage', name: 'Zones desservies', url: abs('/zones/'), inLanguage: 'fr-FR', publisher: { '@id': ORG_ID } },
          itemList('Zones desservies', DEPTS.flatMap((d) => [[`${d.name} (${d.code})`, deptPath(d)] as [string, string], ...d.cities.map((c) => [c.name, cityPath(d, c)] as [string, string])])),
        ]}
      />
      <PageHero
        eyebrow="Zones desservies"
        title="Visible et joignable dans votre commune."
        lead="Une page par département et par ville, avec les communes desservies, les recherches de vos clients et la réceptionniste IA qui répond aux appels que vous manquez."
      >
        <a href="/info/outil-gratuit/" className="btn btn-primary">Tester ma visibilité en 30 s →</a>
      </PageHero>
      {DEPTS.map((d) => (
        <section key={d.slug} className="wrap section">
          <h2 className="h2"><a href={deptPath(d)}>{d.name} ({d.code})</a></h2>
          <div className="grid-280" style={{ marginTop: 24 }}>
            {d.cities.map((c) => (
              <a key={c.slug} href={cityPath(d, c)} className="card" data-reveal="stagger">
                <span className="card-tag">{d.name} · {d.code}</span>
                <h3 style={{ fontSize: 20 }}>{c.name}</h3>
                <p>{c.communes.slice(1, 5).join(', ')}…</p>
                <span className="link-underline">Voir la page →</span>
              </a>
            ))}
          </div>
        </section>
      ))}
    </SubShell>
  )
}
