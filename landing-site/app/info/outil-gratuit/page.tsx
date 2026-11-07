import type { Metadata } from 'next'
import { PageHero, SubShell } from '../../components/SubShell'
import { ScoreTool } from './ScoreTool'

export const metadata: Metadata = {
  title: 'Test gratuit : votre score de visibilité locale sur Google · Pulse‑Pro',
  description:
    '8 questions, 30 secondes : découvrez votre score de visibilité Google Maps et IA, et les 3 actions prioritaires pour recevoir plus d’appels.',
  alternates: { canonical: '/info/outil-gratuit/' },
}

export default function Tool() {
  return (
    <SubShell variant="info">
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
