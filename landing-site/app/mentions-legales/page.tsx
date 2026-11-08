import type { Metadata } from 'next'
import { pageMeta } from '../seo/seo'
import { Logo } from '../components/Logo'
import '../landing.css'

export const metadata: Metadata = pageMeta({
  title: 'Mentions légales, CGV, CGU et confidentialité | Pulse Locale PME',
  description: 'Mentions légales, conditions générales de vente et d’utilisation, et politique de confidentialité (RGPD) de Pulse Locale PME, solution éditée par HoldMasto.',
  path: '/mentions-legales/',
})

import { CONTACT_EMAIL } from '../components/contact'
import { siteHref } from '../seo/domains'
const CONTACT = CONTACT_EMAIL

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
          <a href={siteHref('/')} className="brand" aria-label="Pulse Locale PME, accueil">
            <Logo />
          </a>
          <a href={siteHref('/')} className="back">
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
                  <div><span>Site et marque</span><strong>Pulse Locale PME · pulse-locale-pme.fr</strong></div>
                  <div><span>Éditeur (maison mère)</span><strong>HoldMasto</strong></div>
                  <div><span>Forme</span><strong>SASU au capital de 10 €</strong></div>
                  <div><span>RCS</span><strong>Fort‑de‑France 106 121 536</strong></div>
                  <div><span>Siège social</span><strong>2 Impasse Bacouna, 97231 Le Robert, France</strong></div>
                  <div><span>Directeur de la publication</span><strong>Ludovic Rigah, Président</strong></div>
                  <div><span>Paiements</span><strong>Stripe · abonnement mensuel ou annuel</strong></div>
                  <div><span>Contact</span><a href={`mailto:${CONTACT}`}>{CONTACT}</a></div>
                </div>
              </div>
              <Block title="Hébergement">
                Firebase Hosting, service de Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irlande.
              </Block>
              <Block title="Propriété intellectuelle">
                La marque Pulse Locale PME, les textes, visuels et éléments graphiques de ce site sont la propriété de HoldMasto.
                Toute reproduction sans autorisation écrite est interdite.
              </Block>
            </section>

            <section id="cgv" className="legal-section">
              <h2>Conditions générales de vente</h2>
              <Block title="1. Objet">
                Les présentes CGV encadrent la souscription aux abonnements Pulse Locale PME (Starter, Pro, Élite) par des clients
                professionnels auprès de HoldMasto.
              </Block>
              <Block title="2. Démonstration">
                Une démonstration peut être présentée avant toute souscription. Elle est gratuite, n’engage pas le client et
                n’est pas publiée sur son nom de domaine.
              </Block>
              <Block title="3. Tarifs et paiement">
                Les prix sont indiqués hors taxes (HT), sans frais de création. Le paiement se fait par carte bancaire via
                Stripe, au choix mensuellement ou annuellement (10 mois facturés pour 12, soit 2 mois offerts), et n’est
                demandé qu’après validation de l’offre choisie.
              </Block>
              <Block title="4. Durée et résiliation">
                L’abonnement mensuel est sans engagement de durée. Il peut être résilié à tout moment depuis l’espace
                client ; la résiliation prend effet à la fin de la période mensuelle en cours. L’abonnement annuel couvre
                douze mois payés d’avance ; il peut être résilié à tout moment et prend fin à l’échéance annuelle, sans
                renouvellement si la résiliation intervient avant cette date.
              </Block>
              <Block title="5. Services inclus">
                Le contenu de chaque formule est détaillé sur la page Offres et confirmé avant souscription. Les
                modifications non utilisées dans le mois ne sont pas reportées. Dans la formule Élite, les demandes de
                modification sont limitées à dix par mois dans le cadre d’un usage raisonnable.
              </Block>
              <Block title="6. Réceptionniste IA">
                La Réceptionniste IA est proposée en essai gratuit de 30 jours, limité à 60 appels ou conversations
                pris en charge par l’IA. Une conversation commencée avant ce plafond se poursuit jusqu’à son terme ; au-delà
                du plafond ou de la durée d’essai, et sans souscription, les appels renvoyés aboutissent sur une simple
                messagerie (message transmis au client). L’option payante coûte 39 € HT par mois et comprend 100 appels
                ou conversations par mois ; chaque appel supplémentaire est facturé 0,83 € HT, soit 1 € TTC, en fin de
                mois. Un appel ou une conversation WhatsApp compte pour une unité, quelle que soit sa durée dans la limite
                de 5 minutes ; au-delà, il compte pour deux. Elle est incluse dans la formule Élite (100 appels par mois,
                même tarif au-delà). L’option est sans engagement et résiliable à tout moment depuis l’espace client.
              </Block>
              <Block title="7. Pack Connecté">
                Le Pack Connecté (Google Agenda, Google Sheets et webhook) est proposé à 19 € HT par mois, sans engagement.
                Il est offert pendant l’essai de la Réceptionniste IA et inclus dans la formule Élite. Il prend fin avec
                l’option Réceptionniste IA.
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
              <Block title="Applications connectées (Pack Connecté)">
                Le client peut connecter son compte Google et une adresse de webhook. L’accès Google est limité à la
                lecture des disponibilités et à la création d’événements dans l’agenda, et aux seuls fichiers créés par
                Pulse Locale PME dans son Drive (tableur des appels). Le client peut retirer cet accès à tout moment depuis
                son espace ou son compte Google. Les rendez-vous ne sont proposés que sur des créneaux libres de l’agenda ;
                le client reste responsable de leur honoration et des informations transmises à ses propres applications
                via le webhook.
              </Block>
              <Block title="Réceptionniste IA">
                Le client active lui-même le renvoi de ses appels vers le numéro de la réceptionniste et peut le désactiver
                à tout moment. La réceptionniste se présente comme une assistante virtuelle : l’appelant est informé qu’il
                échange avec une intelligence artificielle. Elle prend des messages et qualifie les demandes à partir des
                seules informations fournies par le client ; elle ne confirme ni prix, ni rendez-vous, ni intervention, et
                oriente vers le 15, le 18 ou le 112 en cas de danger. Elle ne remplace pas un service d’urgence et le
                client reste responsable du suivi des demandes qui lui sont transmises. Le nombre d’appels pris en charge
                et la consommation du mois sont consultables dans l’espace client.
              </Block>
              <Block title="Responsabilité">
                HoldMasto met en œuvre les moyens nécessaires à la disponibilité des sites hébergés et de la réceptionniste,
                sans pouvoir garantir un service ininterrompu, notamment en cas d’indisponibilité des opérateurs
                téléphoniques ou des services tiers (Twilio, WhatsApp, fournisseurs d’IA).
              </Block>
            </section>

            <section id="rgpd" className="legal-section">
              <h2>Politique de confidentialité (RGPD)</h2>
              <Block title="Responsable du traitement">
                HoldMasto, représentée par Ludovic Rigah, 2 Impasse Bacouna, 97231 Le Robert.
              </Block>
              <Block title="Données collectées">
                Informations professionnelles publiques utilisées pour préparer une démonstration ; coordonnées, contenus et
                données de facturation des clients abonnés ; statistiques de visite des sites hébergés ; demandes envoyées
                par les formulaires du site. Pour la Réceptionniste IA, agissant pour le compte du client : numéro de
                l’appelant, nom, motif, adresse et créneau indiqués, transcription de l’échange et, en messagerie,
                enregistrement vocal.
              </Block>
              <Block title="Finalités et durée">
                Préparation des démonstrations, réponse aux demandes envoyées par les formulaires (contact, devis,
                démonstration, audit, support), exécution du contrat, facturation et suivi des performances. Durées :
                demandes reçues par formulaire, 3 ans après le dernier échange ; copies des emails envoyés
                (accusés de réception, notifications), 90 jours ; données des clients, durée de l’abonnement puis
                selon les obligations légales ; pièces comptables (commandes, factures), 10 ans. Un accusé de réception
                est un email de service : il n’inscrit à aucune newsletter.
              </Block>
              <Block title="Sous-traitants">
                Google (hébergement Firebase et Cloud Run ; API Google Agenda et Google Sheets si le client les connecte),
                IONOS (messagerie : envoi des accusés de réception et des notifications), Stripe (paiement), Twilio (téléphonie, SMS et WhatsApp, avec
                Meta pour WhatsApp) et fournisseurs d’intelligence artificielle (Google Gemini ; OpenAI ou Mistral en
                secours). Certains de ces sous-traitants peuvent traiter des données hors de l’Union européenne, dans le
                cadre de garanties appropriées (clauses contractuelles types). Aucune donnée n’est revendue.
              </Block>
              <Block title="Données Google">
                Lorsque le client connecte son compte Google, Pulse Locale PME n’accède qu’à ses disponibilités et aux
                événements qu’elle crée dans son agenda, et aux seuls fichiers qu’elle crée dans son Drive. Ces données
                servent uniquement à proposer et réserver des rendez-vous et à tenir le registre des appels ; elles ne
                sont ni vendues, ni utilisées à des fins publicitaires, ni pour entraîner des modèles d’IA. L’utilisation
                des informations reçues des API Google respecte la politique Google API Services User Data Policy, y
                compris ses exigences d’utilisation limitée (Limited Use). Le jeton d’accès est conservé chiffré et
                supprimé à la déconnexion.
              </Block>
              <Block title="Vos droits">
                Vous disposez d’un droit d’accès, de rectification, d’opposition et de suppression. Écrivez à{' '}
                <a href={`mailto:${CONTACT}?subject=${encodeURIComponent('RGPD Pulse Locale PME')}`}>{CONTACT}</a>. Vous pouvez
                aussi saisir la CNIL.
              </Block>
            </section>
          </div>
        </div>
      </main>

      <footer className="legal-footer">
        <div className="wrap">
          <span>Pulse Locale PME · édité par HoldMasto, maison mère</span>
          <span>© 2026 HoldMasto</span>
        </div>
      </footer>
    </div>
  )
}
