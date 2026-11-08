import type { Metadata } from 'next'

export const metadata: Metadata = { title: 'Page introuvable | Pulse Locale PME', robots: { index: false, follow: true }, alternates: { canonical: null } }

export default function NotFound() {
  return (
    <main style={{ padding: '120px 24px', textAlign: 'center', fontFamily: 'Inter, sans-serif' }}>
      <h1 style={{ fontFamily: 'Montserrat, sans-serif' }}>Cette page n’existe pas.</h1>
      <p style={{ marginTop: 16 }}><a href="/" style={{ color: '#028090', fontWeight: 600 }}>Retour à l’accueil</a> · <a href="/info/" style={{ color: '#028090', fontWeight: 600 }}>Ressources</a> · <a href="/store/" style={{ color: '#028090', fontWeight: 600 }}>Boutique</a></p>
    </main>
  )
}
