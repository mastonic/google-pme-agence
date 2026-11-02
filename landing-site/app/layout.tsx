import type { Metadata } from 'next'
import { Petrona, Work_Sans, IBM_Plex_Mono } from 'next/font/google'
import './globals.css'

const petrona = Petrona({
  subsets: ['latin'],
  variable: '--font-petrona',
  weight: ['400', '500', '600'],
  display: 'swap',
})

const workSans = Work_Sans({
  subsets: ['latin'],
  variable: '--font-work-sans',
  weight: ['400', '500', '600'],
  display: 'swap',
})

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  variable: '--font-ibm-plex-mono',
  weight: ['400', '500'],
  display: 'swap',
})

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
      className={`scroll-smooth ${petrona.variable} ${workSans.variable} ${ibmPlexMono.variable}`}
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
