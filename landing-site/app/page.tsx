import { Faq } from './components/Faq'
import { OrderButton } from './components/OrderButton'
import { GoogleCard } from './components/GoogleCard'
import { Logo } from './components/Logo'
import { Reveal } from './components/Reveal'
import { SceneAnalyse, SceneCalm, SceneDemo, SceneMaps, SceneRun, SceneSite, SceneValidate, Showreel } from './components/Showreel'
import './landing.css'
import { JsonLd } from './components/JsonLd'
import { FAQS } from './seo/faq-data'
import { ORG_ID, abs, faqPage } from './seo/seo'

import { CONTACT_EMAIL } from './components/contact'
import { siteHref } from './seo/domains'

const PLANS = [
  {
    name: 'Starter',
    desc: 'Une présence web propre et rassurante.',
    price: '49 €',
    annual: '490 €',
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
    price: '149 €',
    annual: '1 490 €',
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
    price: '299 €',
    annual: '2 990 €',
    reception: true,
    features: [
      'Tout Pro',
      'Réceptionniste IA incluse (100 appels/mois)',
      'Pack Connecté : Google Agenda, Sheets, Zapier',
      'Garanti chaque mois : 4 contenus SEO + 4 posts Google',
      'Chatbot IA / assistant WhatsApp',
      'Automatisation des demandes d’avis',
      'Jusqu’à 10 modifications par mois',
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
  ['On s’occupe du reste', 'Après souscription, Pulse Locale PME prend en charge les services inclus dans votre formule.'],
]

const RECEPTION_STEPS = [
  ['Renvoi d’appel', 'Vous activez le renvoi de votre ligne vers votre réceptionniste quand vous ne décrochez pas. Votre numéro ne change pas.'],
  ['L’IA répond', 'Elle accueille l’appelant au nom de votre entreprise, note sa demande, ses coordonnées et repère si c’est urgent.'],
  ['Vous recevez un résumé', 'Un résumé clair arrive par WhatsApp ou SMS : qui a appelé, pour quoi, et à quel point c’est pressé. Vous rappelez quand vous êtes libre.'],
]

const PROFESSIONS = ['Électricien', 'Plombier', 'Chauffagiste', 'Coiffeur', 'Esthéticienne', 'Taxi / VTC', 'Restaurant', 'Garage', 'Serrurier', 'Kiné', 'Agence immobilière', 'Et votre métier…']

export default function Home() {
  return (
    <div id="top" className="landing">
      <Reveal />
      <JsonLd
        items={[
          { '@type': 'WebSite', '@id': abs('/#site'), url: abs('/'), name: 'Pulse Locale PME', inLanguage: 'fr-FR', publisher: { '@id': ORG_ID } },
          {
            '@type': 'Service',
            '@id': abs('/#service'),
            name: 'Pulse Locale PME : site internet, fiche Google et réceptionniste IA pour TPE et artisans',
            serviceType: 'Création de site internet et référencement local',
            description: 'Site vitrine professionnel, optimisation de la fiche Google Business, SEO local, suivi des appels et WhatsApp, réceptionniste IA. Démo gratuite avant paiement.',
            provider: { '@id': ORG_ID },
            areaServed: [
              { '@type': 'AdministrativeArea', name: 'Yvelines (78)', url: abs('/agence-seo-local-yvelines/') },
              { '@type': 'AdministrativeArea', name: 'Eure-et-Loir (28)', url: abs('/agence-seo-local-eure-et-loir/') },
              { '@type': 'Country', name: 'France' },
            ],
            audience: { '@type': 'BusinessAudience', audienceType: 'TPE, PME, artisans et commerçants' },
            hasOfferCatalog: {
              '@type': 'OfferCatalog',
              name: 'Formules Pulse Locale PME',
              itemListElement: PLANS.map((p) => ({
                '@type': 'Offer',
                name: `Formule ${p.name}`,
                description: p.desc,
                price: p.price.replace(/[^0-9]/g, ''),
                priceCurrency: 'EUR',
                priceSpecification: { '@type': 'UnitPriceSpecification', price: p.price.replace(/[^0-9]/g, ''), priceCurrency: 'EUR', valueAddedTaxIncluded: false, unitCode: 'MON', referenceQuantity: { '@type': 'QuantitativeValue', value: 1, unitCode: 'MON' } },
                url: abs('/#offres'),
              })),
            },
          },
          faqPage(FAQS),
        ]}
      />

      <header className="site-header">
        <div className="wrap">
          <a href="#top" className="brand" aria-label="Pulse Locale PME, retour en haut">
            <Logo />
          </a>
          <nav className="main-nav" aria-label="Navigation principale">
            <a href="#fonctionnement">Comment ça marche</a>
            <a href="#receptionniste">Réceptionniste IA</a>
            <a href="#offres">Offres</a>
            <a href="#societe">Qui sommes-nous</a>
            <a href="#faq">FAQ</a>
            <a href={siteHref('/store/')}>Boutique</a>
            <a href={siteHref('/info/')}>Ressources</a>
          </nav>
          <OrderButton product="Démo gratuite du site" source="callback" title="Recevoir ma démo gratuite" className="btn btn-dark btn-header">
            Demander ma démo
          </OrderButton>
        </div>
      </header>

      <main>
        <section className="wrap hero">
          <div className="hero-copy">
            <span className="pill" data-reveal="0">
              <span className="dot pulse" />
              Yvelines (78) · Eure-et-Loir (28)
            </span>
            <h1>Plus de clients locaux dans les Yvelines et l’Eure-et-Loir</h1>
            <p className="hero-lead">
              Pulse Locale PME accompagne les artisans, commerçants et petites entreprises des Yvelines et de l’Eure-et-Loir
              dans leur visibilité sur Google, leur site internet et l’automatisation de leurs demandes clients. Vous voyez
              une démo de votre futur site avant de payer quoi que ce soit.
            </p>
            <div className="hero-ctas" data-reveal="240">
              <OrderButton product="Démo gratuite du site" source="callback" title="Recevoir ma démo gratuite" className="btn btn-primary">
                Recevoir ma démo gratuite →
              </OrderButton>
              <OrderButton product="Devis et tarifs" source="callback" title="Recevoir nos tarifs"
                intro="Laissez votre numéro : on vous présente les formules adaptées à votre activité, sans engagement."
                className="btn btn-ghost">
                Recevoir nos tarifs
              </OrderButton>
            </div>
            <div className="hero-checks" data-reveal="320">
              <span>✓ Sans engagement</span>
              <span>✓ Dès 49 € HT / mois</span>
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
            <div data-reveal="0">
              <Showreel
                id="gains"
                chapters={[
                  { label: 'Image pro', title: BENEFITS[0][1], text: BENEFITS[0][2], scene: <SceneSite /> },
                  { label: 'Visibilité locale', title: BENEFITS[1][1], text: BENEFITS[1][2], scene: <SceneMaps /> },
                  { label: 'Sérénité', title: BENEFITS[2][1], text: BENEFITS[2][2], scene: <SceneCalm /> },
                ]}
              />
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
          <div data-reveal="0">
            <Showreel
              id="etapes"
              chapters={[
                { label: 'Étape 1 · Analyse', title: STEPS[0][0], text: STEPS[0][1], scene: <SceneAnalyse /> },
                { label: 'Étape 2 · Démo', title: STEPS[1][0], text: STEPS[1][1], scene: <SceneDemo /> },
                { label: 'Étape 3 · Validation', title: STEPS[2][0], text: STEPS[2][1], scene: <SceneValidate /> },
                { label: 'Étape 4 · En ligne', title: STEPS[3][0], text: STEPS[3][1], scene: <SceneRun /> },
              ]}
            />
          </div>
          <div className="demo-box" data-reveal="0">
            <div className="stack" style={{ gap: 8, maxWidth: 720 }}>
              <h3>Vous avez reçu une démo ?</h3>
              <p>
                Elle a été préparée pour que vous puissiez juger sur pièce. Rien n’est publié sur votre domaine et aucun
                abonnement n’est activé sans votre accord. Pour avancer, il suffit de valider vos informations, logo,
                photos et services.
              </p>
            </div>
            <OrderButton product="Suite à ma démo" source="callback" title="On en parle ?" className="btn btn-advance">
              Je veux avancer
            </OrderButton>
          </div>
        </section>

        <section id="receptionniste" className="reception-band">
          <div className="wrap reception">
            <div className="reception-head" data-reveal="0">
              <span className="reception-pill">Nouveau · offerte 30 jours (jusqu’à 60 appels)</span>
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
                <strong>30 jours offerts pour l’essayer en conditions réelles, jusqu’à 60 appels.</strong>
                <span>
                  Ensuite 39 € HT / mois avec 100 appels inclus, puis 0,83 € HT l’appel (1 € TTC), sans engagement.
                  Incluse dans la formule Élite. En option, le Pack Connecté (19 € HT / mois) : elle réserve vos
                  rendez-vous dans Google Agenda et remplit votre tableur Google Sheets.
                </span>
              </div>
              <OrderButton product="Réceptionniste IA (30 jours offerts, 60 appels)" source="callback" title="Activer ma Réceptionniste IA" className="btn btn-primary">
                Activer mes 30 jours gratuits →
              </OrderButton>
            </div>
          </div>
        </section>

        <section id="offres" className="pricing-band">
          <div className="wrap pricing">
            <div className="section-head" style={{ maxWidth: 700 }} data-reveal="0">
              <span className="eyebrow">Tarifs</span>
              <h2 className="h2">Trois formules claires. Sans engagement, sans frais de création.</h2>
              <p className="pricing-intro">
                Prix HT. Mensuel sans engagement, ou annuel avec 2 mois offerts. Le paiement n’est demandé qu’après
                validation de votre démo.
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
                    <span>HT / mois</span>
                  </div>
                  <span className="plan-annual">ou {plan.annual} HT / an : 2 mois offerts</span>
                  <span className="plan-reception">
                    {plan.reception ? '☎ Réceptionniste IA incluse' : '☎ Réceptionniste IA : 30 jours ou 60 appels offerts, puis 39 € HT / mois en option'}
                  </span>
                  <div className="plan-features">
                    {plan.features.map((f) => (
                      <span key={f}>✓ {f}</span>
                    ))}
                  </div>
                  <OrderButton product={`Formule ${plan.name} (${plan.price} HT / mois ou ${plan.annual} HT / an)`} source="callback" title={`Formule ${plan.name}`} className="plan-cta" style={{ width: '100%' }}>
                    Choisir {plan.name}
                  </OrderButton>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="comparatif" className="wrap compare">
          <div className="section-head" style={{ maxWidth: 760 }} data-reveal="0">
            <span className="eyebrow">Comparatif</span>
            <h2 className="h2">Ce que vous payez vraiment la première année.</h2>
            <p className="pricing-intro">
              Pour un site professionnel avec fiche Google et gestion des avis, les frais de création et l’engagement
              changent tout.
            </p>
          </div>
          <div className="compare-scroll" data-reveal="0">
            <table className="compare-table">
              <thead>
                <tr>
                  <th scope="col"></th>
                  <th scope="col" className="us">Pulse Locale PME · Pro</th>
                  <th scope="col">Simplébo · Pack Croissance</th>
                  <th scope="col">Agence SEO locale</th>
                </tr>
              </thead>
              <tbody>
                <tr><th scope="row">Abonnement</th><td className="us">149 € HT / mois</td><td>120 € HT / mois</td><td>300 à 1 500 € HT / mois</td></tr>
                <tr><th scope="row">Frais de création</th><td className="us">0 €</td><td>500 € HT</td><td>500 à 800 € HT</td></tr>
                <tr><th scope="row">Engagement</th><td className="us">Aucun (mensuel)</td><td>12 mois (paiement mensuel)</td><td>Souvent 6 à 12 mois</td></tr>
                <tr><th scope="row">Réceptionniste IA</th><td className="us">30 jours offerts (60 appels), puis 39 € HT / mois</td><td>—</td><td>—</td></tr>
                <tr className="total"><th scope="row">Première année</th><td className="us">1 788 € HT, ou 1 490 € HT en annuel</td><td>1 940 € HT</td><td>4 100 à 18 800 € HT</td></tr>
              </tbody>
            </table>
          </div>
          <p className="compare-note">
            Tarifs publics constatés le 8 novembre 2026 : Simplébo, page tarifs officielle (Pack Croissance, paiement
            mensuel, entreprise de plus de 2 ans) ; agences SEO locales, fourchettes publiées par des agences françaises
            pour un artisan ou une TPE. Les contenus des offres ne sont pas strictement identiques (le Pack Croissance
            inclut par exemple un blog IA hebdomadaire). « — » : non proposé dans l’offre publique comparée.
          </p>
        </section>

        <section id="zones" className="wrap zones" aria-labelledby="zones-title">
          <div className="section-head" style={{ maxWidth: 720 }} data-reveal="0">
            <span className="eyebrow">Zones desservies</span>
            <h2 id="zones-title" className="h2">Yvelines et Eure-et-Loir&nbsp;: une page par secteur.</h2>
            <p className="zones-lead">
              Vos clients cherchent par commune. Nos pages locales détaillent les communes desservies, les recherches
              typiques et nos tarifs, identiques partout. L’accompagnement se fait à distance, partout en France.
            </p>
          </div>
          <div className="grid-280">
            <a href={siteHref('/agence-seo-local-yvelines/')} className="zone-card" data-reveal="stagger">
              <span className="zone-tag">Yvelines · 78</span>
              <h3>SEO local dans les Yvelines</h3>
              <p>Versailles, Saint-Quentin-en-Yvelines, Trappes, Poissy, Mantes-la-Jolie, Rambouillet, Saint-Germain-en-Laye.</p>
              <span className="link-underline">Voir la page Yvelines →</span>
            </a>
            <a href={siteHref('/agence-seo-local-eure-et-loir/')} className="zone-card" data-reveal="stagger">
              <span className="zone-tag">Eure-et-Loir · 28</span>
              <h3>SEO local en Eure-et-Loir</h3>
              <p>Chartres, Lucé, Mainvilliers, Dreux, Châteaudun, Nogent-le-Rotrou.</p>
              <span className="link-underline">Voir la page Eure-et-Loir →</span>
            </a>
            <a href={siteHref('/methode/')} className="zone-card" data-reveal="stagger">
              <span className="zone-tag">Méthode</span>
              <h3>Comment nous travaillons</h3>
              <p>Audit, fiche Google, site, contenus, suivi des appels et de la visibilité IA : notre méthode, sans promesse de position.</p>
              <span className="link-underline">Voir la méthode →</span>
            </a>
          </div>
        </section>

        <section id="societe" className="wrap about">
          <div className="about-inner" data-reveal="0">
            <span className="eyebrow">Qui sommes-nous</span>
            <h2 className="h2">Une vraie société, joignable et vérifiable.</h2>
            <p>
              Pulse Locale PME (pulse-locale-pme.fr) est éditée et opérée par sa maison mère HoldMasto, société française spécialisée dans le
              développement de sites, logiciels et plateformes pour professionnels. Vous savez à qui vous confiez votre
              image, votre site et vos données.
            </p>
            <OrderButton product="Question à HoldMasto" source="contact" title="Poser une question à HoldMasto" phoneRequired={false}
              intro="Une question sur la société, nos offres ou vos données ? Écrivez-nous, on vous répond sous 24 h ouvrées." submitLabel="Envoyer ma question →"
              className="link-underline" style={{ background: 'none', padding: 0, color: 'inherit', textAlign: 'left' }}>
              Poser une question à HoldMasto →
            </OrderButton>
            <a href={siteHref('/a-propos/')} className="link-underline">Qui sommes-nous : HoldMasto et Pulse Locale PME →</a>
            <a href={siteHref('/mentions-legales/')} className="link-legal">
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
            <p>Laissez-nous votre numéro et le nom de votre entreprise. On vous prépare une démo personnalisée, gratuitement.</p>
            <OrderButton product="Démo gratuite du site" source="callback" title="Recevoir ma démo gratuite" className="btn btn-final">
              Recevoir ma démo gratuite →
            </OrderButton>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="wrap footer-grid">
          <div className="stack" style={{ gap: 6 }}>
            <strong className="footer-brand">Pulse Locale PME</strong>
            <span>pulse-locale-pme.fr · édité et opéré par HoldMasto, maison mère.</span>
          </div>
          <div className="stack">
            <strong>HoldMasto</strong>
            <span>SASU · RCS Fort‑de‑France 106 121 536</span>
            <span>2 Impasse Bacouna, 97231 Le Robert, France</span>
          </div>
          <div className="stack">
            <strong>Contact</strong>
            <OrderButton product="Contact Pulse Locale PME" source="contact" title="Nous contacter" phoneRequired={false}
              intro="Une question, un projet ? Laissez-nous un message, on vous répond sous 24 h ouvrées." submitLabel="Envoyer →"
              style={{ background: 'none', padding: 0, color: 'inherit', textAlign: 'left', textDecoration: 'underline' }}>
              Nous écrire
            </OrderButton>
            <span>{CONTACT_EMAIL}</span>
            <span>© 2026 HoldMasto</span>
          </div>
          <nav className="stack" aria-label="Ressources">
            <strong>Ressources</strong>
            <a href={siteHref('/store/')}>Boutique : packs à prix fixe</a>
            <a href={siteHref('/info/outil-gratuit/')}>Test de visibilité gratuit</a>
            <a href={siteHref('/info/guide-gratuit/')}>Guide : les 10 erreurs Google</a>
            <a href={siteHref('/info/guides/')}>Guides par métier</a>
            <a href={siteHref('/zones/')}>Zones desservies</a>
            <a href={siteHref('/agence-seo-local-yvelines/')}>Yvelines (78)</a>
            <a href={siteHref('/agence-seo-local-eure-et-loir/')}>Eure-et-Loir (28)</a>
            <a href={siteHref('/info/auteur/ludovic-rigah/')}>Ludovic Rigah, fondateur</a>
          </nav>
          <nav className="stack" aria-label="Informations légales">
            <strong>Informations légales</strong>
            <a href={siteHref('/mentions-legales/#mentions')}>Mentions légales</a>
            <a href={siteHref('/mentions-legales/#cgv')}>CGV</a>
            <a href={siteHref('/mentions-legales/#cgu')}>CGU</a>
            <a href={siteHref('/mentions-legales/#rgpd')}>Confidentialité (RGPD)</a>
          </nav>
        </div>
      </footer>
    </div>
  )
}
