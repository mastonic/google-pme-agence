"use client"

import { useEffect, useState } from 'react'

const BUSINESSES = [
  {
    query: 'boulangerie près de moi',
    cat: 'Boulangerie · Le Robert',
    rating: '4,9',
    reviews: 127,
    close: '19:00',
    author: 'M',
    review: '« Pain excellent et accueil au top. Je les ai trouvés en 2 minutes sur Google ! »',
    photos: ['linear-gradient(135deg,#C9A24B 0%,#E8C98A 45%,#8C6A2C 100%)', 'linear-gradient(135deg,#00A896,#028090)', 'linear-gradient(135deg,#F1E3C4,#D9B877)'],
  },
  {
    query: 'plombier urgence Le Robert',
    cat: 'Plombier · Le Robert',
    rating: '4,8',
    reviews: 86,
    close: '20:00',
    author: 'S',
    review: '« Intervention rapide, prix annoncé respecté. Je recommande ! »',
    photos: ['linear-gradient(135deg,#1E293B 0%,#334155 60%,#028090 100%)', 'linear-gradient(135deg,#8FDCD1,#00A896)', 'linear-gradient(135deg,#CBD5E1,#94A3B8)'],
  },
  {
    query: 'coiffeur ouvert maintenant',
    cat: 'Salon de coiffure · Le Robert',
    rating: '5,0',
    reviews: 64,
    close: '18:30',
    author: 'L',
    review: '« Rendez-vous pris en ligne, coupe parfaite. Mon nouveau salon ! »',
    photos: ['linear-gradient(135deg,#05445E 0%,#028090 55%,#00A896 100%)', 'linear-gradient(135deg,#E8C98A,#C9A24B)', 'linear-gradient(135deg,#E6F7F5,#8FDCD1)'],
  },
]

const ACTIONS: [string, string][] = [
  ['☎', 'Appeler'],
  ['➤', 'Itinéraire'],
  ['◍', 'Site web'],
  ['✉', 'WhatsApp'],
]

const TYPE_MS = 55
const HOLD_MS = 4200

export function GoogleCard() {
  const [idx, setIdx] = useState(0)
  const [typed, setTyped] = useState(BUSINESSES[0].query.length)
  const [shown, setShown] = useState(true)
  const [animated, setAnimated] = useState(false)

  useEffect(() => {
    if (!document.documentElement.classList.contains('motion')) return
    setAnimated(true)
    let cancelled = false
    const timers: number[] = []
    const wait = (ms: number) => new Promise<void>((r) => timers.push(window.setTimeout(r, ms)))

    const run = async (i: number) => {
      if (cancelled) return
      const q = BUSINESSES[i].query
      setShown(false)
      setIdx(i)
      setTyped(0)
      await wait(i === 0 ? 700 : 350)
      for (let n = 1; n <= q.length; n++) {
        if (cancelled) return
        setTyped(n)
        await wait(TYPE_MS)
      }
      await wait(250)
      if (cancelled) return
      setShown(true)
      await wait(HOLD_MS)
      run((i + 1) % BUSINESSES.length)
    }
    run(0)
    return () => {
      cancelled = true
      timers.forEach(clearTimeout)
    }
  }, [])

  const b = BUSINESSES[idx]
  const cls = ['gbp', animated ? 'gbp-anim' : '', shown ? 'gbp-on' : ''].join(' ')

  return (
    <div className={cls} aria-hidden="true">
      <div className="gbp-search">
        <svg viewBox="0 0 24 24" width="18" height="18">
          <circle cx="11" cy="11" r="7" fill="none" stroke="#64748B" strokeWidth="2" />
          <path d="M16.5 16.5 21 21" stroke="#64748B" strokeWidth="2" strokeLinecap="round" />
        </svg>
        <span>
          {b.query.slice(0, typed)}
          {animated && <span className="gbp-caret" />}
        </span>
      </div>
      <div className="gbp-card" key={idx}>
        <div className="gbp-photos">
          {b.photos.map((bg, k) => (
            <div key={k} className={`ph ph${k + 1}`} style={{ background: bg }} />
          ))}
        </div>
        <div className="gbp-body">
          <div className="gbp-head">
            <h3>Votre commerce</h3>
            <span className="badge-google">1er résultat</span>
          </div>
          <div className="gbp-rating">
            <strong>{b.rating}</strong>
            <span className="stars">
              {[0, 1, 2, 3, 4].map((s) => (
                <span key={s} style={{ ['--i' as string]: s }}>★</span>
              ))}
            </span>
            <span className="muted">({b.reviews} avis)</span>
          </div>
          <span className="muted">{b.cat}</span>
          <span className="gbp-open">
            <b>Ouvert</b> · Ferme à {b.close}
          </span>
          <div className="gbp-actions">
            {ACTIONS.map(([icon, label], k) => (
              <span key={label} style={{ ['--i' as string]: k }}>
                <i>{icon}</i>
                {label}
              </span>
            ))}
          </div>
          <div className="gbp-review">
            <span className="gbp-avatar">{b.author}</span>
            <p>{b.review}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
