import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { abs, breadcrumbs, faqPage, itemList, localService, pageMeta } from '../../seo/seo'
import { JsonLd } from '../../components/JsonLd'
import { OrderButton } from '../../components/OrderButton'
import { PageHero, SubShell } from '../../components/SubShell'
import { guideBySlug, type Guide } from '../../info/guides/guides'
import { DEPTS, cityPath, deptBySlug, deptPath } from '../zones'

export const dynamicParams = false

export function generateStaticParams() {
  return DEPTS.map((d) => ({ dept: d.slug }))
}

export function generateMetadata({ params }: { params: { dept: string } }): Metadata {
  const d = deptBySlug(params.dept)
  if (!d) return {}
  return pageMeta({ title: d.title, description: d.description, path: deptPath(d) })
}

export default function DeptPage({ params }: { params: { dept: string } }) {
  const d = deptBySlug(params.dept)
  if (!d) notFound()
  const path = deptPath(d)
  const region = `${d.name} (${d.code})`
  const allCommunes = Array.from(new Set(d.cities.flatMap((c) => c.communes)))
  const guides = d.metiers.map(guideBySlug).filter(Boolean) as Guide[]
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Zones desservies', '/zones/'], [d.name, path]]),
          { '@type': 'WebPage', '@id': abs(path) + '#page', url: abs(path), name: d.title, inLanguage: 'fr-FR', about: { '@type': 'AdministrativeArea', name: region } },
          localService({ path, name: `Visibilité locale et réceptionniste IA : ${region}`, description: d.enBref, areas: allCommunes, region }),
          itemList(`Villes desservies : ${d.name}`, d.cities.map((c) => [c.name, cityPath(d, c)])),
          faqPage(d.faqs),
        ]}
      />
      <PageHero eyebrow={`${d.name} · ${d.code}`} title={d.h1} lead={d.lead}>
        <a href="/info/outil-gratuit/" className="btn btn-primary">Tester ma visibilité en 30 s →</a>
        <OrderButton product={`Réceptionniste IA – ${region}`} source="callback" title="Activer ma réceptionniste IA" className="btn btn-ghost">
          Essayer la réceptionniste IA
        </OrderButton>
      </PageHero>
      <article className="article">
        <div className="callout" role="note">
          <strong className="mont">En bref</strong>
          <p>{d.enBref}</p>
        </div>
        {d.context.map((p) => <p key={p.slice(0, 24)}>{p}</p>)}

        <h2>Nos pages par ville</h2>
        <ul>
          {d.cities.map((c) => (
            <li key={c.slug}><a href={cityPath(d, c)} className="link-underline">{c.name}</a> : {c.communes.slice(1, 5).join(', ')}…</li>
          ))}
        </ul>

        <h2>Communes desservies en {d.name}</h2>
        <p>{allCommunes.join(', ')}, et toutes les autres communes du département : tout se fait en ligne, depuis votre espace client.</p>

        <h2>La réceptionniste IA : plus aucun appel perdu</h2>
        <p>
          Quand vous ne pouvez pas décrocher, l’appel est renvoyé vers votre réceptionniste IA. Elle répond au nom de votre
          entreprise, pose les bonnes questions (besoin, commune, urgence, créneau), puis vous envoie un résumé par WhatsApp
          ou SMS. Votre numéro ne change pas. Essai gratuit de 30 jours dans la limite de 60 appels, puis 39 € HT par mois
          avec 100 appels inclus, ou incluse dans la formule Élite.
        </p>

        <h2>Guides pour les métiers les plus recherchés</h2>
        <ul>
          {guides.map((g) => (
            <li key={g.slug}><a href={`/info/guides/${g.slug}/`} className="link-underline">Guide {g.metier.toLowerCase()}</a> : {g.card}</li>
          ))}
        </ul>

        <h2 id="faq">Questions fréquentes : {d.name}</h2>
        {d.faqs.map(([q, a]) => (
          <div key={q}>
            <h3>{q}</h3>
            <p>{a}</p>
          </div>
        ))}

        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>On commence par un diagnostic gratuit ?</strong>
          <p>Le test de visibilité compare votre fiche Google aux critères qui comptent, en 8 questions. Ensuite, la démonstration de votre site est offerte avant tout paiement.</p>
          <div className="hero-ctas">
            <a href="/info/outil-gratuit/" className="btn btn-primary btn-sm">Faire le test gratuit →</a>
            <a href="/#offres" className="btn btn-ghost btn-sm">Voir les formules</a>
          </div>
        </div>
      </article>
    </SubShell>
  )
}
