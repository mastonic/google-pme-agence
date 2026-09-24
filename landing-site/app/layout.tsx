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
  title: 'Pulse-PME — une solution de HoldMasto',
  description:
    "Pulse-PME accompagne les TPE et PME dans leur présence web et leur visibilité locale. Une solution éditée et opérée par HoldMasto, RCS Fort-de-France 106 121 536.",
  applicationName: 'Pulse-PME',
  robots: {
    index: true,
    follow: true,
  },
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
