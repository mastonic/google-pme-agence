import { StatStrip } from './components/StatStrip'
import { ScrollReveal } from './components/ScrollReveal'

// ──────────────────────────────────────────────────────────────────
// PROVISOIRE — prix à valider avant mise en production.
// Pour modifier le tarif ou les conditions, changer uniquement
// cet objet. Ne pas toucher au reste du fichier.
// ──────────────────────────────────────────────────────────────────
const pricingConfig = {
  label: "Plan unique pour l'instant",
  price: "49",
  currency: "€",
  period: "/mois",
  conditions: ["sans engagement", "résiliable à tout moment", "7 jours d'essai"],
} as const
// ──────────────────────────────────────────────────────────────────

const CONTACT = {
  email: 'contact@holdmasto.com',
  tel: '0596 63 78 41',
  nomLegal: 'SASU HoldMasto',
} as const

// ── Données de contenu ────────────────────────────────────────────

const notions = [
  {
    term: "Identité numérique",
    def: "Tout ce que Google et vos clients voient de vous en ligne — fiche, site, avis, photos. Sans elle, vous n'existez pas dans une recherche.",
  },
  {
    term: "Fiche Google",
    def: "La carte de visite qui apparaît sur Maps et dans les recherches locales. Revendiquée et à jour, elle peut suffire à faire la différence avant même d'avoir un site.",
  },
  {
    term: "Avis clients",
    def: "La preuve qui rassure quelqu'un qui ne vous connaît pas encore. Sans avis récents, un commerce passe pour fermé ou peu fiable.",
  },
  {
    term: "Tunnel de revenu",
    def: "Chaque canal par lequel un client peut vous trouver et passer à l'achat. Moins de canaux ouverts, moins de clients qui arrivent jusqu'à vous.",
  },
] as const

const steps = [
  {
    num: "01",
    title: "Analyse de votre présence",
    desc: "On évalue votre visibilité actuelle et on identifie ce qui vous coûte des clients.",
  },
  {
    num: "02",
    title: "Création sur-mesure",
    desc: "On construit votre site et on optimise votre fiche, sans intervention technique de votre part.",
  },
  {
    num: "03",
    title: "Mise en ligne et suivi",
    desc: "Votre commerce devient trouvable, et on continue à l'entretenir dans le temps.",
  },
  {
    num: "04",
    title: "Vous gérez votre commerce, pas votre site",
    desc: "On s'occupe de tout.",
  },
] as const

const services = [
  "Site web professionnel adapté à votre activité",
  "Optimisation et suivi de votre fiche Google",
  "Hébergement et mises à jour inclus",
  "Accompagnement humain, pas un outil en libre-service",
] as const

// ── Composants utilitaires ────────────────────────────────────────

function MapPinIcon() {
  return (
    <svg width="22" height="30" viewBox="0 0 22 30" fill="none" aria-hidden="true">
      <path
        d="M11 1C5.477 1 1 5.477 1 11c0 8.5 10 19 10 19S21 19.5 21 11C21 5.477 16.523 1 11 1z"
        fill="#3C6358"
        fillOpacity="0.12"
        stroke="#3C6358"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <circle cx="11" cy="11" r="3.5" fill="#3C6358" fillOpacity="0.45" />
    </svg>
  )
}

function HeroPulse() {
  return (
    <div
      className="relative mx-auto mb-16 flex items-center justify-center"
      style={{ width: 210, height: 210 }}
      aria-hidden="true"
    >
      <div className="hero-pulse-ring absolute inset-0 rounded-full border-2 border-jade" />
      <div className="hero-pulse-ring hero-pulse-ring--delay absolute inset-0 rounded-full border border-jade" />
      <div className="absolute top-1/2 left-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-jade" />
      <div className="absolute bottom-1/2 left-1/2 -translate-x-1/2">
        <MapPinIcon />
      </div>
    </div>
  )
}

function PulseSeparator() {
  return (
    <div className="flex justify-center py-10" aria-hidden="true">
      <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
        <circle cx="15" cy="15" r="12" stroke="#3C6358" strokeWidth="0.75" opacity="0.18" />
        <circle cx="15" cy="15" r="7"  stroke="#3C6358" strokeWidth="1"    opacity="0.28" />
        <circle cx="15" cy="15" r="2.5" fill="#3C6358" opacity="0.5" />
      </svg>
    </div>
  )
}

// ── Page principale ───────────────────────────────────────────────

