import type { Metadata } from 'next'
import { ArticleLayout, metaFor, type Section, type Source } from '../../../components/ArticleLayout'
import { siteHref } from '../../../seo/domains'
import { CONNECT_PACK_HT, RECEPTIONIST } from '../../../seo/offers'
import { pageMeta } from '../../../seo/seo'

const SLUG = 'receptionniste-ia-artisan'
export const metadata: Metadata = pageMeta(metaFor(SLUG))

const SOURCES: Source[] = [
  ['Pulse Locale PME, conditions générales et politique de confidentialité (section Réceptionniste IA)', 'https://pulse-locale-pme.fr/mentions-legales/#rgpd'],
  ['CNIL, « Le règlement général sur la protection des données (RGPD) »', 'https://www.cnil.fr/fr/reglement-europeen-protection-donnees'],
  ['Règlement (UE) 2024/1689 sur l’intelligence artificielle (EUR-Lex)', 'https://eur-lex.europa.eu/eli/reg/2024/1689/oj'],
]

const SECTIONS: Section[] = [
  {
    id: 'fonctionnement', title: 'Comment fonctionne une réceptionniste IA',
    body: (<>
      <p>Une réceptionniste IA est un agent vocal qui décroche à votre place. Chez Pulse Locale PME, le principe est le suivant :</p>
      <ol>
        <li>Vous activez le <strong>renvoi d’appel</strong> de votre ligne vers le numéro de la réceptionniste, par exemple quand vous ne répondez pas. Votre numéro ne change pas.</li>
        <li>Elle se présente comme l’<strong>assistante virtuelle</strong> de votre entreprise : l’appelant sait qu’il parle à une IA.</li>
        <li>Elle répond aux questions simples à partir des informations que vous avez renseignées (horaires, zone, services).</li>
        <li>Elle <strong>qualifie la demande</strong> : nom, besoin, commune, urgence, créneau souhaité.</li>
        <li>Elle vous envoie un <strong>résumé par WhatsApp ou SMS</strong>. Vous rappelez en priorité les bons contacts.</li>
      </ol>
      <p>Elle répond aussi aux messages WhatsApp. Avec le Pack Connecté, elle consulte vos créneaux réellement libres dans Google Agenda et peut réserver le rendez-vous.</p>
    </>),
  },
  {
    id: 'cas-usage', title: 'Cas d’usage pour les artisans et TPE',
    body: (<>
      <ul>
        <li><strong>Plombier ou électricien sur un chantier</strong> : les appels de dépannage sont notés et classés par urgence.</li>
        <li><strong>Coiffeur ou esthéticienne</strong> en prestation : les demandes de rendez-vous sont prises sans interrompre le client présent.</li>
        <li><strong>Restaurant pendant le service</strong> : les questions sur les horaires et les réservations sont recueillies.</li>
        <li><strong>Garage</strong> : véhicule, type de panne et disponibilité sont transmis avant le rappel.</li>
      </ul>
    </>),
  },
  {
    id: 'transfert', title: 'Transfert d’appel : ce qu’il faut savoir',
    body: (<>
      <p>Le renvoi d’appel se règle depuis votre téléphone ou votre opérateur : renvoi systématique, ou seulement en cas de non-réponse ou d’occupation. Vous pouvez le désactiver à tout moment. C’est vous qui choisissez quand la réceptionniste intervient.</p>
    </>),
  },
  {
    id: 'urgences', title: 'Gestion des urgences',
    body: (<>
      <p>La réceptionniste signale les demandes urgentes dans le résumé envoyé. Elle ne remplace pas un service d’urgence : en cas de danger, elle oriente l’appelant vers le 15, le 18 ou le 112 [1]. Le suivi des demandes reste sous votre responsabilité.</p>
    </>),
  },
  {
    id: 'donnees', title: 'Protection des données',
    body: (<>
      <p>Pour le compte de l’entreprise cliente, la réceptionniste traite le numéro de l’appelant, son nom, le motif, l’adresse et le créneau indiqués, la transcription de l’échange et, en messagerie, l’enregistrement vocal [1]. Les sous-traitants techniques (téléphonie Twilio, WhatsApp, fournisseurs d’IA, hébergement Google) sont listés dans la politique de confidentialité, avec les garanties appliquées aux transferts hors de l’Union européenne [1]. Ces traitements relèvent du RGPD [2].</p>
      <p>Le règlement européen sur l’intelligence artificielle prévoit des obligations de transparence lorsqu’une personne interagit avec un système d’IA [3] : c’est pourquoi la réceptionniste se présente comme une assistante virtuelle.</p>
    </>),
  },
  {
    id: 'limites', title: 'Les limites de l’IA',
    body: (<>
      <ul>
        <li>Elle ne confirme ni prix, ni devis, ni intervention à votre place [1].</li>
        <li>Elle ne connaît que les informations que vous lui donnez : des réglages incomplets donnent des réponses incomplètes.</li>
        <li>La reconnaissance vocale peut mal comprendre un nom ou une adresse dans un environnement bruyant : le résumé est à vérifier lors du rappel.</li>
        <li>Elle dépend de services tiers (opérateurs, téléphonie, IA) dont la disponibilité ne peut être garantie à 100 % [1].</li>
      </ul>
    </>),
  },
  {
    id: 'tarifs', title: 'Tarifs',
    body: (<>
      <ul>
        <li>Essai gratuit de {RECEPTIONIST.trialDays} jours, dans la limite de {RECEPTIONIST.trialCalls} appels, sans engagement.</li>
        <li>Ensuite : {RECEPTIONIST.monthly} € HT par mois avec {RECEPTIONIST.includedCalls} appels inclus.</li>
        <li>Au-delà : {RECEPTIONIST.extraCallHT} € HT ({RECEPTIONIST.extraCallTTC} € TTC) par appel supplémentaire.</li>
        <li>Pack Connecté (Google Agenda, Google Sheets, webhook) : {CONNECT_PACK_HT} € HT par mois, offert pendant l’essai.</li>
        <li>Réceptionniste et Pack Connecté sont inclus dans la formule Élite (299 € HT par mois).</li>
      </ul>
    </>),
  },
]

