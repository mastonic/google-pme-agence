"use client"

import { useEffect, useState } from "react"

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="8" r="8" fill="#00E5B4" fillOpacity="0.15"/>
    <path d="M4.5 8L7 10.5L11.5 6" stroke="#00E5B4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

type ApiFeature = string | { text?: string; included?: boolean }
type ApiPlan = {
  slug: string
  name: string
  price: number
  badge?: string | null
  is_popular?: boolean
  features?: ApiFeature[]
}

const PLAN_VISUAL: Record<string, { tagline: string; color: string; cta: string }> = {
  starter: {
    tagline: "Une présence locale propre, professionnelle et suivie",
    color: "#4A9EFF",
    cta: "Découvrir Starter",
  },
  pro: {
    tagline: "Visibilité locale et suivi régulier de votre présence",
    color: "#00E5B4",
    cta: "Découvrir Pro",
  },
  elite: {
    tagline: "Accompagnement local renforcé et fonctionnalités avancées",
    color: "#FFB347",
    cta: "Découvrir Elite",
  },
}

const normalizeFeatures = (features: ApiFeature[] = []) =>
  features
    .filter((feature) => typeof feature === "string" || feature?.included !== false)
    .map((feature) => typeof feature === "string" ? feature : feature?.text)
    .filter(Boolean) as string[]


const painPoints = [
  { icon: "📍", text: "Introuvable sur Google Maps" },
  { icon: "📱", text: "Pas de site ou site vieillissant" },
  { icon: "😤", text: "Vos concurrents captent vos clients" },
  { icon: "💸", text: "Agence web trop chère, trop lente" },
]

const stats = [
  { value: "Audit", label: "de votre présence locale avant toute proposition" },
  { value: "Démo", label: "personnalisée pour visualiser les améliorations" },
  { value: "Suivi", label: "continu selon l'offre choisie" },
]

const faqs = [
  {
    q: "\"Mon site IA sera-t-il vraiment professionnel ?\"",
    a: "Généré sur mesure pour votre secteur d'activité, avec vos textes, vos couleurs, votre logo. Aucun template visible. Vos clients ne feront pas la différence — et c'est le but.",
  },
  {
    q: "\"Et si je veux changer quelque chose ?\"",
    a: "Depuis votre espace, vous nous signalez la modification. Elle est appliquée sous 48h. Pas de ticket, pas de devis surprise.",
  },
  {
    q: "\"Est-ce que ça marche vraiment pour attirer des clients ?\"",
    a: "L'objectif est d'améliorer les points concrets qui freinent votre présence locale : clarté du site, prise de contact, informations Google, avis et SEO local. Les résultats dépendent de votre marché, de votre zone et de la concurrence.",
  },
  {
    q: "\"Je peux arrêter quand je veux ?\"",
    a: "Oui. Sans préavis, sans frais de résiliation. Vous gardez votre domaine. On croit en notre service, pas aux contrats pièges.",
  },
]

const comparison = [
  { label: "Diagnostic initial",     agency: "Selon le prestataire", pulse: "Audit local inclus" },
  { label: "Démo avant décision",    agency: "Pas systématique",     pulse: "Démo personnalisée" },
  { label: "Mises à jour",           agency: "Selon contrat",         pulse: "Selon l'offre choisie" },
  { label: "SEO local",              agency: "Selon prestation",      pulse: "Intégré aux offres éligibles" },
  { label: "Suivi",                  agency: "Selon contrat",         pulse: "Pilotage Local Pulse" },
]

