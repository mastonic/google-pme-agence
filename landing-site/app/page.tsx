import { Faq } from './components/Faq'
import { GoogleCard } from './components/GoogleCard'
import { Logo } from './components/Logo'
import { Reveal } from './components/Reveal'
import './landing.css'

import { CONTACT_EMAIL, mail } from './components/contact'

const PLANS = [
  {
    name: 'Starter',
    desc: 'Une présence web propre et rassurante.',
    price: '49€',
    features: [
      'Site vitrine pro jusqu’à 5 pages',
      'Hébergement, SSL et maintenance',
      'Téléphone, WhatsApp, formulaire, infos pratiques',
      'Supervision du site',
      '1 petite modification par mois',
    ],
  },
  {
    name: 'Pro',
    desc: 'Pour être mieux trouvé et recevoir plus de contacts locaux.',
    price: '149€',
    featured: true,
    features: [
      'Tout Starter',
      'Nom de domaine personnalisé',
      'SEO local et pages prioritaires',
      'Optimisation fiche Google Business',
      'Suivi des appels, WhatsApp et demandes',
    ],
  },
  {
    name: 'Élite',
    desc: 'Pour automatiser votre acquisition et votre suivi.',
    price: '299€',
    features: [
      'Tout Pro',
      'SEO avancé et contenus réguliers',
      'Chatbot IA / assistant WhatsApp',
      'Automatisation des demandes d’avis',
      'Optimisations mensuelles de conversion',
    ],
  },
]

const BENEFITS = [
  ['01', 'Une image pro, tout de suite', 'Un site vitrine clair et rassurant, pensé pour le mobile, qui donne envie de vous appeler.'],
  ['02', 'Plus de clients près de chez vous', 'SEO local et fiche Google Business optimisée pour apparaître quand on cherche votre métier dans votre ville.'],
  ['03', 'Zéro technique à gérer', 'Hébergement, sécurité, maintenance et modifications : tout est inclus dans votre abonnement mensuel.'],
]

const STEPS = [
  ['Analyse', 'Nous analysons vos informations professionnelles publiques et les points de friction visibles.'],
  ['Démo', 'Une démonstration personnalisée vous montre le résultat attendu pour votre activité.'],
  ['Validation', 'Vous vérifiez infos, design et services souhaités avant toute mise en ligne.'],
  ['On s’occupe du reste', 'Après souscription, Pulse‑Pro prend en charge les services inclus dans votre formule.'],
]

const RECEPTION_STEPS = [
  ['Renvoi d’appel', 'Vous activez le renvoi de votre ligne vers votre réceptionniste quand vous ne décrochez pas. Votre numéro ne change pas.'],
  ['L’IA répond', 'Elle accueille l’appelant au nom de votre entreprise, note sa demande, ses coordonnées et repère si c’est urgent.'],
  ['Vous recevez un SMS', 'Un résumé clair arrive sur votre téléphone : qui a appelé, pour quoi, et à quel point c’est pressé. Vous rappelez quand vous êtes libre.'],
]

const PROFESSIONS = ['Électricien', 'Plombier', 'Chauffagiste', 'Coiffeur', 'Esthéticienne', 'Taxi / VTC', 'Restaurant', 'Garage', 'Serrurier', 'Kiné', 'Agence immobilière', 'Et votre métier…']

