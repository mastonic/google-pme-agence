import type { Metadata } from 'next'
import { Logo } from '../components/Logo'
import '../landing.css'

export const metadata: Metadata = {
  title: 'Mentions légales, CGV, CGU et confidentialité · Pulse‑Pro',
  description:
    'Mentions légales, conditions générales de vente et d’utilisation, et politique de confidentialité (RGPD) de Pulse‑Pro, solution éditée par HoldMasto.',
  alternates: { canonical: '/mentions-legales/' },
}

const CONTACT = 'rigahludovic@gmail.com'

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="legal-block">
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  )
}

export default function MentionsLegales() {
  return (
    <div id="top" className="legal">
      <header className="site-header">
        <div className="wrap">
          <a href="/" className="brand" aria-label="Pulse‑Pro, accueil">
            <Logo />
          </a>
          <a href="/" className="back">
            ← Retour au site
          </a>
        </div>
      </header>

      <main>
        <div className="wrap legal-hero">
          <span className="eyebrow">Informations légales</span>
          <h1>Mentions légales, CGV, CGU et confidentialité</h1>
          <p className="updated">Dernière mise à jour : novembre 2026</p>
        </div>

        <div className="wrap legal-layout">
          <nav className="legal-nav" aria-label="Sommaire">
            <a href="#mentions">Mentions légales</a>
            <a href="#cgv">Conditions générales de vente</a>
            <a href="#cgu">Conditions générales d’utilisation</a>
            <a href="#rgpd">Confidentialité (RGPD)</a>
          </nav>

          <div className="legal-content">
            <section id="mentions" className="legal-section">
              <h2>Mentions légales</h2>
              <div className="legal-block table">
                <h3>Éditeur du site</h3>
                <div className="kv">
                  <div><span>Raison sociale</span><strong>HoldMasto</strong></div>
                  <div><span>Forme</span><strong>SASU au capital de 10 €</strong></div>
                  <div><span>RCS</span><strong>Fort‑de‑France 106 121 536</strong></div>
                  <div><span>Siège social</span><strong>2 Impasse Bacouna, 97231 Le Robert, France</strong></div>
                  <div><span>Directeur de la publication</span><strong>Ludovic Rigah, Président</strong></div>
                  <div><span>Paiements</span><strong>Stripe · abonnement mensuel</strong></div>
                  <div><span>Contact</span><a href={`mailto:${CONTACT}`}>{CONTACT}</a></div>
                </div>
              </div>
              <Block title="Hébergement">
                Firebase Hosting, service de Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irlande.
              </Block>
              <Block title="Propriété intellectuelle">
                La marque Pulse‑Pro, les textes, visuels et éléments graphiques de ce site sont la propriété de HoldMasto.
                Toute reproduction sans autorisation écrite est interdite.
              </Block>
            </section>

            <section id="cgv" className="legal-section">
              <h2>Conditions générales de vente</h2>
              <Block title="1. Objet">
                Les présentes CGV encadrent la souscription aux abonnements Pulse‑Pro (Starter, Pro, Élite) par des clients
                professionnels auprès de HoldMasto.
              </Block>
              <Block title="2. Démonstration">
                Une démonstration peut être présentée avant toute souscription. Elle est gratuite, n’engage pas le client et
                n’est pas publiée sur son nom de domaine.
              </Block>
              <Block title="3. Tarifs et paiement">
                Les prix sont indiqués par mois. Le paiement est mensuel, par carte bancaire via Stripe, et n’est demandé
                qu’après validation de l’offre choisie.
              </Block>
              <Block title="4. Durée et résiliation">
                L’abonnement est sans engagement de durée. Il peut être résilié à tout moment depuis l’espace client ; la
                résiliation prend effet à la fin de la période mensuelle en cours.
              </Block>
              <Block title="5. Services inclus">
                Le contenu de chaque formule est détaillé sur la page Offres et confirmé avant souscription. Les
                modifications non utilisées dans le mois ne sont pas reportées.
              </Block>
            </section>

            <section id="cgu" className="legal-section">
              <h2>Conditions générales d’utilisation</h2>
              <Block title="Accès au site et à l’espace client">
                Le site est accessible gratuitement. L’espace client est réservé aux abonnés, avec une connexion par lien
                sécurisé envoyé par e-mail.
              </Block>
              <Block title="Contenus fournis par le client">
                Le client garantit détenir les droits sur les textes, logos et photos qu’il transmet, et l’exactitude des
                informations publiées (coordonnées, horaires).
              </Block>
              <Block title="Responsabilité">
                HoldMasto met en œuvre les moyens nécessaires à la disponibilité des sites hébergés, sans pouvoir garantir
                un service ininterrompu.
              </Block>
            </section>

            <section id="rgpd" className="legal-section">
              <h2>Politique de confidentialité (RGPD)</h2>
              <Block title="Responsable du traitement">
                HoldMasto, représentée par Ludovic Rigah, 2 Impasse Bacouna, 97231 Le Robert.
              </Block>
              <Block title="Données collectées">
                Informations professionnelles publiques utilisées pour préparer une démonstration ; coordonnées, contenus et
                données de facturation des clients abonnés ; statistiques de visite des sites hébergés.
              </Block>
              <Block title="Finalités et durée">
                Préparation des démonstrations, exécution du contrat, facturation et suivi des performances. Les données
                sont conservées pendant la durée de l’abonnement, puis selon les obligations légales.
              </Block>
              <Block title="Sous-traitants">
                Google (hébergement Firebase) et Stripe (paiement). Aucune donnée n’est revendue.
              </Block>
              <Block title="Vos droits">
                Vous disposez d’un droit d’accès, de rectification, d’opposition et de suppression. Écrivez à{' '}
                <a href={`mailto:${CONTACT}?subject=${encodeURIComponent('RGPD Pulse-Pro')}`}>{CONTACT}</a>. Vous pouvez
                aussi saisir la CNIL.
              </Block>
            </section>
          </div>
        </div>
      </main>

      <footer className="legal-footer">
        <div className="wrap">
          <span>Pulse‑Pro · solution éditée par HoldMasto</span>
          <span>© 2026 HoldMasto</span>
        </div>
      </footer>
    </div>
  )
}
