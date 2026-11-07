'use client'

import { useEffect, useRef, useState } from 'react'
import '../showreel.css'

export type Chapter = { label: string; title: string; text: string; scene: React.ReactNode }

const DURATION = 5200

/**
 * Lecteur « showreel » : scènes animées en CSS, enchaînées automatiquement quand le bloc est visible.
 * Chapitres cliquables, pause, et sans lecture auto si l'appareil demande moins d'animations.
 */
export function Showreel({ chapters, id }: { chapters: Chapter[]; id: string }) {
  const [i, setI] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [visible, setVisible] = useState(false)
  const [reduced, setReduced] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const r = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    setReduced(r)
    setPlaying(!r)
    const io = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { threshold: 0.35 })
    if (ref.current) io.observe(ref.current)
    return () => io.disconnect()
  }, [])

  useEffect(() => {
    if (!playing || !visible) return
    const t = window.setTimeout(() => setI((n) => (n + 1) % chapters.length), DURATION)
    return () => window.clearTimeout(t)
  }, [i, playing, visible, chapters.length])

  const running = playing && visible
  const c = chapters[i]

  return (
    <div ref={ref} className={`reel${running ? ' is-running' : ''}${reduced ? ' is-reduced' : ''}`} style={{ ['--dur' as string]: `${DURATION}ms` }}>
      <div className="reel-screen" aria-hidden="true">
        <div className="reel-chrome"><i /><i /><i /><span>{c.label}</span><b>{String(i + 1).padStart(2, '0')} / {String(chapters.length).padStart(2, '0')}</b></div>
        <div className="reel-stage" key={`${id}-${i}`}>{c.scene}</div>
      </div>

      <div className="reel-side">
        <div className="reel-caption" key={`cap-${i}`} aria-live="polite">
          <span className="eyebrow">{c.label}</span>
          <h3>{c.title}</h3>
          <p>{c.text}</p>
        </div>
        <ol className="reel-chapters">
          {chapters.map((ch, n) => (
            <li key={ch.label}>
              <button type="button" className={n === i ? 'on' : n < i ? 'done' : ''} onClick={() => setI(n)} aria-current={n === i}>
                <span className="reel-num">{n + 1}</span>
                <span className="reel-lab">{ch.title}</span>
                <span className="reel-bar"><span /></span>
              </button>
            </li>
          ))}
        </ol>
        <button type="button" className="reel-toggle" onClick={() => setPlaying((p) => !p)}>
          {playing ? '❚❚ Pause' : '▶ Lecture'}
        </button>
      </div>
    </div>
  )
}

/* ─────────── Scènes ─────────── */

export function SceneSite() {
  return (
    <div className="sc sc-site">
      <div className="phone">
        <div className="ph-hero"><span className="ph-logo">Plomberie Martin</span><b>Dépannage en 2 h à Trappes</b></div>
        <div className="ph-line l1" /><div className="ph-line l2" /><div className="ph-line l3" />
        <div className="ph-stars">★★★★★ <span>4,9 · 87 avis</span></div>
        <div className="ph-btns"><span className="call">Appeler</span><span className="wa">WhatsApp</span></div>
      </div>
      <div className="tag t1">Mobile d’abord</div>
      <div className="tag t2">En ligne en 7 jours</div>
      <div className="tag t3">Image pro ✓</div>
    </div>
  )
}

export function SceneMaps() {
  return (
    <div className="sc sc-maps">
      <div className="search"><span className="typed">plombier près de moi</span></div>
      <div className="map">
        <i className="pin p1" /><i className="pin p2" /><i className="pin p3 you" />
      </div>
      <div className="results">
        <div className="res you"><b>Plomberie Martin</b><span>★ 4,9 · Ouvert · 1,2 km</span><em>#1</em></div>
        <div className="res r2"><b>Concurrent A</b><span>★ 4,1 · 2,8 km</span></div>
        <div className="res r3"><b>Concurrent B</b><span>★ 3,8 · 4 km</span></div>
      </div>
    </div>
  )
}

export function SceneCalm() {
  const items = ['Hébergement', 'Certificat SSL', 'Sauvegardes', 'Mises à jour', 'Modifications']
  return (
    <div className="sc sc-calm">
      <ul className="checks">{items.map((t, n) => <li key={t} style={{ ['--n' as string]: n }}><i>✓</i>{t}</li>)}</ul>
      <div className="notifs">
        <div className="nt n1"><i>📞</i><b>Nouvel appel</b><span>Fuite cuisine · Élancourt</span></div>
        <div className="nt n2"><i>💬</i><b>WhatsApp</b><span>Devis chauffe-eau</span></div>
        <div className="nt n3"><i>★</i><b>Nouvel avis 5★</b><span>« Rapide et propre »</span></div>
      </div>
    </div>
  )
}

export function SceneAnalyse() {
  return (
    <div className="sc sc-analyse">
      <div className="card-a">
        <b>Votre présence aujourd’hui</b>
        {[['Fiche Google', 38], ['Avis', 52], ['Site mobile', 20], ['Cohérence infos', 64]].map(([l, v], n) => (
          <div className="meter" key={l} style={{ ['--v' as string]: v, ['--n' as string]: n }}><span>{l}</span><div><i /></div><em>{v}</em></div>
        ))}
      </div>
      <div className="scanline" />
      <div className="tag t1">3 points de friction trouvés</div>
    </div>
  )
}

export function SceneDemo() {
  return (
    <div className="sc sc-demo">
      <div className="browser">
        <div className="bw-bar"><i /><i /><i /><span>demo.pulse-pro/plomberie-martin</span></div>
        <div className="bw-hero"><b>Plomberie Martin</b><span>Votre plombier à Trappes, 7j/7</span><em>Appeler</em></div>
        <div className="bw-grid"><i /><i /><i /></div>
      </div>
      <div className="stamp">DÉMO PRÊTE</div>
      <div className="tag t2">Gratuit · Rien n’est publié</div>
    </div>
  )
}

export function SceneValidate() {
  const items = ['Logo et couleurs', 'Photos', 'Horaires', 'Services et prix', 'Formule choisie']
  return (
    <div className="sc sc-validate">
      <div className="form-v">
        <b>Vous validez</b>
        <ul>{items.map((t, n) => <li key={t} style={{ ['--n' as string]: n }}><i />{t}</li>)}</ul>
        <span className="go">Valider et mettre en ligne</span>
      </div>
      <div className="cursor" />
    </div>
  )
}

export function SceneRun() {
  return (
    <div className="sc sc-run">
      <div className="kpis">
        {[['Appels', '+38'], ['WhatsApp', '+21'], ['Itinéraires', '+64'], ['Avis', '+12']].map(([l, v], n) => (
          <div className="kpi" key={l} style={{ ['--n' as string]: n }}><span>{l}</span><b>{v}</b><em>ce mois</em></div>
        ))}
      </div>
      <svg className="curve" viewBox="0 0 300 90" preserveAspectRatio="none"><path d="M0 80 C 60 74, 90 60, 140 52 S 230 22, 300 8" /></svg>
      <div className="tag t3">Rapport mensuel envoyé</div>
    </div>
  )
}
