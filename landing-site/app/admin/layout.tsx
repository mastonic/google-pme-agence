import type { Metadata } from 'next'

// Espace interne : jamais indexé.
export const metadata: Metadata = {
  robots: { index: false, follow: false },
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return children
}