const FAQS: [string, string][] = [
  ['Mes clients savent-ils qu’ils parlent à une IA ?', 'Oui. La réceptionniste se présente comme l’assistante virtuelle de votre entreprise.'],
  ['Puis-je garder mon numéro de téléphone ?', 'Oui. Vous renvoyez simplement vos appels vers la réceptionniste quand vous ne décrochez pas, et vous pouvez désactiver ce renvoi à tout moment.'],
  ['Que se passe-t-il après 60 appels pendant l’essai ?', 'Au-delà de 60 appels pendant l’essai, les appels arrivent sur une simple messagerie jusqu’à votre souscription.'],
  ['Peut-elle prendre des rendez-vous ?', 'Oui avec le Pack Connecté : elle propose vos créneaux réellement libres dans Google Agenda et crée le rendez-vous.'],
  ['Peut-elle gérer une urgence vitale ?', 'Non. Elle oriente vers le 15, le 18 ou le 112 en cas de danger et signale l’urgence dans le résumé. Elle ne remplace pas un service d’urgence.'],
]

export default function Page() {
  return (
    <ArticleLayout
      slug={SLUG}
      answer="Une réceptionniste IA décroche quand vous ne pouvez pas répondre, grâce à un simple renvoi d’appel : elle se présente comme assistante virtuelle, note le besoin, la commune et l’urgence, puis vous envoie un résumé par WhatsApp ou SMS. Elle ne confirme ni prix ni intervention et ne remplace pas les secours. Chez Pulse Locale PME : 30 jours d’essai (60 appels), puis 39 € HT par mois pour 100 appels."
      sections={SECTIONS}
      faqs={FAQS}
      sources={SOURCES}
      related={['prix-site-internet-artisan-yvelines', 'visibilite-google-maps-chartres']}
      cta={<div className="callout dark"><strong className="mont" style={{ fontSize: 20 }}>Essayer la réceptionniste IA</strong><p>30 jours gratuits dans la limite de 60 appels, sans engagement.</p><div className="hero-ctas"><a href={siteHref('/#receptionniste')} className="btn btn-primary btn-sm">Découvrir la réceptionniste IA →</a><a href={siteHref('/agence-seo-local-yvelines/')} className="btn btn-ghost btn-sm">Yvelines</a><a href={siteHref('/agence-seo-local-eure-et-loir/')} className="btn btn-ghost btn-sm">Eure-et-Loir</a></div></div>}
    />
  )
}
