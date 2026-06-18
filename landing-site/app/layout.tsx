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
  title: 'Pulse-PME — Présence numérique pour commerces de proximité',
  description:
    "Pulse-PME construit votre site, optimise votre fiche Google et gère votre visibilité locale. Vous gérez votre commerce, on s'occupe du reste.",
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
      <body className="bg-porcelaine font-sans text-encre antialiased">
        {children}
      </body>
    </html>
  )
}
