import type { Metadata } from 'next'
// Polices hébergées avec le site (paquets @fontsource) : la construction ne dépend plus
// de Google Fonts, dont la réponse faisait échouer next/font sur Cloud Build.
import '@fontsource/petrona/400.css'
import '@fontsource/petrona/500.css'
import '@fontsource/petrona/600.css'
import '@fontsource/work-sans/400.css'
import '@fontsource/work-sans/500.css'
import '@fontsource/work-sans/600.css'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'
import './globals.css'

const SITE_URL = 'https://pme-local-pulse.web.app'
const DESCRIPTION =
  "Pulse-PME accompagne les TPE et PME dans leur présence web et leur visibilité locale. Une solution éditée et opérée par HoldMasto, RCS Fort-de-France 106 121 536."

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: 'Pulse-PME — une solution de HoldMasto',
  description: DESCRIPTION,
  applicationName: 'Pulse-PME',
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    locale: 'fr_FR',
    url: SITE_URL,
    siteName: 'Pulse-PME',
    title: 'Pulse-PME — une solution de HoldMasto',
    description: DESCRIPTION,
  },
  robots: {
    index: true,
    follow: true,
  },
}

// Données structurées : uniquement des informations publiques et vérifiables.
const JSON_LD = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'HoldMasto',
      url: SITE_URL,
      identifier: 'RCS Fort-de-France 106 121 536',
    },
    {
      '@type': 'SoftwareApplication',
      name: 'Pulse-PME',
      applicationCategory: 'BusinessApplication',
      operatingSystem: 'Web',
      url: SITE_URL,
      description: DESCRIPTION,
      publisher: { '@type': 'Organization', name: 'HoldMasto' },
      inLanguage: 'fr',
    },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="fr"
      className="scroll-smooth"
    >
      <body className="bg-[#060D17] antialiased">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD).replace(/</g, '\\u003c') }}
        />
        {children}
      </body>
    </html>
  )
}
