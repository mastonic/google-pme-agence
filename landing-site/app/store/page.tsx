import type { Metadata } from 'next'
import { abs, breadcrumbs, faqPage, ORG_ID, pageMeta } from '../seo/seo'
import { JsonLd } from '../components/JsonLd'
import { PageHero, SubShell } from '../components/SubShell'
import { OrderButton } from '../components/OrderButton'
import { siteHref } from '../seo/domains'

export const metadata: Metadata = pageMeta({
  title: 'Boutique : fiche Google, pack avis et audit IA à prix fixe',
  description: 'Packs à prix fixe pour artisans et commerces : fiche Google optimisée 149 € HT, pack 50 avis 99 € HT, audit visibilité IA 99 € HT, plaques NFC avis.',
  path: '/store/',
})

const PACKS = [
  {
    slug: 'fiche-google-optimisee',
    tag: 'Le plus vendu',
    gold: true,
    name: 'Fiche Google optimisée',
    pitch: 'Votre fiche Google refaite de A à Z pour sortir dans le « pack local » de Maps. Déduit de votre 1er mois si vous passez en formule Pro.',
    price: '149 €',
    unit: 'HT, une fois',
    delay: 'Livré en 5 jours ouvrés',
    items: ['Catégories et services optimisés', 'Description rédigée pour votre ville', '10 photos retouchées', '4 posts Google prêts'],
  },
  {
    slug: 'pack-avis-50',
    tag: 'Réputation',
    name: 'Pack 50 avis',
    pitch: 'Une campagne SMS + QR code pour demander un avis Google à chacun de vos clients, sans filtrer ni récompenser.',
    price: '99 €',
    unit: 'HT, une fois',
    delay: 'Démarre sous 48 h',
    items: ['Message SMS rédigé et envoyé', 'Lien d’avis direct', 'Relance automatique J+3', 'Suivi des avis reçus'],
  },
  {
    slug: 'audit-visibilite-ia',
    tag: 'Nouveau',
    name: 'Audit visibilité IA',
    pitch: 'Savez-vous si ChatGPT, Gemini et Google recommandent votre commerce ? On vérifie pour vous, puis on vous explique tout au téléphone.',
    price: '99 €',
    unit: 'HT, une fois',
    delay: 'Rapport PDF sous 72 h',
    items: ['Appel de 20 min avec un expert pour tout vous expliquer', 'Test sur 3 IA et Google Maps', 'Comparaison avec 3 concurrents', 'Plan d’action priorisé'],
  },
]

const KITS = [
  ['Plaque NFC « Laissez-nous un avis »', 'Le client approche son téléphone, la page d’avis s’ouvre. Format comptoir, plexiglas.', '39 € HT'],
  ['Kit 20 stickers QR vitrine & tables', 'Pour vitrine, tables, caisse ou camion. Résistants à l’eau et aux UV.', '29 € HT'],
  ['Chevalet de comptoir personnalisé', 'Votre logo, votre QR code, votre note Google. Livré prêt à poser.', '24 € HT'],
]

const SUBS = [
  ['Starter', '49 €', '490 €', 'Site vitrine pro, hébergement et maintenance compris.'],
  ['Pro', '149 €', '1 490 €', 'Site + SEO local + fiche Google suivie chaque mois.'],
  ['Élite', '299 €', '2 990 €', 'Tout Pro + réceptionniste IA et Pack Connecté inclus + 4 contenus SEO et 4 posts Google garantis par mois.'],
]

const FAQ = [
  ['Je dois m’engager ?', 'Non. Les packs sont payés une fois. Les abonnements sont sans frais de création et se résilient en un clic, à tout moment. En payant à l’année, vous avez 2 mois offerts.'],
  ['Le pack Fiche Google est-il perdu si je prends un abonnement ensuite ?', 'Non : si vous passez en formule Pro dans les 30 jours, les 149 € HT du pack sont déduits de votre premier mois.'],
  ['Il faut que je fasse quelque chose ?', 'Juste répondre à un formulaire de 5 minutes après l’achat (accès à votre fiche, photos, horaires). On s’occupe du reste.'],
  ['Et si je n’ai pas encore de fiche Google ?', 'On la crée et on gère la validation avec vous. C’est inclus dans le pack Fiche Google optimisée.'],
  ['Je peux avoir une facture ?', 'Oui, une facture au nom de votre entreprise est envoyée automatiquement après le paiement.'],
]

