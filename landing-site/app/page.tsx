"use client"

import { useState } from "react"

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="8" r="8" fill="#00E5B4" fillOpacity="0.15"/>
    <path d="M4.5 8L7 10.5L11.5 6" stroke="#00E5B4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const XIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="8" r="8" fill="#ffffff" fillOpacity="0.05"/>
    <path d="M5.5 5.5L10.5 10.5M10.5 5.5L5.5 10.5" stroke="#ffffff" strokeOpacity="0.25" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
)

const plans = [
  {
    id: "essentiel",
    name: "Essentiel",
    tagline: "Soyez visible sur Google dès demain",
    price: 79,
    badge: null as null,
    color: "#4A9EFF",
    features: [
      { text: "Site IA généré & déployé en 24h", ok: true },
      { text: "Domaine .fr inclus 1ère année", ok: true },
      { text: "Hébergement + SSL sécurisé", ok: true },
      { text: "Fiche Google Business optimisée", ok: true },
      { text: "1 mise à jour par trimestre", ok: true },
      { text: "Support email 48h", ok: true },
      { text: "Régénération IA mensuelle", ok: false },
      { text: "Rapport visibilité Google", ok: false },
      { text: "SEO local actif", ok: false },
    ],
    cta: "Démarrer",
  },
  {
    id: "croissance",
    name: "Croissance",
    tagline: "Votre vitrine qui travaille pour vous",
    price: 149,
    badge: "Le plus choisi" as string | null,
    color: "#00E5B4",
    features: [
      { text: "Site IA généré & déployé en 24h", ok: true },
      { text: "Domaine .fr inclus 1ère année", ok: true },
      { text: "Hébergement + SSL sécurisé", ok: true },
      { text: "Fiche Google Business optimisée", ok: true },
      { text: "Régénération IA mensuelle", ok: true },
      { text: "Galerie photos IA secteur", ok: true },
      { text: "Rapport mensuel visibilité", ok: true },
      { text: "Intégration WhatsApp Business", ok: true },
      { text: "SEO local actif", ok: false },
    ],
    cta: "Choisir Croissance",
  },
  {
    id: "domination",
    name: "Domination Locale",
    tagline: "Écrasez vos concurrents sur Google",
    price: 299,
    badge: "Résultats garantis" as string | null,
    color: "#FFB347",
    features: [
      { text: "Tout le pack Croissance", ok: true },
      { text: "SEO local IA (mots-clés secteur)", ok: true },
      { text: "Publications Google 2×/semaine auto", ok: true },
      { text: "Campagne Google Ads pilotée IA", ok: true },
      { text: "Landing page saisonnière", ok: true },
      { text: "Tableau de bord analytics dédié", ok: true },
      { text: "Appel bilan mensuel 30 min", ok: true },
      { text: "Support WhatsApp direct", ok: true },
      { text: "Rapport concurrents locaux", ok: true },
    ],
    cta: "Dominer ma zone",
  },
]

const painPoints = [
  { icon: "📍", text: "Introuvable sur Google Maps" },
  { icon: "📱", text: "Pas de site ou site vieillissant" },
  { icon: "😤", text: "Vos concurrents captent vos clients" },
  { icon: "💸", text: "Agence web trop chère, trop lente" },
]

const stats = [
  { value: "97%", label: "des Français cherchent sur Google avant d'acheter local" },
  { value: "< 24h", label: "Pour être en ligne avec Local Pulse" },
  { value: "3×", label: "Plus de clients pour les PME visibles sur Google" },
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
    a: "Google envoie du trafic aux sites régulièrement mis à jour. C'est exactement ce que fait notre IA chaque mois pour vous — là où votre concurrent dort.",
  },
  {
    q: "\"Je peux arrêter quand je veux ?\"",
    a: "Oui. Sans préavis, sans frais de résiliation. Vous gardez votre domaine. On croit en notre service, pas aux contrats pièges.",
  },
]

const comparison = [
  { label: "Coût création",         agency: "1 500 – 4 000 €",    pulse: "Inclus dans l'abonnement" },
  { label: "Délai de mise en ligne", agency: "3 à 8 semaines",     pulse: "< 24 heures" },
  { label: "Mises à jour",           agency: "Facturées en +",     pulse: "IA automatique" },
  { label: "SEO local actif",        agency: "Option payante",     pulse: "Inclus dès Pro" },
  { label: "Suivi mensuel",          agency: "Rare / inexistant",  pulse: "Rapport dédié" },
]

