'use client'

import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { LeadPayload, sendLead } from './leads'

// Bouton de commande / demande de rappel : ouvre un formulaire court. La demande arrive dans
// l'entonnoir « Leads » du cockpit (colonne « À rappeler ») et l'équipe est prévenue par email.

type Props = {
  product: string
  children: React.ReactNode
  className?: string
  style?: React.CSSProperties
  source?: LeadPayload['source']
  title?: string
  intro?: string
  // Email toujours obligatoire ; téléphone obligatoire pour un rappel, facultatif pour une simple question.
  phoneRequired?: boolean
  submitLabel?: string
}

const SLOTS: [string, string][] = [
  ['asap', 'Dès que possible'],
  ['morning', 'Le matin'],
  ['noon', 'Le midi'],
  ['afternoon', "L'après-midi"],
  ['evening', 'En fin de journée'],
]
const PHONE = /^(?:\+33\s?|0)[1-9](?:[\s.-]?\d{2}){4}$|^\+\d{9,15}$/

const S: Record<string, React.CSSProperties> = {
  overlay: { position: 'fixed', inset: 0, background: 'rgba(15,23,42,.55)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 },
  panel: { background: '#fff', color: '#1E293B', borderRadius: 20, width: '100%', maxWidth: 520, maxHeight: '92vh', overflowY: 'auto', padding: 28, boxShadow: '0 30px 80px -20px rgba(15,23,42,.45)', textAlign: 'left' },
  head: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 6 },
  title: { fontSize: 22, fontWeight: 700, margin: 0, lineHeight: 1.25 },
  close: { border: 0, background: '#F1F5F9', borderRadius: 999, width: 36, height: 36, fontSize: 18, cursor: 'pointer', flex: 'none' },
  product: { display: 'inline-block', background: '#E6F6F4', color: '#027A6E', borderRadius: 999, padding: '4px 12px', fontSize: 13, fontWeight: 600, margin: '6px 0 14px' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 12 },
  label: { display: 'flex', flexDirection: 'column', gap: 6, fontSize: 14, fontWeight: 600 },
  input: { font: 'inherit', fontWeight: 400, fontSize: 15, border: '1px solid #CBD5E1', borderRadius: 12, padding: '11px 12px', background: '#F8FAFC', color: '#1E293B', width: '100%' },
  consent: { display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 13, color: '#64748B', fontWeight: 400 },
  submit: { border: 0, cursor: 'pointer', width: '100%', background: '#00A896', color: '#fff', borderRadius: 999, padding: '15px 20px', fontSize: 16, fontWeight: 700 },
  err: { color: '#B45309', fontSize: 14, margin: 0 },
}

