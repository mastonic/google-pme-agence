'use client'

import { useState } from 'react'
import { mail } from '../../components/SubShell'

type Q = { id: string; q: string; opts: [string, number][]; fix: string; w: number }

const QS: Q[] = [
  { id: 'fiche', q: 'Avez-vous une fiche Google Business (Google Maps) ?', w: 20,
    opts: [['Oui, à jour', 1], ['Oui, mais pas touchée depuis longtemps', 0.4], ['Non / je ne sais pas', 0]],
    fix: 'Créez ou reprenez votre fiche Google : c’est la base de tout le reste.' },
  { id: 'cat', q: 'Votre catégorie principale décrit-elle exactement votre métier ?', w: 10,
    opts: [['Oui', 1], ['Je ne sais pas', 0.3], ['Non', 0]],
    fix: 'Choisissez la catégorie la plus précise (« Plombier » plutôt que « Entreprise »).' },
  { id: 'avis', q: 'Combien d’avis Google avez-vous ?', w: 15,
    opts: [['Plus de 50', 1], ['Entre 10 et 50', 0.6], ['Moins de 10', 0.2]],
    fix: 'Demandez systématiquement un avis : un QR code au comptoir suffit pour démarrer.' },
  { id: 'note', q: 'Votre note moyenne ?', w: 10,
    opts: [['4,5 ou plus', 1], ['Entre 4 et 4,4', 0.6], ['Moins de 4 / aucune', 0.1]],
    fix: 'Répondez à chaque avis, surtout les négatifs : c’est lu par vos futurs clients.' },
  { id: 'photos', q: 'Avez-vous publié des photos récentes (moins de 3 mois) ?', w: 10,
    opts: [['Oui, plus de 10', 1], ['Quelques-unes', 0.5], ['Non', 0]],
    fix: 'Ajoutez 10 photos réelles : devanture, équipe, réalisations.' },
  { id: 'site', q: 'Avez-vous un site web qui s’affiche bien sur mobile ?', w: 15,
    opts: [['Oui', 1], ['Oui, mais vieux ou lent', 0.4], ['Non', 0]],
    fix: 'Un site mobile simple avec bouton « Appeler » rassure et convertit.' },
  { id: 'nap', q: 'Nom, adresse et téléphone sont-ils identiques partout (Google, site, Pages Jaunes…) ?', w: 10,
    opts: [['Oui', 1], ['Je ne sais pas', 0.3], ['Non', 0]],
    fix: 'Harmonisez vos coordonnées partout : les incohérences font baisser votre fiabilité.' },
  { id: 'ia', q: 'Si on demande à ChatGPT « un bon [votre métier] à [votre ville] », vous apparaissez ?', w: 10,
    opts: [['Oui', 1], ['Je n’ai jamais testé', 0.2], ['Non', 0]],
    fix: 'Testez-vous dans les IA : elles s’appuient sur vos avis, votre site et les annuaires.' },
]

export function ScoreTool() {
  const [a, setA] = useState<Record<string, number>>({})
  const [done, setDone] = useState(false)
  const [name, setName] = useState('')
  const answered = Object.keys(a).length
  const score = Math.round(QS.reduce((s, q) => s + (a[q.id] ?? 0) * q.w, 0))
  const fixes = [...QS].sort((x, y) => (1 - (a[y.id] ?? 0)) * y.w - (1 - (a[x.id] ?? 0)) * x.w).filter((q) => (a[q.id] ?? 0) < 1).slice(0, 3)
  const color = score >= 70 ? '#047857' : score >= 40 ? '#C9A24B' : '#B45309'
  const verdict = score >= 70 ? 'Bonne base ! Quelques réglages et vous passez devant.' : score >= 40 ? 'Vous êtes visible, mais vos concurrents prennent une partie de vos clients.' : 'Vous êtes quasi invisible : des clients vous cherchent et tombent sur un autre.'

  if (done)
    return (
      <div className="tool" aria-live="polite">
        <div className="score">
          <div className="gauge" style={{ ['--v' as string]: score, ['--c' as string]: color }}><b>{score}</b></div>
          <div className="stack" style={{ gap: 8, flex: 1, minWidth: 240 }}>
            <span className="eyebrow">Votre score{name ? ` · ${name}` : ''}</span>
            <h2 className="mont" style={{ fontSize: 28 }}>{verdict}</h2>
          </div>
        </div>
        <div className="stack" style={{ gap: 12 }}>
          <h3 className="mont" style={{ fontSize: 20 }}>Vos 3 actions prioritaires</h3>
          <ol className="fixes">{fixes.map((f) => <li key={f.id}>{f.fix}</li>)}</ol>
        </div>
        <div className="callout">
          <strong className="mont">Recevez votre rapport détaillé + le guide PDF</strong>
          <p>On vous envoie l’analyse complète de votre fiche et la checklist des 10 erreurs, gratuitement.</p>
          <div className="hero-ctas">
            <a className="btn btn-primary btn-sm" href={mail(`Rapport visibilité - ${name || 'mon commerce'} - score ${score}/100`)}>Recevoir mon rapport →</a>
            <a className="btn btn-outline" href="/store/">Qu’on s’en occupe pour moi</a>
          </div>
        </div>
        <button className="btn btn-outline" onClick={() => { setA({}); setDone(false) }} style={{ alignSelf: 'flex-start', cursor: 'pointer' }}>Refaire le test</button>
      </div>
    )

  return (
    <form className="tool" onSubmit={(e) => { e.preventDefault(); setDone(true) }}>
      <label className="field">Nom de votre commerce (facultatif)
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="ex. Plomberie Martin, Trappes" />
      </label>
      {QS.map((q, i) => (
        <fieldset key={q.id} className="q" style={{ border: 0, margin: 0, padding: '0 0 18px' }}>
          <legend>{i + 1}. {q.q}</legend>
          <div className="q-opts">
            {q.opts.map(([l, v]) => (
              <label key={l}>
                <input type="radio" name={q.id} checked={a[q.id] === v} onChange={() => setA({ ...a, [q.id]: v })} />
                <span>{l}</span>
              </label>
            ))}
          </div>
        </fieldset>
      ))}
      <button type="submit" className="btn btn-primary" disabled={answered < QS.length} style={{ cursor: 'pointer', border: 0, opacity: answered < QS.length ? 0.5 : 1 }}>
        {answered < QS.length ? `Encore ${QS.length - answered} question(s)` : 'Voir mon score →'}
      </button>
    </form>
  )
}
