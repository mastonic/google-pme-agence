// Preuves sociales : composants prêts, alimentés UNIQUEMENT par des données réelles et autorisées.
// Tant que les tableaux sont vides, rien n'est affiché (aucun faux avis, aucun faux client).

export type Testimonial = { quote: string; name: string; business: string; city: string; date: string; consent: true }
export type CaseStudy = { business: string; city: string; problem: string; actions: string[]; result: string; period: string; consent: true }

/** À remplir avec des témoignages réels, autorisés par écrit par le client. */
export const TESTIMONIALS: Testimonial[] = []
/** À remplir avec des études de cas réelles, chiffres vérifiables et accord du client. */
export const CASE_STUDIES: CaseStudy[] = []

export function Testimonials() {
  if (TESTIMONIALS.length === 0) return null
  return (
    <section aria-label="Témoignages clients">
      <h2>Ils nous font confiance</h2>
      {TESTIMONIALS.map((t) => (
        <figure key={t.name + t.date} className="callout">
          <blockquote><p>« {t.quote} »</p></blockquote>
          <figcaption>{t.name}, {t.business} ({t.city}), {t.date}</figcaption>
        </figure>
      ))}
    </section>
  )
}

export function CaseStudies() {
  if (CASE_STUDIES.length === 0) return null
  return (
    <section aria-label="Études de cas">
      <h2>Études de cas</h2>
      {CASE_STUDIES.map((c) => (
        <div key={c.business} className="callout">
          <strong>{c.business} ({c.city})</strong>
          <p><strong>Point de départ :</strong> {c.problem}</p>
          <ul>{c.actions.map((a) => <li key={a}>{a}</li>)}</ul>
          <p><strong>Résultat ({c.period}) :</strong> {c.result}</p>
        </div>
      ))}
    </section>
  )
}
