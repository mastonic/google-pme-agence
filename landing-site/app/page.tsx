"use client"

import { useState } from "react"

const plans = [
  {
    name: "Starter",
    price: 49,
    subtitle: "Une présence web propre et rassurante.",
    features: [
      "Site vitrine professionnel jusqu’à 5 pages",
      "Hébergement, SSL et maintenance technique",
      "Téléphone, WhatsApp, formulaire et informations pratiques",
      "Supervision du site",
      "1 petite modification de contenu par mois",
    ],
  },
  {
    name: "Pro",
    price: 149,
    subtitle: "Pour être mieux trouvé et générer plus de contacts locaux.",
    popular: true,
    features: [
      "Tout Starter",
      "Nom de domaine personnalisé",
      "SEO local et pages prioritaires",
      "Optimisation de la fiche Google Business",
      "Suivi des appels, WhatsApp et demandes de contact",
    ],
  },
  {
    name: "Élite",
    price: 299,
    subtitle: "Pour automatiser davantage votre acquisition et votre suivi.",
    features: [
      "Tout Pro",
      "SEO avancé et contenus réguliers",
      "Chatbot IA / assistant WhatsApp selon besoin",
      "Automatisation des demandes d’avis",
      "Optimisations mensuelles de conversion",
    ],
  },
]

const faq = [
  {
    q: "Pulse-PME est-il une vraie entreprise ?",
    a: "Pulse-PME est une solution commerciale exploitée par HoldMasto, société française immatriculée au RCS de Fort-de-France sous le numéro 106 121 536.",
  },
  {
    q: "Pourquoi ai-je reçu une démo sans l’avoir demandée ?",
    a: "Nous pouvons préparer une démonstration à partir d’informations professionnelles déjà publiques afin de vous montrer concrètement ce qui pourrait être amélioré. Rien n’est publié sur votre domaine sans votre accord.",
  },
  {
    q: "Suis-je obligé de souscrire après avoir vu la démo ?",
    a: "Non. La démonstration sert uniquement à vous permettre de juger le résultat avant de décider.",
  },
  {
    q: "Qui s’occupe du site après la mise en ligne ?",
    a: "Selon la formule choisie, Pulse-PME gère l’hébergement, la maintenance, les modifications prévues au forfait et les services de visibilité associés.",
  },
  {
    q: "Puis-je arrêter l’abonnement ?",
    a: "Les abonnements sont mensuels et sans engagement. Les conditions précises sont présentées avant tout paiement.",
  },
]

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" aria-hidden="true">
      <path d="M12 3 19 6v5c0 4.8-2.8 8.1-7 10-4.2-1.9-7-5.2-7-10V6l7-3Z" stroke="currentColor" strokeWidth="1.8"/>
      <path d="m8.8 12 2 2 4.6-4.7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

