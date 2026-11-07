import type { Metadata } from 'next'
import { SubShell } from '../../../components/SubShell'

export const metadata: Metadata = {
  title: 'Plombier : comment sortir en premier sur Google Maps dans votre ville · Pulse‑Pro',
  description:
    'Guide pratique pour plombiers : fiche Google, catégories, zone d’intervention, avis et urgences. Les réglages qui font sonner le téléphone.',
  alternates: { canonical: '/info/guides/plombier/' },
}

export default function Guide() {
  return (
    <SubShell variant="info">
      <article className="article">
        <p className="crumbs"><a href="/info/">Ressources</a> / <a href="/info/#guides">Guides métier</a> / Plombier</p>
        <span className="eyebrow">Guide métier · Plombier</span>
        <h1>Plombier : sortir en premier sur Google Maps quand un client a une fuite.</h1>
        <div className="meta"><span>Lecture : 7 min</span><span>Mis à jour en novembre 2026</span></div>
        <p>
          Un client qui a de l’eau partout ne compare pas dix devis. Il tape « plombier » ou « plombier urgence » sur
          son téléphone et appelle l’un des trois premiers résultats de la carte. Ce guide vous explique comment faire
          partie de ces trois-là.
        </p>

        <nav className="toc" aria-label="Sommaire">
          <strong className="mont">Au sommaire</strong>
          <ol>
            <li>Les bonnes catégories</li>
            <li>Déclarer sa zone d’intervention</li>
            <li>Les services à lister</li>
            <li>Les avis qui rassurent en urgence</li>
            <li>Être joignable (vraiment)</li>
          </ol>
        </nav>

        <h2>1. Les bonnes catégories</h2>
        <p>
          Catégorie principale : <strong>Plombier</strong>. Ajoutez ensuite les catégories secondaires qui correspondent
          vraiment à votre activité : <em>Chauffagiste</em>, <em>Service de débouchage</em>, <em>Entreprise de
          chauffe-eau</em>. N’ajoutez pas une catégorie que vous ne faites pas : Google le repère avec les avis.
        </p>

        <h2>2. Déclarer sa zone d’intervention</h2>
        <p>
          Vous travaillez chez vos clients : déclarez-vous en « entreprise de services de proximité » et masquez votre
          adresse si vous recevez à domicile. Listez les communes que vous couvrez vraiment (Trappes, Élancourt,
          Plaisir, Montigny…), pas tout le département.
        </p>

        <h2>3. Les services à lister</h2>
        <ul>
          <li>Recherche de fuite</li>
          <li>Débouchage canalisation / WC</li>
          <li>Remplacement chauffe-eau / ballon</li>
          <li>Dépannage urgence 7j/7 (seulement si c’est vrai)</li>
          <li>Rénovation salle de bains</li>
        </ul>
        <p>Chaque service avec une phrase de description : ce sont des mots que Google relie aux recherches.</p>

        <div className="callout">
          <strong className="mont">L’astuce qui change tout</strong>
          <p>
            Après chaque intervention, envoyez un SMS avec votre lien d’avis pendant que le client est encore soulagé.
            Le taux de réponse est bien meilleur à chaud que trois jours plus tard.
          </p>
        </div>

        <h2>4. Les avis qui rassurent en urgence</h2>
        <p>
          En urgence, le client lit deux ou trois avis, pas plus. Il cherche : rapidité, prix annoncé respecté, propreté.
          Répondez à chaque avis en reprenant ces mots (« merci, ravi d’être intervenu rapidement à Plaisir »). Ça
          rassure le lecteur et renforce votre fiche.
        </p>

        <h2>5. Être joignable (vraiment)</h2>
        <p>
          Horaires exacts, horaires spéciaux pour les jours fériés, et un numéro qui répond. Un appel manqué, c’est un
          client perdu : il rappelle le suivant. Si vous êtes sur un chantier, un renvoi vers un assistant qui prend le
          message et vous l’envoie par SMS évite de perdre ces appels.
        </p>

        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>Vous voulez qu’on le fasse pour vous ?</strong>
          <p>Le pack Fiche Google optimisée applique tout ce guide à votre fiche, livré en 5 jours.</p>
          <div className="hero-ctas">
            <a href="/store/fiche-google-optimisee/" className="btn btn-primary btn-sm">Voir le pack à 149 € →</a>
            <a href="/info/outil-gratuit/" className="btn btn-ghost btn-sm">Faire le test gratuit</a>
          </div>
        </div>
      </article>
    </SubShell>
  )
}
