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
import { SITE_URL, pageMeta } from './lib/seo'

const TITLE = 'Site internet et fiche Google pour artisans et TPE dès 49 €/mois | Pulse-Pro'
const DESCRIPTION =
  "Pulse-Pro crée votre site professionnel, optimise votre fiche Google et gère vos appels et WhatsApp pour attirer plus de clients locaux. Démo gratuite avant de payer, dès 49 €/mois, sans engagement."

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: TITLE,
  description: DESCRIPTION,
  applicationName: 'Pulse-Pro',
  authors: [{ name: 'HoldMasto', url: 'https://holdmasto.fr' }],
  ...pageMeta({ title: TITLE, description: DESCRIPTION, path: '/' }),
  robots: { index: true, follow: true, 'max-image-preview': 'large', 'max-snippet': -1 },
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
        {children}
      </body>
    </html>
  )
}