export default function Home() {
  return (
    <div id="top" className="landing">
      <Reveal />

      <header className="site-header">
        <div className="wrap">
          <a href="#top" className="brand" aria-label="Pulse‑Pro, retour en haut">
            <Logo />
          </a>
          <nav className="main-nav" aria-label="Navigation principale">
            <a href="#fonctionnement">Comment ça marche</a>
            <a href="#receptionniste">Réceptionniste IA</a>
            <a href="#offres">Offres</a>
            <a href="#societe">Qui sommes-nous</a>
            <a href="#faq">FAQ</a>
          </nav>
          <a href={mail('Pulse-Pro - Demande de démo')} className="btn btn-dark btn-header">
            Demander ma démo
          </a>
        </div>
      </header>

      <main>
        <section className="wrap hero">
          <div className="hero-copy">
            <span className="pill" data-reveal="0">
              <span className="dot pulse" />
              Pour les TPE et PME locales
            </span>
            <h1 data-reveal="80">Plus de clients locaux. Sans vous occuper du web.</h1>
            <p className="hero-lead" data-reveal="160">
              Site professionnel, fiche Google, appels et WhatsApp : Pulse‑Pro gère votre visibilité locale. Vous voyez
              une démo de votre futur site avant de payer quoi que ce soit.
            </p>
            <div className="hero-ctas" data-reveal="240">
              <a href={mail('Pulse-Pro - Je veux ma démo')} className="btn btn-primary">
                Recevoir ma démo gratuite →
              </a>
              <a href="#offres" className="btn btn-ghost">
                Voir les tarifs
              </a>
            </div>
            <div className="hero-checks" data-reveal="320">
              <span>✓ Sans engagement</span>
              <span>✓ Dès 49 € / mois</span>
              <span>✓ Société française</span>
            </div>
          </div>

          <div className="hero-visual">
            <div data-reveal="200" data-reveal-scale="">
              <GoogleCard />
            </div>
            <div className="notif float" aria-hidden="true">
              <span className="notif-icon">☎</span>
              <div className="stack" style={{ gap: 2 }}>
                <span className="notif-title">Nouvelle demande de contact</span>
                <span className="notif-sub">via votre fiche Google</span>
              </div>
            </div>
          </div>
        </section>

        <section className="band-white">
          <div className="wrap benefits">
            <div className="section-head" style={{ maxWidth: 720 }} data-reveal="0">
              <span className="eyebrow">Ce que vous y gagnez</span>
              <h2 className="h2">Vous gérez votre activité. On s’occupe que l’on vous trouve.</h2>
            </div>
            <div className="grid-280">
              {BENEFITS.map(([num, title, text]) => (
                <div className="benefit" data-reveal="stagger" key={num}>
                  <span className="benefit-num">{num}</span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="fonctionnement" className="wrap how">
          <div className="how-head" data-reveal="0">
            <div className="section-head" style={{ maxWidth: 640 }}>
              <span className="eyebrow">Comment ça marche</span>
              <h2 className="h2">Vous voyez le résultat avant de vous engager.</h2>
            </div>
            <p>On prépare une proposition concrète, vous jugez sur pièce, puis vous activez uniquement ce que vous choisissez.</p>
          </div>
          <ol className="steps" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {STEPS.map(([title, text], i) => (
              <li className={i === STEPS.length - 1 ? 'step last' : 'step'} data-reveal="stagger" key={title}>
                <span className="step-num">{i + 1}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </li>
            ))}
          </ol>
          <div className="demo-box" data-reveal="0">
            <div className="stack" style={{ gap: 8, maxWidth: 720 }}>
              <h3>Vous avez reçu une démo ?</h3>
              <p>
                Elle a été préparée pour que vous puissiez juger sur pièce. Rien n’est publié sur votre domaine et aucun
                abonnement n’est activé sans votre accord. Pour avancer, il suffit de valider vos informations, logo,
                photos et services.
              </p>
            </div>
            <a href={mail('Pulse-Pro - Suite à ma démo')} className="btn btn-advance">
              Je veux avancer
            </a>
          </div>
        </section>

        <section id="receptionniste" className="reception-band">
          <div className="wrap reception">
            <div className="reception-head" data-reveal="0">
              <span className="reception-pill">Nouveau · offerte 30 jours</span>
              <h2 className="h2">Réceptionniste IA : plus aucun appel perdu pendant que vous travaillez.</h2>
              <p className="reception-lead">
                Vous êtes sur un chantier, en rendez-vous, au volant ou en plein service : le téléphone sonne, vous ne
                pouvez pas décrocher. Le client n’attend pas, il appelle le suivant sur Google. Votre réceptionniste IA
                répond à votre place, 24h/24.
              </p>
            </div>

            <div className="reception-example" data-reveal="0">
              <span className="reception-example-tag">Exemple</span>
              <p>
                Un électricien est sur un tableau électrique, les mains occupées. Un particulier appelle pour une panne
                de courant. Sans réponse, il appelle un concurrent. Avec la réceptionniste IA, l’appel est pris, la
                panne est notée comme urgente et l’électricien reçoit un SMS : il rappelle dix minutes plus tard et
                garde le client.
              </p>
            </div>

            <ol className="reception-steps">
              {RECEPTION_STEPS.map(([title, text], i) => (
                <li className="reception-step" data-reveal="stagger" key={title}>
                  <span className="reception-step-num">{i + 1}</span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </li>
              ))}
            </ol>

            <div className="reception-pros" data-reveal="0">
              <span className="reception-pros-title">Fonctionne pour tous les métiers qui reçoivent des appels :</span>
              <div className="chips">
                {PROFESSIONS.map((p) => (
                  <span className="chip" key={p}>{p}</span>
                ))}
              </div>
            </div>

            <div className="reception-cta" data-reveal="0">
              <div className="stack" style={{ gap: 6 }}>
                <strong>30 jours offerts pour l’essayer en conditions réelles.</strong>
                <span>Sans engagement, résiliable à tout moment. Vous ne continuez que si elle vous est utile.</span>
              </div>
              <a href={mail('Pulse-Pro - Activer ma Réceptionniste IA (30 jours offerts)')} className="btn btn-primary">
                Activer mes 30 jours gratuits →
              </a>
            </div>
          </div>
        </section>

        <section id="offres" className="pricing-band">
          <div className="wrap pricing">
            <div className="section-head" style={{ maxWidth: 700 }} data-reveal="0">
              <span className="eyebrow">Tarifs</span>
              <h2 className="h2">Trois formules claires. Sans engagement.</h2>
              <p className="pricing-intro">
                Le paiement n’est demandé qu’après validation de l’offre choisie. Fonctionnalités confirmées avant
                souscription.
              </p>
            </div>
            <div className="plans">
              {PLANS.map((plan) => (
                <div className={plan.featured ? 'plan featured' : 'plan'} data-reveal="stagger" key={plan.name}>
                  {plan.featured && <span className="plan-badge">Le plus choisi</span>}
                  <div className="stack" style={{ gap: 8 }}>
                    <h3>{plan.name}</h3>
                    <p className="plan-desc">{plan.desc}</p>
                  </div>
                  <div className="plan-price">
                    <strong>{plan.price}</strong>
                    <span>/ mois</span>
                  </div>
                  <span className="plan-reception">☎ Réceptionniste IA offerte 30 jours, en option ensuite</span>
                  <div className="plan-features">
                    {plan.features.map((f) => (
                      <span key={f}>✓ {f}</span>
                    ))}
                  </div>
                  <a href={mail(`Pulse-Pro - Formule ${plan.name}`)} className="plan-cta">
                    Choisir {plan.name}
                  </a>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="societe" className="wrap about">
          <div className="about-inner" data-reveal="0">
            <span className="eyebrow">Qui sommes-nous</span>
            <h2 className="h2">Une vraie société, joignable et vérifiable.</h2>
            <p>
              Pulse‑Pro est une solution éditée et opérée par HoldMasto, société française spécialisée dans le
              développement de sites, logiciels et plateformes pour professionnels. Vous savez à qui vous confiez votre
              image, votre site et vos données.
            </p>
            <a href={mail('Vérification Pulse-Pro')} className="link-underline">
              Poser une question à HoldMasto →
            </a>
            <a href="/mentions-legales/" className="link-legal">
              Mentions légales, CGV, CGU et confidentialité
            </a>
          </div>
        </section>

        <section id="faq" className="faq-band">
          <div className="faq">
            <div className="section-head" data-reveal="0">
              <span className="eyebrow">Questions fréquentes</span>
              <h2 className="h2">Tout ce que vous voulez savoir avant de décider.</h2>
            </div>
            <Faq />
          </div>
        </section>

        <section className="final-band">
          <div className="final" data-reveal="0" data-reveal-scale="">
            <h2>Voyez votre futur site avant de payer.</h2>
            <p>Écrivez-nous avec le nom de votre entreprise. On vous prépare une démo personnalisée, gratuitement.</p>
            <a href={mail('Pulse-Pro - Je veux ma démo')} className="btn btn-final">
              Recevoir ma démo gratuite →
            </a>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="wrap footer-grid">
          <div className="stack" style={{ gap: 6 }}>
            <strong className="footer-brand">Pulse‑Pro</strong>
            <span>Solution numérique éditée et opérée par HoldMasto.</span>
          </div>
          <div className="stack">
            <strong>HoldMasto</strong>
            <span>SASU · RCS Fort‑de‑France 106 121 536</span>
            <span>2 Impasse Bacouna, 97231 Le Robert, France</span>
          </div>
          <div className="stack">
            <strong>Contact</strong>
            <a href={mail('Pulse-Pro - Contact')}>{CONTACT_EMAIL}</a>
            <span>© 2026 HoldMasto</span>
          </div>
          <nav className="stack" aria-label="Informations légales">
            <strong>Informations légales</strong>
            <a href="/mentions-legales/#mentions">Mentions légales</a>
            <a href="/mentions-legales/#cgv">CGV</a>
            <a href="/mentions-legales/#cgu">CGU</a>
            <a href="/mentions-legales/#rgpd">Confidentialité (RGPD)</a>
          </nav>
        </div>
      </footer>
    </div>
  )
}