export default function Page() {
  const [openFaq, setOpenFaq] = useState<number | null>(0)

  return (
    <main className="site-shell">
      <style>{`
        :root {
          --bg: #07111f;
          --panel: #0b1728;
          --panel-2: #0f1d30;
          --line: rgba(255,255,255,.09);
          --text: #f4f7fb;
          --muted: #96a8bd;
          --brand: #38d6b0;
          --brand-2: #82f0d2;
          --accent: #66a7ff;
          --warm: #f8c56f;
        }
        * { box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body { margin: 0; }
        .site-shell {
          min-height: 100vh;
          background:
            radial-gradient(circle at 10% -10%, rgba(56,214,176,.13), transparent 32rem),
            radial-gradient(circle at 92% 15%, rgba(102,167,255,.10), transparent 28rem),
            var(--bg);
          color: var(--text);
          font-family: var(--font-work-sans), Inter, system-ui, sans-serif;
        }
        a { color: inherit; text-decoration: none; }
        .wrap { width: min(1160px, calc(100% - 40px)); margin: 0 auto; }
        .nav {
          position: sticky; top: 0; z-index: 30;
          backdrop-filter: blur(16px);
          background: rgba(7,17,31,.82);
          border-bottom: 1px solid var(--line);
        }
        .nav-inner { height: 76px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
        .brand { display: flex; align-items: center; gap: 11px; font-weight: 700; letter-spacing: -.02em; }
        .brand-mark {
          width: 34px; height: 34px; border-radius: 11px;
          display: grid; place-items: center;
          background: linear-gradient(145deg, rgba(56,214,176,.25), rgba(102,167,255,.18));
          border: 1px solid rgba(56,214,176,.3);
          color: var(--brand);
        }
        .brand-sub { color: var(--muted); font-weight: 500; font-size: 12px; display: block; margin-top: 1px; }
        .nav-links { display: flex; align-items: center; gap: 26px; color: var(--muted); font-size: 14px; }
        .nav-links a:hover { color: white; }
        .btn {
          display: inline-flex; align-items: center; justify-content: center; gap: 8px;
          border-radius: 12px; padding: 12px 18px; font-weight: 650; font-size: 14px;
          transition: transform .2s ease, border-color .2s ease, background .2s ease;
        }
        .btn:hover { transform: translateY(-1px); }
        .btn-primary { background: var(--brand); color: #052019; }
        .btn-secondary { border: 1px solid var(--line); background: rgba(255,255,255,.03); color: white; }
        .hero { padding: 92px 0 72px; }
        .eyebrow {
          display: inline-flex; align-items: center; gap: 9px;
          border: 1px solid rgba(56,214,176,.25);
          background: rgba(56,214,176,.08);
          color: var(--brand-2);
          padding: 7px 12px; border-radius: 999px; font-size: 12px; font-weight: 650;
        }
        h1,h2,h3 { font-family: var(--font-petrona), Georgia, serif; letter-spacing: -.035em; margin: 0; }
        h1 { font-size: clamp(44px, 7vw, 76px); line-height: .98; max-width: 920px; font-weight: 600; margin-top: 24px; }
        .hero-accent { color: var(--brand); }
        .hero-copy { max-width: 720px; color: var(--muted); font-size: 18px; line-height: 1.7; margin: 28px 0 0; }
        .hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 34px; }
        .trust-strip {
          margin-top: 54px; display: grid; grid-template-columns: repeat(4,1fr);
          border: 1px solid var(--line); border-radius: 18px; overflow: hidden;
          background: rgba(255,255,255,.025);
        }
        .trust-item { padding: 20px; border-right: 1px solid var(--line); }
        .trust-item:last-child { border-right: 0; }
        .trust-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
        .trust-value { margin-top: 7px; font-size: 14px; font-weight: 650; }
        .section { padding: 86px 0; border-top: 1px solid var(--line); }
        .section-head { max-width: 720px; margin-bottom: 36px; }
        .section-head h2 { font-size: clamp(34px, 5vw, 52px); line-height: 1.04; }
        .section-head p { color: var(--muted); font-size: 16px; line-height: 1.7; margin: 16px 0 0; }
        .proof-grid { display: grid; grid-template-columns: 1.1fr .9fr; gap: 22px; }
        .card {
          border: 1px solid var(--line); background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.018));
          border-radius: 20px; padding: 28px;
        }
        .card h3 { font-size: 26px; }
        .card p { color: var(--muted); line-height: 1.7; }
        .legal-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 10px; margin-top: 24px; }
        .legal-row { padding: 14px; border-radius: 12px; background: rgba(255,255,255,.025); border: 1px solid rgba(255,255,255,.06); }
        .legal-row span { display:block; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 5px; }
        .legal-row strong { font-size: 14px; }
        .steps { display:grid; grid-template-columns: repeat(4,1fr); gap: 14px; }
        .step-num { font-family: var(--font-ibm-plex-mono), monospace; font-size: 12px; color: var(--brand); margin-bottom: 20px; }
        .step h3 { font-size: 22px; }
        .step p { margin: 10px 0 0; color: var(--muted); line-height: 1.65; font-size: 14px; }
        .demo-box {
          display:grid; grid-template-columns: 1fr 1fr; gap: 34px; align-items:center;
          background: linear-gradient(135deg, rgba(56,214,176,.08), rgba(102,167,255,.06));
          border: 1px solid rgba(56,214,176,.2); border-radius: 24px; padding: 36px;
        }
        .demo-window { border:1px solid var(--line); border-radius:16px; background:#081523; overflow:hidden; box-shadow:0 26px 80px rgba(0,0,0,.25); }
        .demo-bar { height:38px; display:flex; align-items:center; gap:6px; padding:0 12px; border-bottom:1px solid var(--line); }
        .dot { width:8px; height:8px; border-radius:50%; background:#26374a; }
        .demo-content { padding:24px; }
        .skeleton { height:10px; border-radius:999px; background:linear-gradient(90deg,#16283b,#24425d); margin-bottom:10px; }
        .pricing { display:grid; grid-template-columns: repeat(3,1fr); gap: 16px; }
        .price-card { position:relative; }
        .popular { border-color: rgba(56,214,176,.45); box-shadow:0 0 0 1px rgba(56,214,176,.08), 0 28px 80px rgba(0,0,0,.17); }
        .badge { position:absolute; right:18px; top:18px; font-size:11px; color:#06241d; background:var(--brand); padding:6px 9px; border-radius:999px; font-weight:700; }
        .price { font-size:42px; font-family:var(--font-petrona),serif; margin:18px 0 4px; }
        .price small { font:500 13px var(--font-work-sans),sans-serif; color:var(--muted); }
        .feature-list { list-style:none; padding:0; margin:24px 0 0; display:grid; gap:12px; }
        .feature-list li { color:#c8d5e4; font-size:14px; display:flex; gap:10px; align-items:flex-start; }
        .check { color:var(--brand); }
        .faq { display:grid; gap:10px; max-width:900px; }
        .faq button {
          width:100%; color:white; background:rgba(255,255,255,.025); border:1px solid var(--line);
          border-radius:14px; padding:18px 20px; text-align:left; cursor:pointer; display:flex; justify-content:space-between; gap:20px;
          font:600 15px var(--font-work-sans),sans-serif;
        }
        .faq-answer { color:var(--muted); line-height:1.7; padding:0 20px 18px; margin-top:-4px; }
        .contact-panel {
          display:flex; justify-content:space-between; gap:30px; align-items:center;
          border:1px solid rgba(56,214,176,.25); border-radius:24px; padding:34px;
          background:rgba(56,214,176,.055);
        }
        .footer { border-top:1px solid var(--line); padding:36px 0 44px; color:var(--muted); font-size:12px; }
        .footer-grid { display:grid; grid-template-columns:1.4fr 1fr 1fr; gap:30px; }
        .footer strong { color:#dfe8f3; }
        @media (max-width: 900px) {
          .nav-links { display:none; }
          .trust-strip { grid-template-columns:1fr 1fr; }
          .trust-item:nth-child(2) { border-right:0; }
          .trust-item:nth-child(-n+2) { border-bottom:1px solid var(--line); }
          .proof-grid,.demo-box { grid-template-columns:1fr; }
          .steps { grid-template-columns:1fr 1fr; }
          .pricing { grid-template-columns:1fr; }
        }
        @media (max-width: 620px) {
          .wrap { width:min(100% - 24px,1160px); }
          .nav-inner { height:68px; }
          .nav .btn-primary { display:none; }
          .hero { padding:64px 0 52px; }
          .hero-copy { font-size:16px; }
          .trust-strip,.steps,.legal-grid { grid-template-columns:1fr; }
          .trust-item { border-right:0; border-bottom:1px solid var(--line); }
          .trust-item:last-child { border-bottom:0; }
          .section { padding:64px 0; }
          .card,.demo-box,.contact-panel { padding:22px; }
          .contact-panel { align-items:flex-start; flex-direction:column; }
          .footer-grid { grid-template-columns:1fr; }
        }
      `}</style>

      <nav className="nav">
        <div className="wrap nav-inner">
          <a className="brand" href="#top">
            <span className="brand-mark"><ShieldIcon /></span>
            <span>
              Pulse‑PME
              <span className="brand-sub">une solution de HoldMasto</span>
            </span>
          </a>
          <div className="nav-links">
            <a href="#societe">Qui sommes-nous ?</a>
            <a href="#fonctionnement">Comment ça marche</a>
            <a href="#offres">Offres</a>
            <a href="#faq">FAQ</a>
          </div>
          <a className="btn btn-primary" href="mailto:rigahludovic@gmail.com?subject=Pulse-PME%20-%20Demande%20d%27information">
            Nous contacter <ArrowIcon />
          </a>
        </div>
      </nav>

      <section className="hero" id="top">
        <div className="wrap">
          <span className="eyebrow"><ShieldIcon /> Service numérique français · HoldMasto</span>
          <h1>
            Votre présence locale, <span className="hero-accent">gérée sérieusement.</span>
          </h1>
          <p className="hero-copy">
            Pulse‑PME conçoit et exploite des sites et services de visibilité locale pour les TPE et PME.
            Vous pouvez voir une démo avant de décider, comprendre exactement ce qui est inclus,
            et savoir quelle société se trouve derrière le service.
          </p>
          <div className="hero-actions">
            <a className="btn btn-primary" href="#societe">Vérifier qui est derrière Pulse‑PME <ArrowIcon /></a>
            <a className="btn btn-secondary" href="#offres">Voir les offres</a>
          </div>

          <div className="trust-strip">
            <div className="trust-item">
              <div className="trust-label">Société éditrice</div>
              <div className="trust-value">HoldMasto</div>
            </div>
            <div className="trust-item">
              <div className="trust-label">Immatriculation</div>
              <div className="trust-value">RCS Fort‑de‑France 106 121 536</div>
            </div>
            <div className="trust-item">
              <div className="trust-label">Statut</div>
              <div className="trust-value">SASU française</div>
            </div>
            <div className="trust-item">
              <div className="trust-label">Paiements</div>
              <div className="trust-value">Stripe · abonnement mensuel</div>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="societe">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">Identité vérifiable</span>
            <h2>Pulse‑PME n’est pas une page anonyme.</h2>
            <p>
              Pulse‑PME est une solution éditée et opérée par HoldMasto, société immatriculée en France.
              HoldMasto exerce notamment des activités de développement de sites internet, logiciels,
              plateformes et systèmes digitaux pour professionnels.
            </p>
          </div>

          <div className="proof-grid">
            <div className="card">
              <h3>HoldMasto</h3>
              <p>
                Société par actions simplifiée unipersonnelle. Pulse‑PME s’inscrit dans l’activité numérique
                de HoldMasto et constitue une offre de services destinée aux entreprises locales.
              </p>
              <div className="legal-grid">
                <div className="legal-row"><span>Raison sociale</span><strong>HoldMasto</strong></div>
                <div className="legal-row"><span>RCS</span><strong>106 121 536 · Fort‑de‑France</strong></div>
                <div className="legal-row"><span>Siège social</span><strong>2 Impasse Bacouna, 97231 Le Robert</strong></div>
                <div className="legal-row"><span>Président</span><strong>Ludovic Rigah</strong></div>
                <div className="legal-row"><span>Forme</span><strong>SASU</strong></div>
                <div className="legal-row"><span>Capital social</span><strong>10 €</strong></div>
              </div>
            </div>

            <div className="card">
              <h3>Pourquoi cette transparence ?</h3>
              <p>
                Un dirigeant doit pouvoir vérifier à qui il confie son image, son site et ses données.
                C’est pourquoi nous affichons clairement la société éditrice, notre mode de fonctionnement,
                nos tarifs et nos coordonnées.
              </p>
              <p>
                Si vous avez reçu une démo Pulse‑PME, vous pouvez la consulter sans engagement.
                Aucun site n’est basculé sur votre domaine et aucun abonnement n’est activé sans votre action.
              </p>
              <a className="btn btn-secondary" href="mailto:rigahludovic@gmail.com?subject=V%C3%A9rification%20Pulse-PME" style={{marginTop: 8}}>
                Poser une question à HoldMasto
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="fonctionnement">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">Fonctionnement</span>
            <h2>Vous voyez le résultat avant de vous engager.</h2>
            <p>
              Notre approche est simple : analyser la présence publique du commerce, préparer une proposition concrète,
              vous laisser juger le résultat, puis activer uniquement les services que vous choisissez.
            </p>
          </div>

          <div className="steps">
            {[
              ["01","Analyse","Nous analysons les informations professionnelles disponibles et les points de friction visibles."],
              ["02","Démo","Une démonstration personnalisée peut être préparée pour vous montrer le résultat attendu."],
              ["03","Validation","Vous vérifiez les informations, le design et les services souhaités avant toute mise en production."],
              ["04","Exploitation","Après souscription, Pulse‑PME prend en charge les services inclus dans votre formule."],
            ].map(([n,t,d]) => (
              <div className="card step" key={n}>
                <div className="step-num">{n}</div>
                <h3>{t}</h3>
                <p>{d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="demo-box">
            <div>
              <span className="eyebrow">Vous avez reçu une démo ?</span>
              <h2 style={{fontSize:"clamp(34px,5vw,50px)", marginTop:18}}>Elle a été préparée pour vous permettre de juger sur pièce.</h2>
              <p style={{color:"var(--muted)", lineHeight:1.7, marginTop:18}}>
                Le lien de démonstration montre ce que Pulse‑PME peut mettre en place pour votre activité.
                Vous pouvez simplement le consulter. Si vous souhaitez avancer, l’étape suivante consiste à
                valider vos informations, votre logo, vos photos et les services à activer.
              </p>
            </div>
            <div className="demo-window" aria-hidden="true">
              <div className="demo-bar"><span className="dot"/><span className="dot"/><span className="dot"/></div>
              <div className="demo-content">
                <div className="skeleton" style={{width:"42%",height:12}}/>
                <div className="skeleton" style={{width:"86%",height:22,marginTop:24}}/>
                <div className="skeleton" style={{width:"72%",height:22}}/>
                <div className="skeleton" style={{width:"55%",marginTop:24}}/>
                <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginTop:26}}>
                  <div style={{height:110,borderRadius:12,background:"linear-gradient(135deg,#17344a,#0f5a4b)"}}/>
                  <div style={{height:110,borderRadius:12,background:"linear-gradient(135deg,#17344a,#263d62)"}}/>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section" id="offres">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">Offres claires</span>
            <h2>Trois niveaux de service, sans catalogue caché.</h2>
            <p>
              Les offres ci-dessous correspondent aux forfaits Pulse‑PME actuellement proposés.
              Les fonctionnalités précises sont confirmées avant souscription.
            </p>
          </div>

          <div className="pricing">
            {plans.map((plan) => (
              <div className={`card price-card ${plan.popular ? "popular" : ""}`} key={plan.name}>
                {plan.popular && <span className="badge">Le plus adapté à la plupart des PME</span>}
                <h3>{plan.name}</h3>
                <p>{plan.subtitle}</p>
                <div className="price">{plan.price}€ <small>/ mois</small></div>
                <ul className="feature-list">
                  {plan.features.map((f) => <li key={f}><span className="check">✓</span><span>{f}</span></li>)}
                </ul>
              </div>
            ))}
          </div>
          <p style={{color:"var(--muted)",fontSize:12,marginTop:18}}>
            Abonnements mensuels sans engagement. Le paiement n’est demandé qu’après validation de l’offre choisie.
          </p>
        </div>
      </section>

      <section className="section" id="faq">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">Questions fréquentes</span>
            <h2>Ce que vous pouvez vérifier avant de décider.</h2>
          </div>
          <div className="faq">
            {faq.map((item,i) => (
              <div key={item.q}>
                <button onClick={() => setOpenFaq(openFaq === i ? null : i)}>
                  <span>{item.q}</span><span>{openFaq === i ? "−" : "+"}</span>
                </button>
                {openFaq === i && <div className="faq-answer">{item.a}</div>}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="contact-panel">
            <div>
              <span className="eyebrow">Contact direct</span>
              <h2 style={{fontSize:"clamp(32px,5vw,48px)",marginTop:16}}>Une question sur la démo ou sur HoldMasto ?</h2>
              <p style={{color:"var(--muted)",lineHeight:1.7,marginBottom:0}}>
                Vous pouvez contacter directement la société éditrice avant de souscrire.
              </p>
            </div>
            <div style={{display:"grid",gap:10,minWidth:260}}>
              <a className="btn btn-primary" href="mailto:rigahludovic@gmail.com?subject=Pulse-PME%20-%20Contact">rigahludovic@gmail.com</a>
              <a className="btn btn-secondary" href="tel:+33782491516">07 82 49 15 16</a>
            </div>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="wrap footer-grid">
          <div>
            <strong>Pulse‑PME</strong>
            <p style={{lineHeight:1.6}}>Solution numérique éditée et opérée par HoldMasto.</p>
          </div>
          <div>
            <strong>HoldMasto</strong>
            <p style={{lineHeight:1.6}}>
              SASU · RCS Fort‑de‑France 106 121 536<br/>
              2 Impasse Bacouna<br/>
              97231 Le Robert, France
            </p>
          </div>
          <div>
            <strong>Informations</strong>
            <p style={{lineHeight:1.6}}>
              Président : Ludovic Rigah<br/>
              Capital social : 10 €<br/>
              © 2026 HoldMasto
            </p>
          </div>
        </div>
      </footer>
    </main>
  )
}
