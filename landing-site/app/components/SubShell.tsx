import { Logo } from './Logo'
import { Reveal } from './Reveal'
import '../landing.css'
import '../sub.css'

import { CONTACT_EMAIL, mail } from './contact'
import { OrderButton } from './OrderButton'
import { siteHref } from '../seo/domains'
export { mail }

/** main = pages du .fr (locales, entreprise), info = .info, store = .store */
type Variant = 'main' | 'store' | 'info'

const NAV: Record<Variant, [string, string][]> = {
  main: [
    ['/#offres', 'Offres'],
    ['/agence-seo-local-yvelines/', 'Yvelines'],
    ['/agence-seo-local-eure-et-loir/', 'Eure-et-Loir'],
    ['/methode/', 'Méthode'],
    ['/info/', 'Ressources'],
  ],
  store: [
    ['/store/#packs', 'Packs'],
    ['/store/#abonnements', 'Abonnements'],
    ['/store/#materiel', 'Matériel avis'],
    ['/store/#faq', 'FAQ'],
  ],
  info: [
    ['/info/outil-gratuit/', 'Test gratuit'],
    ['/info/guides/', 'Guides métier'],
    ['/info/articles/', 'Articles'],
    ['/info/seo-aeo-geo/', 'SEO / GEO'],
    ['/info/guide-gratuit/', 'Guide PDF'],
  ],
}

const CTA: Record<Variant, [string, string]> = {
  main: ['/info/outil-gratuit/', 'Tester ma visibilité'],
  store: ['/store/#packs', 'Voir les packs'],
  info: ['/info/outil-gratuit/', 'Tester ma visibilité'],
}

export function SubShell({ variant, children }: { variant: Variant; children: React.ReactNode }) {
  const home = variant === 'store' ? '/store/' : variant === 'info' ? '/info/' : '/'
  const tag = variant === 'store' ? 'Boutique' : variant === 'info' ? 'Ressources' : null
  return (
    <div id="top" className="landing">
      <Reveal />
      <header className="site-header">
        <div className="wrap">
          <a href={siteHref(home)} className="brand" aria-label="Accueil">
            <Logo />
            {tag && <span className="brand-tag">{tag}</span>}
          </a>
          <nav className="main-nav" aria-label="Navigation principale">
            {NAV[variant].map(([href, label]) => (
              <a key={href} href={siteHref(href)}>
                {label}
              </a>
            ))}
          </nav>
          <a href={siteHref(CTA[variant][0])} className="btn btn-dark btn-header">
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
            <a href={siteHref('/')}>Découvrir l’offre complète →</a>
          </div>
          <div className="stack">
            <strong>Nos sites</strong>
            <a href={siteHref('/')}>pulse-locale-pme.fr</a>
            <a href={siteHref('/store/')}>Boutique (.store)</a>
            <a href={siteHref('/info/')}>Ressources (.info)</a>
            <a href={siteHref('/a-propos/')}>Qui sommes-nous</a>
          </div>
          <nav className="stack" aria-label="Zones desservies">
            <strong>Zones desservies</strong>
            <a href={siteHref('/agence-seo-local-yvelines/')}>Yvelines (78)</a>
            <a href={siteHref('/zones/yvelines/versailles/')}>Versailles</a>
            <a href={siteHref('/agence-seo-local-eure-et-loir/')}>Eure-et-Loir (28)</a>
            <a href={siteHref('/zones/eure-et-loir/chartres/')}>Chartres</a>
            <a href={siteHref('/methode/')}>Notre méthode</a>
          </nav>
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
            <a href={siteHref('/mentions-legales/#mentions')}>Mentions légales</a>
            <a href={siteHref('/mentions-legales/#cgv')}>CGV</a>
            <a href={siteHref('/mentions-legales/#rgpd')}>Confidentialité (RGPD)</a>
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
      <h1>{title}</h1>
      <p className="hero-lead">
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
