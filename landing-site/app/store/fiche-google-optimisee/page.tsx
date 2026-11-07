import type { Metadata } from 'next'
import { SubShell, mail } from '../../components/SubShell'

export const metadata: Metadata = {
  title: 'Fiche Google optimisée · 149 € · Boutique Pulse‑Pro',
  description:
    'Votre fiche Google Business refaite par un expert : catégories, description, photos, posts. Livrée en 5 jours ouvrés. Prix fixe 149 €.',
  alternates: { canonical: '/store/fiche-google-optimisee/' },
}

const ROWS = [
  ['Catégorie', '1 catégorie générique', 'Catégorie principale + 4 secondaires choisies sur vos vraies recherches'],
  ['Description', 'Vide ou 2 lignes', '750 caractères rédigés avec votre métier, votre ville et vos services'],
  ['Photos', '3 photos floues', '10 photos retouchées, nommées et géolocalisées'],
  ['Services', 'Non renseignés', 'Liste complète avec prix indicatifs'],
  ['Activité', 'Aucun post depuis 2023', '4 posts prêts à publier sur 1 mois'],
]

const STEPS = [
  ['Jour 0', 'Vous payez et remplissez le formulaire (5 min).'],
  ['Jour 1-2', 'Audit de votre fiche et de vos 3 concurrents les mieux placés.'],
  ['Jour 3-4', 'Réécriture, photos, catégories, services, posts.'],
  ['Jour 5', 'Mise en ligne + rapport avant / après envoyé par email.'],
]

export default function Product() {
  return (
    <SubShell variant="store">
      <div className="wrap" style={{ paddingTop: 28 }}>
        <p className="crumbs"><a href="/store/">Boutique</a> / Packs / Fiche Google optimisée</p>
      </div>
      <section className="wrap product">
        <div className="stack" style={{ gap: 28 }}>
          <span className="card-tag gold">Le plus vendu</span>
          <h1 className="h2" style={{ fontSize: 'clamp(36px,5vw,58px)' }}>
            Quand on cherche votre métier dans votre ville, c’est vous qu’on doit voir.
          </h1>
          <p className="hero-lead">
            Sur Google Maps, une fiche incomplète, c’est un client qui appelle le
            concurrent juste à côté. On transforme votre fiche en vitrine qui fait sonner le téléphone.
          </p>

          <h2 className="mont" style={{ fontSize: 26 }}>Avant / après, concrètement</h2>
          <table className="compare">
            <thead><tr><th>Élément</th><th>Fiche typique</th><th>Après Pulse‑Pro</th></tr></thead>
            <tbody>
              {ROWS.map(([a, b, c]) => (
                <tr key={a}><th>{a}</th><td className="before">{b}</td><td className="after">{c}</td></tr>
              ))}
            </tbody>
          </table>

          <h2 className="mont" style={{ fontSize: 26 }}>Comment ça se passe</h2>
          <div className="steps">
            {STEPS.map(([d, t], i) => (
              <div key={d} className={`step${i === STEPS.length - 1 ? ' last' : ''}`}>
                <span className="step-num" style={{ width: 'auto', padding: '0 14px', borderRadius: 999 }}>{d}</span>
                <p>{t}</p>
              </div>
            ))}
          </div>

          <div className="callout">
            <strong className="mont" style={{ fontSize: 20 }}>Garantie « refait sans frais »</strong>
            <p>
              Si un élément livré ne correspond pas à ce qui est décrit sur cette page, on le refait gratuitement. Nous
              ne promettons pas de position exacte : personne ne contrôle l’algorithme de Google. Nous promettons une
              fiche complète, conforme et mieux armée que celle de vos concurrents.
            </p>
          </div>
        </div>

        <aside className="buybox" aria-label="Acheter ce pack">
          <h2 className="mont" style={{ fontSize: 22 }}>Fiche Google optimisée</h2>
          <div className="price"><strong>149 €</strong><span>HT · paiement unique</span></div>
          <ul className="ticks">
            <li>Catégories et services optimisés</li>
            <li>Description rédigée pour votre ville</li>
            <li>10 photos retouchées</li>
            <li>4 posts Google prêts à publier</li>
            <li>Rapport avant / après</li>
          </ul>
          <a href={mail('Commande - Fiche Google optimisée 149 €')} className="btn btn-primary" style={{ textAlign: 'center' }}>
            Commander maintenant →
          </a>
          <p className="small muted">Livré en 5 jours ouvrés · Facture automatique · Sans abonnement</p>
          <hr style={{ border: 0, borderTop: '1px solid #E2E8F0', width: '100%' }} />
          <p className="small muted">
            <strong style={{ color: '#1E293B' }}>Souvent pris ensemble :</strong> Pack 50 avis (99 €) pour remonter votre
            note dans la foulée.
          </p>
        </aside>
      </section>
    </SubShell>
  )
}
