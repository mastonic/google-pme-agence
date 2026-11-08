import { siteHref } from '../seo/domains'
import { CONNECT_PACK_HT, PACKS_HT, PLANS_HT, RECEPTIONIST, fmt } from '../seo/offers'

/** Tarifs réels (HT) affichés dans les pages locales et articles : une seule source, seo/offers.ts. */
export function PricingTable() {
  return (
    <>
      <div className="table-wrap">
        <table className="seo-table">
          <caption>Abonnements Pulse Locale PME (prix hors taxes, sans frais de création)</caption>
          <thead>
            <tr><th scope="col">Formule</th><th scope="col">Mensuel</th><th scope="col">Annuel (2 mois offerts)</th><th scope="col">Contenu</th></tr>
          </thead>
          <tbody>
            {PLANS_HT.map((p) => (
              <tr key={p.name}><th scope="row">{p.name}</th><td>{fmt(p.monthly)} € HT</td><td>{fmt(p.annual)} € HT</td><td>{p.summary}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul>
        <li><a href={siteHref(PACKS_HT.ficheGoogle.path)} className="link-underline">{PACKS_HT.ficheGoogle.name}</a> : {PACKS_HT.ficheGoogle.price} € HT, une seule fois, livrée en {PACKS_HT.ficheGoogle.delay}.</li>
        <li><a href={siteHref(PACKS_HT.avis.path)} className="link-underline">{PACKS_HT.avis.name}</a> et <a href={siteHref(PACKS_HT.auditIA.path)} className="link-underline">{PACKS_HT.auditIA.name}</a> : {PACKS_HT.avis.price} € HT chacun.</li>
        <li>Réceptionniste IA : essai gratuit {RECEPTIONIST.trialDays} jours dans la limite de {RECEPTIONIST.trialCalls} appels, puis {RECEPTIONIST.monthly} € HT par mois avec {RECEPTIONIST.includedCalls} appels inclus, {RECEPTIONIST.extraCallHT} € HT ({RECEPTIONIST.extraCallTTC} € TTC) par appel supplémentaire ; incluse dans Élite.</li>
        <li>Pack Connecté (Google Agenda, Sheets, webhook) : {CONNECT_PACK_HT} € HT par mois, inclus dans Élite.</li>
      </ul>
    </>
  )
}
