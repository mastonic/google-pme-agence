"use client"

import { useEffect, useState } from 'react'

/**
 * Animation du haut de la landing, en deux scènes par métier :
 *  1. le client trouve le commerce sur sa fiche Google ;
 *  2. il appelle, la Réceptionniste IA décroche et le gérant reçoit un SMS résumé.
 */

type Line = { from: 'client' | 'ia'; text: string }

const BUSINESSES: {
  query: string
  cat: string
  rating: string
  reviews: number
  close: string
  author: string
  review: string
  photos: string[]
  caller: string
  call: Line[]
  sms: string
}[] = [
  {
    query: 'boulangerie près de moi',
    cat: 'Boulangerie · Le Robert',
    rating: '4,9',
    reviews: 127,
    close: '19:00',
    author: 'M',
    review: '« Pain excellent et accueil au top. Je les ai trouvés en 2 minutes sur Google ! »',
    photos: ['linear-gradient(135deg,#C9A24B 0%,#E8C98A 45%,#8C6A2C 100%)', 'linear-gradient(135deg,#00A896,#028090)', 'linear-gradient(135deg,#F1E3C4,#D9B877)'],
    caller: '06 96 •• •• 21',
    call: [
      { from: 'ia', text: 'Boulangerie du Robert, bonjour ! Comment puis-je vous aider ?' },
      { from: 'client', text: 'Je voudrais commander 30 viennoiseries pour samedi matin.' },
      { from: 'ia', text: 'C’est noté pour samedi. À quel nom et à quelle heure ?' },
      { from: 'client', text: 'Mme Louis, vers 8 h. Merci !' },
    ],
    sms: 'Commande : 30 viennoiseries samedi 8 h — Mme Louis, 06 96 •• •• 21',
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
    caller: '06 96 •• •• 48',
    call: [
      { from: 'ia', text: 'Plomberie Martin, bonjour ! Que puis-je faire pour vous ?' },
      { from: 'client', text: 'J’ai une fuite sous l’évier, ça coule partout !' },
      { from: 'ia', text: 'Coupez l’arrivée d’eau. Je préviens le plombier en urgence.' },
      { from: 'client', text: 'D’accord, je suis au 12 rue des Flamboyants.' },
    ],
    sms: '🔴 URGENT : fuite sous évier — 12 rue des Flamboyants, 06 96 •• •• 48',
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
    caller: '06 96 •• •• 07',
    call: [
      { from: 'ia', text: 'Salon Élégance, bonjour ! Vous souhaitez un rendez-vous ?' },
      { from: 'client', text: 'Oui, une coupe et un brushing demain après-midi.' },
      { from: 'ia', text: 'Je transmets votre demande pour 15 h. À quel nom ?' },
      { from: 'client', text: 'Sarah. Parfait, merci !' },
    ],
    sms: 'RDV demandé : coupe + brushing demain 15 h — Sarah, 06 96 •• •• 07',
  },
]

const ACTIONS: [string, string][] = [
  ['☎', 'Appeler'],
  ['➤', 'Itinéraire'],
  ['◍', 'Site web'],
  ['✉', 'WhatsApp'],
]

const TYPE_MS = 55
const GOOGLE_HOLD_MS = 3800
const LINE_MS = 1300

type Scene = 'google' | 'call'

export function GoogleCard() {
  const [idx, setIdx] = useState(0)
  const [typed, setTyped] = useState(BUSINESSES[0].query.length)
  const [shown, setShown] = useState(true)
  const [animated, setAnimated] = useState(false)
  const [scene, setScene] = useState<Scene>('google')
  // Appel : 0 = sonnerie, 1 = décroché, 2.. = lignes affichées, puis SMS
  const [callStep, setCallStep] = useState(0)
  const [smsShown, setSmsShown] = useState(false)

  useEffect(() => {
    if (!document.documentElement.classList.contains('motion')) return
    setAnimated(true)
    let cancelled = false
    const timers: number[] = []
    const wait = (ms: number) => new Promise<void>((r) => timers.push(window.setTimeout(r, ms)))

    const run = async (i: number) => {
      if (cancelled) return
      const b = BUSINESSES[i]

      // Scène 1 : recherche + fiche Google
      setScene('google')
      setShown(false)
      setIdx(i)
      setTyped(0)
      setCallStep(0)
      setSmsShown(false)
      await wait(i === 0 ? 700 : 450)
      for (let n = 1; n <= b.query.length; n++) {
        if (cancelled) return
        setTyped(n)
        await wait(TYPE_MS)
      }
      await wait(250)
      if (cancelled) return
      setShown(true)
      await wait(GOOGLE_HOLD_MS)
      if (cancelled) return

      // Scène 2 : appel décroché par la Réceptionniste IA
      setScene('call')
      await wait(1400) // sonnerie
      if (cancelled) return
      setCallStep(1) // décroché
      await wait(600)
      for (let l = 0; l < b.call.length; l++) {
        if (cancelled) return
        setCallStep(2 + l)
        await wait(LINE_MS)
      }
      if (cancelled) return
      setSmsShown(true)
      await wait(3000)
      run((i + 1) % BUSINESSES.length)
    }
    run(0)
    return () => {
      cancelled = true
      timers.forEach(clearTimeout)
    }
  }, [])

  const b = BUSINESSES[idx]
  const visibleLines = animated ? Math.max(0, callStep - 1) : b.call.length
  const answered = !animated || callStep >= 1
  const cls = ['gbp', animated ? 'gbp-anim' : '', shown ? 'gbp-on' : ''].join(' ')

  return (
    <div className={`hero-scenes scene-${animated ? scene : 'google'}`} aria-hidden="true">
      {/* Scène 1 — fiche Google */}
      <div className={`scene scene-google-wrap ${cls}`}>
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
                <span key={label} style={{ ['--i' as string]: k }} className={k === 0 && scene === 'google' && shown ? 'act-call-hint' : ''}>
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

      {/* Scène 2 — Réceptionniste IA */}
      <div className="scene scene-call-wrap">
        <div className="rcp" key={`call-${idx}`}>
          <div className="rcp-head">
            <span className={`rcp-avatar ${answered ? 'on' : 'ringing'}`}>☎</span>
            <div className="stack" style={{ gap: 2, minWidth: 0 }}>
              <strong>Réceptionniste IA</strong>
              <span className="rcp-status">
                {answered ? (
                  <>
                    <i className="rcp-live" /> En ligne · {b.caller}
                  </>
                ) : (
                  <>Appel entrant · {b.caller}</>
                )}
              </span>
            </div>
            <span className="rcp-badge">24h/24</span>
          </div>
          {!answered && (
            <div className="rcp-ring">
              <span className="rcp-ring-dot" />
              <p>Vous êtes sur un chantier… la Réceptionniste IA décroche pour vous.</p>
            </div>
          )}
          <div className="rcp-lines">
            {b.call.slice(0, visibleLines).map((l, k) => (
              <div key={k} className={`rcp-line ${l.from}`}>
                {l.from === 'ia' && <span className="rcp-who">IA</span>}
                <p>{l.text}</p>
              </div>
            ))}
            {answered && visibleLines < b.call.length && animated && (
              <div className={`rcp-line ${b.call[visibleLines]?.from} typing`}>
                <p>
                  <i />
                  <i />
                  <i />
                </p>
              </div>
            )}
          </div>
          <div className={`rcp-sms ${!animated || smsShown ? 'on' : ''}`}>
            <span className="rcp-sms-icon">✉</span>
            <div className="stack" style={{ gap: 2, minWidth: 0 }}>
              <strong>SMS envoyé au gérant</strong>
              <span>{b.sms}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