export function OrderButton({ product, children, className, style, source = 'store', title, intro, phoneRequired = true, submitLabel }: Props) {
  const [open, setOpen] = useState(false)
  const [f, setF] = useState({ contact_name: '', business_name: '', phone: '', email: '', city: '', callback_slot: 'asap', message: '' })
  const [consent, setConsent] = useState(false)
  const [hp, setHp] = useState('')
  const [state, setState] = useState<'idle' | 'sending' | 'done'>('idle')
  const [err, setErr] = useState('')
  const first = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!open) return
    first.current?.focus()
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.removeEventListener('keydown', onKey); document.body.style.overflow = prev }
  }, [open])

  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setF((p) => ({ ...p, [k]: e.target.value }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErr('')
    const phone = f.phone.trim(), email = f.email.trim()
    if (phoneRequired && !PHONE.test(phone)) { setErr('Indiquez un numéro de téléphone valide (ex. 06 12 34 56 78).'); return }
    if (!email) { setErr('Indiquez votre adresse email.'); return }
    if (phone && !PHONE.test(phone)) { setErr('Numéro de téléphone invalide (ex. 06 12 34 56 78).'); return }
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setErr('Adresse email invalide.'); return }
    setState('sending')
    const r = await sendLead({
      source, product, consent, website: hp,
      contact_name: f.contact_name || undefined, business_name: f.business_name || undefined,
      phone: f.phone || undefined, email: f.email, city: f.city || undefined,
      callback_slot: f.callback_slot, message: f.message || undefined,
    })
    if (r.ok) setState('done')
    else { setState('idle'); setErr(r.error || 'Envoi impossible pour le moment.') }
  }

  return (
    <>
      <button type="button" className={className} style={{ cursor: 'pointer', border: 0, fontFamily: 'inherit', lineHeight: 'inherit', ...style }} onClick={() => setOpen(true)}>
        {children}
      </button>
      {open && typeof document !== 'undefined' && createPortal(
        <div style={S.overlay} onMouseDown={(e) => { if (e.target === e.currentTarget) setOpen(false) }}>
          <div style={S.panel} role="dialog" aria-modal="true" aria-labelledby="order-title">
            <div style={S.head}>
              <h2 id="order-title" style={S.title}>{state === 'done' ? 'Merci, c’est noté !' : title || 'On vous rappelle'}</h2>
              <button type="button" style={S.close} aria-label="Fermer" onClick={() => setOpen(false)}>×</button>
            </div>
            {state === 'done' ? (
              <div aria-live="polite" style={{ display: 'grid', gap: 14 }}>
                <p style={{ margin: 0, color: '#475569' }}>
                  Votre demande <strong>« {product} »</strong> est bien arrivée. Un conseiller Pulse Locale PME vous rappelle
                  {f.callback_slot !== 'asap' ? ` ${SLOTS.find(([k]) => k === f.callback_slot)?.[1].toLowerCase()}` : ' très vite'}
                  , en général sous 24 h ouvrées, pour tout caler avec vous. Aucun paiement n’est demandé à cette étape.
                </p>
                <button type="button" style={S.submit} onClick={() => setOpen(false)}>Fermer</button>
              </div>
            ) : (
              <form onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
                <span style={S.product}>{product}</span>
                <p style={{ margin: 0, color: '#475569', fontSize: 15 }}>
                  {intro || 'Laissez vos coordonnées : on vous rappelle pour valider votre besoin. Aucun paiement à cette étape.'}
                </p>
                <div style={S.grid}>
                  <label style={S.label}>Votre nom
                    <input ref={first} style={S.input} value={f.contact_name} onChange={set('contact_name')} placeholder="Paul Martin" autoComplete="name" maxLength={120} />
                  </label>
                  <label style={S.label}>Nom du commerce
                    <input style={S.input} value={f.business_name} onChange={set('business_name')} placeholder="Plomberie Martin" autoComplete="organization" maxLength={200} />
                  </label>
                  <label style={S.label}>{phoneRequired ? 'Téléphone *' : 'Téléphone'}
                    <input style={S.input} type="tel" inputMode="tel" required={phoneRequired} value={f.phone} onChange={set('phone')} placeholder="06 12 34 56 78" autoComplete="tel" maxLength={40} />
                  </label>
                  <label style={S.label}>Ville
                    <input style={S.input} value={f.city} onChange={set('city')} placeholder="Trappes" autoComplete="address-level2" maxLength={120} />
                  </label>
                  <label style={S.label}>Email *
                    <input style={S.input} type="email" required value={f.email} onChange={set('email')} placeholder="vous@entreprise.fr" autoComplete="email" maxLength={200} />
                  </label>
                  <label style={S.label}>Quand vous rappeler ?
                    <select style={S.input} value={f.callback_slot} onChange={set('callback_slot')}>
                      {SLOTS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                    </select>
                  </label>
                </div>
                <label style={S.label}>{phoneRequired ? 'Un mot sur votre besoin (facultatif)' : 'Votre question'}
                  <textarea style={{ ...S.input, minHeight: 80, resize: 'vertical' }} value={f.message} onChange={set('message')} maxLength={1500} placeholder="Ex. je veux plus d’appels sur Trappes et Plaisir" />
                </label>
                <input tabIndex={-1} autoComplete="off" aria-hidden="true" value={hp} onChange={(e) => setHp(e.target.value)} name="website" style={{ position: 'absolute', left: -9999, width: 1, height: 1 }} />
                <label style={S.consent}>
                  <input type="checkbox" required checked={consent} onChange={(e) => setConsent(e.target.checked)} style={{ marginTop: 3 }} />
                  <span>J’accepte d’être recontacté par Pulse Locale PME (HoldMasto) au sujet de ma demande.{' '}
                    <a href="/mentions-legales/#rgpd" style={{ textDecoration: 'underline' }}>Confidentialité</a></span>
                </label>
                {err && <p role="alert" style={S.err}>{err}</p>}
                <button type="submit" style={S.submit} disabled={state === 'sending'}>
                  {state === 'sending' ? 'Envoi…' : submitLabel || 'Être rappelé →'}
                </button>
              </form>
            )}
          </div>
        </div>,
        document.body,
      )}
    </>
  )
}
