import type { Metadata } from 'next'
// Polices hébergées avec le site (paquets @fontsource) : la construction ne dépend pas
// de Google Fonts, dont la réponse faisait échouer next/font sur Cloud Build.
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '@fontsource/montserrat/600.css'
import '@fontsource/montserrat/700.css'
import '@fontsource/montserrat/800.css'
import './globals.css'

const SITE_URL = 'https://pme-local-pulse.web.app'
const TITLE = 'Pulse‑Pro · Plus de clients locaux, sans vous occuper du web'
const DESCRIPTION =
  "Site professionnel, fiche Google, appels et WhatsApp : Pulse‑Pro gère la visibilité locale des TPE et PME. Démo gratuite avant tout paiement, dès 49 € / mois, sans engagement. Une solution de HoldMasto, RCS Fort-de-France 106 121 536."

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: TITLE,
  description: DESCRIPTION,
  applicationName: 'Pulse‑Pro',
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    locale: 'fr_FR',
    url: SITE_URL,
    siteName: 'Pulse‑Pro',
    title: TITLE,
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
      name: 'Pulse‑Pro',
      applicationCategory: 'BusinessApplication',
      operatingSystem: 'Web',
      url: SITE_URL,
      description: DESCRIPTION,
      publisher: { '@type': 'Organization', name: 'HoldMasto' },
      inLanguage: 'fr',
    },
  ],
}

// Active les animations avant le premier affichage, sauf si l'appareil demande moins d'animations.
const MOTION_SCRIPT =
  "if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches)document.documentElement.classList.add('motion');"

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr" className="scroll-smooth" suppressHydrationWarning>
      <body className="antialiased">
        <script dangerouslySetInnerHTML={{ __html: MOTION_SCRIPT }} />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD).replace(/</g, '\\u003c') }}
        />
        {children}
      </body>
    </html>
  )
}