export default function Store() {
  return (
    <SubShell variant="store">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Boutique', '/store/']]),
          {
            '@type': 'OfferCatalog',
            name: 'Boutique Pulse Locale PME',
            url: abs('/store/'),
            itemListElement: [
              ...PACKS.map((p) => ({ '@type': 'Offer', name: p.name, description: p.pitch, price: p.price.replace(/[^0-9]/g, ''), priceCurrency: 'EUR', url: p.slug === 'fiche-google-optimisee' ? abs(`/store/${p.slug}/`) : abs(`/store/#packs`), seller: { '@id': ORG_ID } })),
              ...KITS.map(([n, d, p]) => ({ '@type': 'Offer', name: n, description: d, price: p.replace(/[^0-9]/g, ''), priceCurrency: 'EUR', priceSpecification: { '@type': 'PriceSpecification', price: p.replace(/[^0-9]/g, ''), priceCurrency: 'EUR', valueAddedTaxIncluded: false }, seller: { '@id': ORG_ID } })),
            ],
          },
          faqPage(FAQ as [string, string][]),
        ]}
      />
      <PageHero
        eyebrow="Prix fixes · Livraison rapide · Sans engagement"
        title="Plus d’appels depuis Google. En un clic, sans rendez-vous."
        lead="Choisissez le pack dont votre commerce a besoin, payez en ligne, on s’occupe du reste. Pas de devis, pas de commercial, pas de jargon."
      >
        <a href="#packs" className="btn btn-primary">
          Choisir mon pack →
        </a>
        <a href={siteHref('/info/outil-gratuit/')} className="btn btn-ghost">
          Pas sûr ? Faites le test gratuit
        </a>
      </PageHero>

      <section className="wrap" style={{ paddingBottom: 48 }}>
        <div className="trust" data-reveal="0">
          <div><strong>Paiement sécurisé</strong><span>Carte bancaire, facture automatique</span></div>
          <div><strong>Résultat livré</strong><span>Ou on refait le travail, sans frais</span></div>
          <div><strong>Société française</strong><span>HoldMasto, support en français</span></div>
          <div><strong>Zéro technique</strong><span>Un formulaire, c’est tout</span></div>
        </div>
      </section>

      <section id="packs" className="band-white">
        <div className="wrap section">
          <div className="section-head" data-reveal="0">
            <span className="eyebrow">Packs à la carte</span>
            <h2 className="h2">Un problème précis ? Un pack précis.</h2>
            <p className="section-lead">Payé une seule fois. Vous gardez tout ce qu’on produit, même sans abonnement.</p>
          </div>
          <div className="grid-280">
            {PACKS.map((p) => (
              <article key={p.slug} className="card" data-reveal="stagger">
                <span className={`card-tag${p.gold ? ' gold' : ''}`}>{p.tag}</span>
                <h3>{p.name}</h3>
                <p>{p.pitch}</p>
                <ul className="ticks">{p.items.map((i) => <li key={i}>{i}</li>)}</ul>
                <div className="price"><strong>{p.price}</strong><span>{p.unit} · {p.delay}</span></div>
                {p.slug === 'fiche-google-optimisee' ? (
                  <a href={siteHref(`/store/${p.slug}/`)} className="btn btn-primary btn-sm">Voir le pack</a>
                ) : (
                  <OrderButton product={`${p.name} (${p.price})`} title={`Commander : ${p.name}`} className="btn btn-primary btn-sm">Commander</OrderButton>
                )}
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="materiel" className="wrap section">
        <div className="section-head" data-reveal="0">
          <span className="eyebrow">Matériel avis clients</span>
          <h2 className="h2">Le client est content ? Il laisse son avis en 10 secondes.</h2>
          <p className="section-lead">Livré chez vous, déjà relié à votre fiche Google. Vous n’avez qu’à le poser. Prix hors taxes, vente réservée aux professionnels.</p>
        </div>
        <div className="grid-280">
          {KITS.map(([n, d, p]) => (
            <article key={n} className="card" data-reveal="stagger">
              <h3>{n}</h3>
              <p>{d}</p>
              <div className="price"><strong>{p}</strong><span>livraison offerte</span></div>
              <OrderButton product={`${n} (${p})`} title={`Commander : ${n}`} className="btn btn-outline">Commander</OrderButton>
            </article>
          ))}
        </div>
      </section>

      <section id="abonnements" className="pricing-band">
        <div className="wrap pricing">
          <div className="section-head" data-reveal="0">
            <span className="eyebrow">Abonnements</span>
            <h2 className="h2">Vous préférez qu’on s’en occupe tous les mois ?</h2>
            <p className="pricing-intro">Prix HT, sans frais de création. Démo gratuite de votre site avant de payer. Mensuel résiliable à tout moment, ou annuel avec 2 mois offerts.</p>
          </div>
          <div className="plans">
            {SUBS.map(([n, p, y, d], i) => (
              <div key={n} className={`plan${i === 1 ? ' featured' : ''}`} data-reveal="stagger">
                {i === 1 && <span className="plan-badge">Recommandé</span>}
                <h3>{n}</h3>
                <p className="plan-desc">{d}</p>
                <div className="plan-price"><strong>{p}</strong><span>HT / mois</span></div>
                <span className="plan-annual">ou {y} HT / an : 2 mois offerts</span>
                <OrderButton product={`Abonnement ${n} (${p} HT / mois ou ${y} HT / an)`} title={`Abonnement ${n}`} className="plan-cta" style={{ width: '100%' }}>Commencer</OrderButton>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="faq" className="faq-band">
        <div className="faq">
          <div className="section-head"><span className="eyebrow">Avant d’acheter</span><h2 className="h2">Vos questions, nos réponses.</h2></div>
          <div className="faq-list">
            {FAQ.map(([q, a]) => (
              <details key={q} className="faq-item">
                <summary className="faq-q">{q}<span className="faq-icon">+</span></summary>
                <p className="faq-a">{a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section className="final-band">
        <div className="final" data-reveal="0">
          <h2>Vos concurrents sont déjà sur Google. Et vous ?</h2>
          <p>Commencez par le pack Fiche Google optimisée : c’est le premier endroit où vos futurs clients vous cherchent.</p>
          <a href={siteHref('/store/fiche-google-optimisee/')} className="btn btn-final">Voir le pack à 149 € →</a>
        </div>
      </section>
    </SubShell>
  )
}
