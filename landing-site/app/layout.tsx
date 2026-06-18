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

export const metadata: Metadata = {
  title: 'LocalPulse — Présence web IA pour PMEs locales',
  description:
    "LocalPulse génère et pilote votre site web en 24h. Fiche Google optimisée, SEO local, hébergement inclus. Dès 79 €/mois, sans engagement.",
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
        {children}
      </body>
    </html>
  )
}