export default function Page() {
  const [plans, setPlans] = useState<ApiPlan[]>([])
  const [plansError, setPlansError] = useState(false)
  const [hoveredPlan, setHoveredPlan] = useState<string | null>(null)

  useEffect(() => {
    fetch("/plans")
      .then((response) => {
        if (!response.ok) throw new Error("plans unavailable")
        return response.json()
      })
      .then((data) => setPlans(Array.isArray(data) ? data : []))
      .catch(() => setPlansError(true))
  }, [])

  return (
    <div style={{
      fontFamily: "'Inter', -apple-system, sans-serif",
      background: "#060D17",
      color: "#E8EDF2",
      minHeight: "100vh",
      overflowX: "hidden",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        .display { font-family: 'Syne', sans-serif; }
        @keyframes pulse-ring {
          0% { transform: scale(1); opacity: 0.6; }
          100% { transform: scale(2.2); opacity: 0; }
        }
        @keyframes glow-border {
          0%, 100% { box-shadow: 0 0 20px #00E5B440, 0 0 60px #00E5B415; }
          50% { box-shadow: 0 0 30px #00E5B460, 0 0 80px #00E5B425; }
        }
        @keyframes fade-up {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .fade-up   { animation: fade-up 0.7s ease both; }
        .fade-up-2 { animation: fade-up 0.7s ease 0.15s both; }
        .fade-up-3 { animation: fade-up 0.7s ease 0.3s both; }
        .pulse-dot {
          position: relative; display: inline-block;
          width: 12px; height: 12px; border-radius: 50%; background: #00E5B4;
        }
        .pulse-dot::before, .pulse-dot::after {
          content: ''; position: absolute; inset: 0;
          border-radius: 50%; background: #00E5B4;
          animation: pulse-ring 2s ease-out infinite;
        }
        .pulse-dot::after { animation-delay: 1s; }
        .plan-card { transition: transform 0.25s ease, box-shadow 0.25s ease; cursor: default; }
        .plan-card:hover { transform: translateY(-6px); }
        .featured-card { animation: glow-border 3s ease infinite; }
        .toggle-pill {
          display: flex; align-items: center;
          background: #0F1D2B; border-radius: 999px; padding: 4px; border: 1px solid #1A3050;
        }
        .toggle-btn {
          padding: 8px 20px; border-radius: 999px; border: none; cursor: pointer;
          font-size: 14px; font-weight: 500; transition: all 0.2s;
        }
        .toggle-active  { background: #00E5B4; color: #060D17; }
        .toggle-inactive { background: transparent; color: #6B8099; }
        .cta-btn {
          border: none; border-radius: 10px; padding: 14px 24px;
          font-size: 15px; font-weight: 600; cursor: pointer;
          width: 100%; transition: all 0.2s; letter-spacing: 0.01em;
        }
        .cta-btn:hover { transform: scale(1.02); }
        .pain-chip {
          display: flex; align-items: center; gap: 10px;
          background: #0F1D2B; border: 1px solid #1A3050;
          border-radius: 12px; padding: 14px 18px;
          font-size: 14px; color: #8AA3BE;
        }
        .stat-block {
          text-align: center; padding: 32px 24px;
          border-right: 1px solid #1A3050;
        }
        .stat-block:last-child { border-right: none; }
        .section-eyebrow {
          display: inline-flex; align-items: center; gap: 8px;
          background: #00E5B415; border: 1px solid #00E5B430;
          border-radius: 999px; padding: 6px 14px;
          font-size: 12px; font-weight: 600; color: #00E5B4;
          letter-spacing: 0.08em; text-transform: uppercase;
        }
        .comparison-row {
          display: flex; justify-content: space-between; align-items: center;
          padding: 16px 0; border-bottom: 1px solid #0F1D2B; font-size: 14px;
        }
        .objection-card {
          background: #0F1D2B; border: 1px solid #1A3050;
          border-radius: 16px; padding: 24px;
        }
        @media (max-width: 768px) {
          .plans-grid { flex-direction: column !important; }
          .stats-row  { flex-direction: column !important; }
          .stat-block { border-right: none !important; border-bottom: 1px solid #1A3050; }
          .hero-h1    { font-size: 36px !important; }
          .problem-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>

      {/* NAV */}
      <nav style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "20px 48px", borderBottom: "1px solid #0F1D2B",
        position: "sticky", top: 0, zIndex: 100,
        background: "rgba(6,13,23,0.92)", backdropFilter: "blur(12px)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span className="pulse-dot" />
          <span className="display" style={{ fontSize: 20, fontWeight: 800, color: "#fff" }}>
            Local<span style={{ color: "#00E5B4" }}>Pulse</span>
          </span>
        </div>
        <button className="cta-btn" style={{
          background: "#00E5B4", color: "#060D17", width: "auto", padding: "10px 24px", fontSize: 14,
        }}>
          Démarrer maintenant →
        </button>
      </nav>

      {/* HERO */}
      <section style={{ padding: "96px 48px 80px", maxWidth: 1100, margin: "0 auto" }}>
        <div className="fade-up" style={{ marginBottom: 24 }}>
          <span className="section-eyebrow">
            <span className="pulse-dot" style={{ width: 8, height: 8 }} />
            Présence web IA pour PMEs locales
          </span>
        </div>
        <h1 className="display fade-up-2 hero-h1" style={{
          fontSize: 58, fontWeight: 800, lineHeight: 1.08,
          color: "#fff", marginBottom: 28, maxWidth: 780,
        }}>
          Pendant que vous travaillez,<br />
          <span style={{ color: "#00E5B4" }}>Google vous envoie des clients.</span>
        </h1>
        <p className="fade-up-3" style={{
          fontSize: 18, color: "#6B8099", maxWidth: 560, lineHeight: 1.65, marginBottom: 52,
        }}>
          Chaque jour sans site pro, vos concurrents prennent vos clients.
          Local Pulse génère et pilote votre présence web en 24h — sans agence, sans effort.
        </p>

        <div style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 12, marginBottom: 72,
        }}>
          {painPoints.map((p, i) => (
            <div key={i} className="pain-chip">
              <span style={{ fontSize: 20 }}>{p.icon}</span>
              {p.text}
            </div>
          ))}
        </div>

        <div className="stats-row" style={{
          display: "flex", background: "#0A1622",
          border: "1px solid #1A3050", borderRadius: 20, overflow: "hidden",
        }}>
          {stats.map((s, i) => (
            <div key={i} className="stat-block" style={{ flex: 1 }}>
              <div className="display" style={{ fontSize: 40, fontWeight: 800, color: "#00E5B4", marginBottom: 8 }}>
                {s.value}
              </div>
              <div style={{ fontSize: 13, color: "#6B8099", lineHeight: 1.5 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* PROBLÈME → SOLUTION */}
      <section style={{
        background: "#080F1A", borderTop: "1px solid #0F1D2B",
        borderBottom: "1px solid #0F1D2B", padding: "80px 48px",
      }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <div className="problem-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 64, alignItems: "center" }}>
            <div>
              <span className="section-eyebrow" style={{ marginBottom: 24, display: "inline-flex" }}>
                La réalité du terrain
              </span>
              <h2 className="display" style={{ fontSize: 34, fontWeight: 800, color: "#fff", marginBottom: 20, lineHeight: 1.2 }}>
                80% des PMEs locales perdent des clients{" "}
                <span style={{ color: "#FFB347" }}>faute de visibilité.</span>
              </h2>
              <p style={{ color: "#6B8099", lineHeight: 1.7, fontSize: 15, marginBottom: 28 }}>
                Un client cherche un plombier, une coiffeuse, un restaurant à Fort-de-France.
                Il tape sur Google. Si vous n&apos;apparaissez pas dans les 3 premiers résultats —
                il appelle votre concurrent.
              </p>
              <p style={{ color: "#6B8099", lineHeight: 1.7, fontSize: 15 }}>
                Les agences web demandent 2 000 à 4 000 € et 6 semaines. Vous méritez mieux.
              </p>
            </div>
            <div>
              <div style={{ background: "#0F1D2B", border: "1px solid #1A3050", borderRadius: 16, padding: "28px 32px" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#6B8099", marginBottom: 20, letterSpacing: "0.06em", textTransform: "uppercase" }}>
                  Comparaison réelle
                </div>
                {comparison.map((row, i) => (
                  <div key={i} className="comparison-row">
                    <span style={{ color: "#8AA3BE", minWidth: 160 }}>{row.label}</span>
                    <span style={{ color: "#4A5568", fontSize: 13, textAlign: "right", marginRight: 20 }}>{row.agency}</span>
                    <span style={{ color: "#00E5B4", fontSize: 13, textAlign: "right", fontWeight: 600, minWidth: 160 }}>{row.pulse}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section style={{ padding: "96px 48px", maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: 56 }}>
          <span className="section-eyebrow" style={{ marginBottom: 20, display: "inline-flex" }}>
            Tarifs transparents
          </span>
          <h2 className="display" style={{ fontSize: 44, fontWeight: 800, color: "#fff", marginBottom: 16 }}>
            Choisissez votre niveau de{" "}
            <span style={{ color: "#00E5B4" }}>croissance</span>
          </h2>
          <p style={{ color: "#6B8099", fontSize: 16, marginBottom: 36 }}>
            Sans engagement. Sans mauvaise surprise. Résiliable à tout moment.
          </p>
          <p style={{ color: "#4A5568", fontSize: 13 }}>
            Les offres et tarifs ci-dessous sont synchronisés avec notre grille active.
          </p>
        </div>

        {plansError && (
          <div style={{ textAlign: "center", color: "#FFB347", marginBottom: 24, fontSize: 14 }}>
            Les tarifs sont momentanément indisponibles. Contactez-nous pour une proposition adaptée.
          </div>
        )}

        <div className="plans-grid" style={{ display: "flex", gap: 20, alignItems: "stretch" }}>
          {plans.map((plan) => {
            const visual = PLAN_VISUAL[plan.slug] || PLAN_VISUAL.starter
            const isFeatured = Boolean(plan.is_popular)
            const features = normalizeFeatures(plan.features)
            return (
              <div
                key={plan.slug}
                className={`plan-card ${isFeatured ? "featured-card" : ""}`}
                onMouseEnter={() => setHoveredPlan(plan.slug)}
                onMouseLeave={() => setHoveredPlan(null)}
                style={{
                  flex: 1,
                  background: isFeatured ? "#0C1C2E" : "#080F1A",
                  border: `1px solid ${isFeatured ? "#00E5B440" : "#1A3050"}`,
                  borderRadius: 20, padding: "36px 28px",
                  display: "flex", flexDirection: "column", position: "relative",
                  transform: isFeatured ? "scale(1.03)" : "scale(1)",
                }}
              >
                {plan.badge && (
                  <div style={{
                    position: "absolute", top: -14, left: "50%", transform: "translateX(-50%)",
                    background: visual.color, color: "#060D17",
                    borderRadius: 999, padding: "5px 16px",
                    fontSize: 12, fontWeight: 700, whiteSpace: "nowrap", letterSpacing: "0.04em",
                  }}>
                    {plan.badge}
                  </div>
                )}
                <div style={{ marginBottom: 28 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 10,
                    background: `${visual.color}20`, border: `1px solid ${visual.color}40`,
                    marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    <div style={{ width: 12, height: 12, borderRadius: "50%", background: visual.color }} />
                  </div>
                  <div className="display" style={{ fontSize: 20, fontWeight: 800, color: "#fff", marginBottom: 6 }}>
                    {plan.name}
                  </div>
                  <div style={{ fontSize: 13, color: "#6B8099", lineHeight: 1.5 }}>{visual.tagline}</div>
                </div>
                <div style={{ marginBottom: 32 }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                    <span className="display" style={{ fontSize: 52, fontWeight: 800, color: visual.color }}>
                      {plan.price}€
                    </span>
                    <span style={{ fontSize: 14, color: "#6B8099" }}>/mois</span>
                  </div>
                </div>
                <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 12, marginBottom: 36, flex: 1 }}>
                  {features.map((feature, j) => (
                    <li key={j} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, color: "#C8D8E8" }}>
                      <CheckIcon />
                      {feature}
                    </li>
                  ))}
                </ul>
                <button className="cta-btn" style={{
                  background: isFeatured ? "#00E5B4" : "transparent",
                  color: isFeatured ? "#060D17" : visual.color,
                  border: `1.5px solid ${isFeatured ? "#00E5B4" : visual.color}`,
                }}>
                  {visual.cta} →
                </button>
              </div>
            )
          })}
        </div>

      </section>

      {/* OBJECTIONS */}
      <section style={{ background: "#080F1A", borderTop: "1px solid #0F1D2B", padding: "80px 48px" }}>
        <div style={{ maxWidth: 900, margin: "0 auto" }}>
          <h2 className="display" style={{ fontSize: 34, fontWeight: 800, color: "#fff", textAlign: "center", marginBottom: 48 }}>
            Vos questions, nos réponses honnêtes
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))", gap: 16 }}>
            {faqs.map((faq, i) => (
              <div key={i} className="objection-card">
                <div style={{ fontSize: 14, fontWeight: 600, color: "#00E5B4", marginBottom: 12, lineHeight: 1.4 }}>
                  {faq.q}
                </div>
                <div style={{ fontSize: 14, color: "#6B8099", lineHeight: 1.65 }}>{faq.a}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA FINAL */}
      <section style={{ padding: "96px 48px", textAlign: "center" }}>
        <div style={{ maxWidth: 640, margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "center", marginBottom: 24 }}>
            <span className="pulse-dot" style={{ width: 18, height: 18 }} />
          </div>
          <h2 className="display" style={{ fontSize: 46, fontWeight: 800, color: "#fff", marginBottom: 20, lineHeight: 1.1 }}>
            Voyez ce que votre présence locale{" "}
            <span style={{ color: "#00E5B4" }}>peut améliorer.</span>
          </h2>
          <p style={{ color: "#6B8099", fontSize: 16, marginBottom: 40, lineHeight: 1.65 }}>
            Nous partons de votre situation actuelle, préparons une démo personnalisée et vous montrons les améliorations concrètes avant toute décision.
          </p>
          <button className="cta-btn" style={{
            background: "#00E5B4", color: "#060D17", fontSize: 17,
            padding: "18px 40px", width: "auto",
            boxShadow: "0 0 40px #00E5B430",
          }}>
            Demander ma démo personnalisée →
          </button>
          <div style={{ marginTop: 16, fontSize: 13, color: "#4A5568" }}>
            Échange sans engagement · Proposition adaptée à votre activité
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{
        borderTop: "1px solid #0F1D2B", padding: "32px 48px",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        color: "#4A5568", fontSize: 13,
      }}>
        <span className="display" style={{ fontWeight: 800, color: "#1A3050" }}>
          Local<span style={{ color: "#00E5B420" }}>Pulse</span>
        </span>
        <span>© 2026 Local Pulse · France</span>
        <span>Mentions légales · CGV</span>
      </footer>
    </div>
  )
}
