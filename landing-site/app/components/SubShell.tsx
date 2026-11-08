import { Logo } from './Logo'
import { Reveal } from './Reveal'
import '../landing.css'
import '../sub.css'

import { CONTACT_EMAIL, mail } from './contact'
import { OrderButton } from './OrderButton'
export { mail }

type Variant = 'store' | 'info'

const NAV: Record<Variant, [string, string][]> = {
  store: [
    ['/store/#packs', 'Packs'],
    ['/store/#abonnements', 'Abonnements'],
    ['/store/#materiel', 'Matériel avis'],
    ['/store/#faq', 'FAQ'],
  ],
  info: [
    ['/info/outil-gratuit/', 'Test gratuit'],
    ['/info/#guides', 'Guides métier'],
    ['/info/#actus', 'Actus'],
    ['/info/guide-gratuit/', 'Guide PDF'],
  ],
}

const CTA: Record<Variant, [string, string]> = {
  store: ['/store/#packs', 'Voir les packs'],
  info: ['/info/outil-gratuit/', 'Tester ma visibilité'],
}

export function SubShell({ variant, children }: { variant: Variant; children: React.ReactNode }) {
  const home = variant === 'store' ? '/store/' : '/info/'
  return (
    <div id="top" className="landing">
      <Reveal />
      <header className="site-header">
        <div className="wrap">
          <a href={home} className="brand" aria-label="Accueil">
            <Logo />
            <span className="brand-tag">{variant === 'store' ? 'Boutique' : 'Ressources'}</span>
          </a>
          <nav className="main-nav" aria-label="Navigation principale">
            {NAV[variant].map(([href, label]) => (
              <a key={href} href={href}>
                {label}
              </a>
            ))}
          </nav>
          <a href={CTA[variant][0]} className="btn btn-dark btn-header">
            {CTA[variant][1]}
          </a>
        </div>
      </header>
      <main>{children}</main>
      <footer className="site-footer">
        <div className="wrap footer-grid">
          <div className="stack" style={{ gap: 6 }}>
            <strong className="footer-brand">Pulse Locale PME</strong>
            <span>Visibilité locale des TPE et PME. Édité par HoldMasto, maison mère.</span>
            <a href="/">Découvrir l’offre complète →</a>
          </div>
          <div className="stack">
            <strong>Nos sites</strong>
            <a href="/">pulse-locale-pme.fr</a>
            <a href="/store/">Boutique (.store)</a>
            <a href="/info/">Ressources (.info)</a>
          </div>
          <div className="stack">
            <strong>HoldMasto</strong>
            <span>SASU · RCS Fort‑de‑France 106 121 536</span>
            <OrderButton product="Contact Pulse Locale PME" source="contact" title="Nous contacter" phoneRequired={false}
              intro="Une question, un projet ? Laissez-nous un message, on vous répond sous 24 h ouvrées." submitLabel="Envoyer →"
              style={{ background: 'none', padding: 0, color: 'inherit', textAlign: 'left', textDecoration: 'underline' }}>
              Nous écrire
            </OrderButton>
            <span>{CONTACT_EMAIL}</span>
          </div>
          <nav className="stack" aria-label="Informations légales">
            <strong>Informations légales</strong>
            <a href="/mentions-legales/#mentions">Mentions légales</a>
            <a href="/mentions-legales/#cgv">CGV</a>
            <a href="/mentions-legales/#rgpd">Confidentialité (RGPD)</a>
          </nav>
        </div>
      </footer>
    </div>
  )
}

export function PageHero({
  eyebrow,
  title,
  lead,
  children,
}: {
  eyebrow: string
  title: string
  lead: string
  children?: React.ReactNode
}) {
  return (
    <section className="wrap sub-hero">
      <span className="pill" data-reveal="0">
        <span className="dot pulse" />
        {eyebrow}
      </span>
      <h1 data-reveal="80">{title}</h1>
      <p className="hero-lead" data-reveal="160">
        {lead}
      </p>
      {children && (
        <div className="hero-ctas" data-reveal="240">
          {children}
        </div>
      )}
    </section>
  )
}