export default function Page() {
  const [billingAnnual, setBillingAnnual] = useState(false)
  const [hoveredPlan, setHoveredPlan] = useState<string | null>(null)

  const getPrice = (base: number) => billingAnnual ? Math.round(base * 0.8) : base

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
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 12 }}>
            <div className="toggle-pill">
              <button className={`toggle-btn ${!billingAnnual ? "toggle-active" : "toggle-inactive"}`}
                onClick={() => setBillingAnnual(false)}>
                Mensuel
              </button>
              <button className={`toggle-btn ${billingAnnual ? "toggle-active" : "toggle-inactive"}`}
                onClick={() => setBillingAnnual(true)}>
                Annuel
              </button>
            </div>
            {billingAnnual && (
              <span style={{
                background: "#FFB34720", border: "1px solid #FFB34740",
                color: "#FFB347", borderRadius: 999, padding: "4px 12px", fontSize: 13, fontWeight: 600,
              }}>
                −20%
              </span>
            )}
          </div>
        </div>

        <div className="plans-grid" style={{ display: "flex", gap: 20, alignItems: "stretch" }}>
          {plans.map((plan) => {
            const isFeatured = plan.id === "croissance"
            return (
              <div
                key={plan.id}
                className={`plan-card ${isFeatured ? "featured-card" : ""}`}
                onMouseEnter={() => setHoveredPlan(plan.id)}
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
                    background: plan.color, color: "#060D17",
                    borderRadius: 999, padding: "5px 16px",
                    fontSize: 12, fontWeight: 700, whiteSpace: "nowrap", letterSpacing: "0.04em",
                  }}>
                    {plan.badge}
                  </div>
                )}
                <div style={{ marginBottom: 28 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 10,
                    background: `${plan.color}20`, border: `1px solid ${plan.color}40`,
                    marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    <div style={{ width: 12, height: 12, borderRadius: "50%", background: plan.color }} />
                  </div>
                  <div className="display" style={{ fontSize: 20, fontWeight: 800, color: "#fff", marginBottom: 6 }}>
                    {plan.name}
                  </div>
                  <div style={{ fontSize: 13, color: "#6B8099", lineHeight: 1.5 }}>{plan.tagline}</div>
                </div>
                <div style={{ marginBottom: 32 }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                    <span className="display" style={{ fontSize: 52, fontWeight: 800, color: plan.color }}>
                      {getPrice(plan.price)}€
                    </span>
                    <span style={{ fontSize: 14, color: "#6B8099" }}>/mois</span>
                  </div>
                  {billingAnnual && (
                    <div style={{ fontSize: 13, color: "#6B8099", marginTop: 4 }}>
                      <s style={{ color: "#4A5568" }}>{plan.price}€</s> · Facturé {getPrice(plan.price) * 12}€/an
                    </div>
                  )}
                </div>
                <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 12, marginBottom: 36, flex: 1 }}>
                  {plan.features.map((f, j) => (
                    <li key={j} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, color: f.ok ? "#C8D8E8" : "#2E3F52" }}>
                      {f.ok ? <CheckIcon /> : <XIcon />}
                      {f.text}
                    </li>
                  ))}
                </ul>
                <button className="cta-btn" style={{
                  background: isFeatured ? "#00E5B4" : "transparent",
                  color: isFeatured ? "#060D17" : plan.color,
                  border: `1.5px solid ${isFeatured ? "#00E5B4" : plan.color}`,
                }}>
                  {plan.cta} →
                </button>
              </div>
            )
          })}
        </div>

        {/* One-shot */}
        <div style={{
          marginTop: 40, background: "#080F1A", border: "1px solid #1A3050",
          borderRadius: 16, padding: "28px 36px",
          display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 20,
        }}>
          <div>
            <div style={{ fontSize: 13, color: "#6B8099", marginBottom: 6, letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 600 }}>
              Pas d&apos;abonnement ?
            </div>
            <div className="display" style={{ fontSize: 20, fontWeight: 800, color: "#fff" }}>Création unique disponible</div>
            <div style={{ fontSize: 14, color: "#6B8099", marginTop: 4 }}>
              Site livré une fois · Pas de mensuel · Mise à jour possible à la demande
            </div>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ textAlign: "center" }}>
              <div className="display" style={{ fontSize: 26, fontWeight: 800, color: "#4A9EFF" }}>490 €</div>
              <div style={{ fontSize: 12, color: "#6B8099" }}>Vitrine one-shot</div>
            </div>
            <div style={{ width: 1, background: "#1A3050" }} />
            <div style={{ textAlign: "center" }}>
              <div className="display" style={{ fontSize: 26, fontWeight: 800, color: "#FFB347" }}>790 €</div>
              <div style={{ fontSize: 12, color: "#6B8099" }}>Audit + Refonte IA</div>
            </div>
          </div>
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
            1 client de plus par mois{" "}
            <span style={{ color: "#00E5B4" }}>rembourse tout.</span>
          </h2>
          <p style={{ color: "#6B8099", fontSize: 16, marginBottom: 40, lineHeight: 1.65 }}>
            Votre concurrent le plus proche est peut-être déjà en train de configurer son compte.
            Ne leur laissez pas cette avance.
          </p>
          <button className="cta-btn" style={{
            background: "#00E5B4", color: "#060D17", fontSize: 17,
            padding: "18px 40px", width: "auto",
            boxShadow: "0 0 40px #00E5B430",
          }}>
            Créer mon site maintenant — dès 79 €/mois →
          </button>
          <div style={{ marginTop: 16, fontSize: 13, color: "#4A5568" }}>
            Sans engagement · Résiliable à tout moment · En ligne en 24h
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
        <span>© 2025 Local Pulse · Martinique, France</span>
        <span>Mentions légales · CGV</span>
      </footer>
    </div>
  )
}
