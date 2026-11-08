import type { Metadata } from 'next'
import { abs, breadcrumbs, ORG_ID, pageMeta } from '../../seo/seo'
import { JsonLd } from '../../components/JsonLd'
import { PageHero, SubShell } from '../../components/SubShell'
import { ScoreTool } from './ScoreTool'

export const metadata: Metadata = pageMeta({
  title: 'Test gratuit : votre score de visibilité Google Maps et IA en 30 secondes | Pulse Locale PME',
  description: '8 questions, 30 secondes, sans inscription : obtenez votre score de visibilité locale sur 100 (Google Maps, avis, site, ChatGPT) et vos 3 actions prioritaires.',
  path: '/info/outil-gratuit/',
})

export default function Tool() {
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Ressources', '/info/'], ['Test de visibilité', '/info/outil-gratuit/']]),
          {
            '@type': 'WebApplication',
            name: 'Test de visibilité locale Pulse Locale PME',
            url: abs('/info/outil-gratuit/'),
            applicationCategory: 'BusinessApplication',
            operatingSystem: 'Web',
            isAccessibleForFree: true,
            offers: { '@type': 'Offer', price: '0', priceCurrency: 'EUR' },
            publisher: { '@id': ORG_ID },
          },
        ]}
      />
      <PageHero
        eyebrow="Gratuit · 30 secondes · Sans inscription"
        title="Votre commerce est-il visible sur Google ? Faites le test."
        lead="Répondez à 8 questions simples. Vous obtenez tout de suite un score sur 100 et les 3 actions qui vous rapporteront le plus de clients."
      />
      <section className="wrap" style={{ paddingBottom: 96 }}>
        <ScoreTool />
      </section>
    </SubShell>
  )
}