export default function Page() {
  return (
    <main>

      {/* ════════════════════════════════════════
          HERO
      ════════════════════════════════════════ */}
      <section className="bg-porcelaine px-6 pb-28 pt-36 sm:pb-36 sm:pt-44">
        <div className="mx-auto max-w-[680px] text-center">
          <p className="mb-10 font-mono text-[0.68rem] uppercase tracking-[0.28em] text-jade">
            Pulse‑PME
          </p>
          <HeroPulse />
          <h1 className="mb-6 font-display text-[2.5rem] font-medium leading-[1.1] tracking-[-0.01em] text-encre sm:text-[3.25rem]">
            Votre commerce existe.{' '}
            <span className="block sm:inline">Pour Google, pas encore.</span>
          </h1>
          <p className="mx-auto mb-12 max-w-[520px] text-[1.0625rem] leading-[1.72] text-encre/65">
            La plupart de vos clients cherchent en ligne avant de se déplacer.
            Pulse-PME donne à votre commerce la présence numérique qui les
            ramène chez vous — sans que vous ayez à vous en occuper.
          </p>
          <a
            href="#stats"
            className="inline-flex items-center gap-2 border-b border-jade/35 pb-px font-sans text-[0.9375rem] font-medium text-jade transition-colors hover:border-jade focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-jade focus-visible:ring-offset-4 focus-visible:ring-offset-porcelaine"
          >
            Voir comment ça marche
            <span aria-hidden="true" className="text-[0.8rem]">↓</span>
          </a>
        </div>
      </section>

      {/* ════════════════════════════════════════
          STATS — chiffres clés sur fond sombre
      ════════════════════════════════════════ */}
      <div id="stats">
        <StatStrip />
      </div>

      <PulseSeparator />

      {/* ════════════════════════════════════════
          NOTIONS — 4 définitions avec reveal décalé
      ════════════════════════════════════════ */}
      <section id="notions" className="bg-brume px-6 py-24 sm:py-32">
        <div className="mx-auto max-w-[680px]">
          <ScrollReveal>
            <h2 className="mb-14 font-display text-[1.875rem] font-normal leading-[1.2] text-encre sm:text-[2.25rem]">
              Quatre notions qui décident si un client vous trouve
            </h2>
          </ScrollReveal>
          <dl className="space-y-10">
            {notions.map(({ term, def }, i) => (
              <ScrollReveal key={term} delay={i * 90}>
                <div>
                  <dt className="mb-2 font-sans font-semibold text-jade">{term}</dt>
                  <dd className="leading-[1.75] text-encre/70">{def}</dd>
                </div>
              </ScrollReveal>
            ))}
          </dl>
        </div>
      </section>

      <PulseSeparator />

      {/* ════════════════════════════════════════
          MÉTHODE — étapes 01→04
      ════════════════════════════════════════ */}
      <section id="methode" className="bg-porcelaine px-6 py-24 sm:py-32">
        <div className="mx-auto max-w-[680px]">
          <ScrollReveal>
            <h2 className="mb-14 font-display text-[1.875rem] font-normal leading-[1.2] text-encre sm:text-[2.25rem]">
              Comment ça marche
            </h2>
          </ScrollReveal>
          <ol className="list-none divide-y divide-encre/[0.08]">
            {steps.map(({ num, title, desc }, i) => (
              <ScrollReveal key={num} delay={i * 80}>
                <li className="flex gap-7 py-8 sm:gap-10">
                  <span
                    className="shrink-0 font-mono text-[1.125rem] leading-7 tracking-wide text-jade/60"
                    aria-hidden="true"
                  >
                    {num}
                  </span>
                  <div>
                    <p className="mb-1.5 font-semibold text-encre">{title}</p>
                    <p className="leading-[1.72] text-encre/65">{desc}</p>
                  </div>
                </li>
              </ScrollReveal>
            ))}
          </ol>
        </div>
      </section>

      <PulseSeparator />

      {/* ════════════════════════════════════════
          INCLUS
      ════════════════════════════════════════ */}
      <section className="bg-brume px-6 py-24 sm:py-32">
        <div className="mx-auto max-w-[680px]">
          <ScrollReveal>
            <h2 className="mb-12 font-display text-[1.875rem] font-normal leading-[1.2] text-encre sm:text-[2.25rem]">
              Ce qui est inclus
            </h2>
          </ScrollReveal>
          <ul className="space-y-5">
            {services.map((service, i) => (
              <ScrollReveal key={service} delay={i * 80}>
                <li className="flex items-start gap-4">
                  <span className="mt-0.5 shrink-0 font-sans text-sm leading-6 text-jade" aria-hidden="true">
                    —
                  </span>
                  <span className="leading-[1.72] text-encre/80">{service}</span>
                </li>
              </ScrollReveal>
            ))}
          </ul>
        </div>
      </section>

      <PulseSeparator />

      {/* ════════════════════════════════════════
          OFFRE — tarif en IBM Plex Mono
      ════════════════════════════════════════ */}
      <section className="bg-porcelaine px-6 py-24 sm:py-32">
        <div className="mx-auto max-w-[680px]">
          <ScrollReveal>
            <h2 className="mb-12 font-display text-[1.875rem] font-normal leading-[1.2] text-encre sm:text-[2.25rem]">
              Une offre simple
            </h2>
          </ScrollReveal>
          <ScrollReveal delay={120}>
            <div className="mx-auto max-w-sm rounded-2xl border border-encre/[0.09] px-10 py-12 text-center sm:px-14">
              <p className="mb-5 text-sm tracking-wide text-encre/45">
                {pricingConfig.label}
              </p>
              <div className="mb-6 flex items-baseline justify-center gap-1">
                <span className="font-mono text-[3.75rem] leading-none tracking-tight text-encre">
                  {pricingConfig.price}
                </span>
                <span className="font-mono text-2xl leading-none text-encre/65">
                  {pricingConfig.currency}
                </span>
                <span className="ml-1 text-base text-encre/45">
                  {pricingConfig.period}
                </span>
              </div>
              <div className="flex flex-wrap justify-center gap-x-4 gap-y-2">
                {pricingConfig.conditions.map((c) => (
                  <span key={c} className="flex items-center gap-1.5 text-[0.8125rem] text-encre/50">
                    <span className="h-1 w-1 rounded-full bg-jade/50" aria-hidden="true" />
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      <PulseSeparator />

      {/* ════════════════════════════════════════
          À PROPOS — fond porcelaine, pas de faux témoignages
      ════════════════════════════════════════ */}
      <section className="bg-porcelaine px-6 py-24 sm:py-32">
        <div className="mx-auto max-w-[680px]">
          <ScrollReveal>
            <h2 className="mb-8 font-display text-[1.875rem] font-normal leading-[1.2] text-encre sm:text-[2.25rem]">
              Qui est derrière Pulse-PME
            </h2>
            <p className="text-[1.0625rem] leading-[1.82] text-encre/72">
              Pulse-PME est porté par Ludovic, indépendant basé en Martinique.
              Je travaille avec des commerces de proximité qui n&apos;ont ni le
              temps ni l&apos;envie de devenir des experts du numérique — c&apos;est
              tout l&apos;objet de Pulse-PME.
            </p>
          </ScrollReveal>
        </div>
      </section>

      <PulseSeparator />

      {/* ════════════════════════════════════════
          CTA FINAL — bouton laiton (seul usage)
      ════════════════════════════════════════ */}
      <section className="bg-brume px-6 py-24 sm:py-32">
        <ScrollReveal>
          <div className="mx-auto max-w-[680px] text-center">
            <h2 className="mb-10 font-display text-[1.875rem] font-normal leading-[1.2] text-encre sm:text-[2.5rem]">
              Votre commerce a-t-il l&apos;identité numérique qu&apos;il mérite ?
            </h2>
            <a
              href={`mailto:${CONTACT.email}`}
              className="inline-flex items-center gap-2 rounded-full bg-laiton px-8 py-4 font-sans text-[0.9375rem] font-semibold text-encre transition-opacity hover:opacity-88 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-laiton focus-visible:ring-offset-4 focus-visible:ring-offset-brume"
            >
              Demander mon analyse gratuite
            </a>
          </div>
        </ScrollReveal>
      </section>

      {/* ════════════════════════════════════════
          FOOTER
      ════════════════════════════════════════ */}
      <footer className="bg-encre px-6 py-12">
        <div className="mx-auto max-w-[680px] flex flex-col gap-3 text-sm text-porcelaine/50 sm:flex-row sm:items-center sm:justify-between">
          <p>
            <span className="font-medium text-porcelaine/75">Pulse-PME</span>
            {' — '}
            {CONTACT.nomLegal}, Martinique
          </p>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <a
              href={`mailto:${CONTACT.email}`}
              className="transition-colors hover:text-porcelaine/80 focus-visible:rounded focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-porcelaine/60"
            >
              {CONTACT.email}
            </a>
            <span aria-hidden="true">·</span>
            <span>{CONTACT.tel}</span>
          </div>
        </div>
      </footer>

    </main>
  )
}
