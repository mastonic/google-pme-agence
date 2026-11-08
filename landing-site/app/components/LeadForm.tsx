'use client'

import { useRef, useState } from 'react'
import { LeadPayload, newRequestId, sendLead } from './leads'
import { PrivacyNotice } from './PrivacyNotice'

type Props = {
  source: LeadPayload['source']
  extra?: Partial<LeadPayload>
  cta: string
  askName?: boolean
  downloadOnSuccess?: string
  successText: React.ReactNode
}

export function LeadForm({ source, extra, cta, askName, downloadOnSuccess, successText }: Props) {
  const [email, setEmail] = useState('')
  const [name, setName] = useState(extra?.business_name || '')
  const [city, setCity] = useState('')
  const [consent, setConsent] = useState(false)
  const [hp, setHp] = useState('')
  const [state, setState] = useState<'idle' | 'sending' | 'done'>('idle')
  const [err, setErr] = useState('')
  const shownAt = useRef(Date.now())
  const requestId = useRef('')

  if (state === 'done') return <div aria-live="polite">{successText}</div>

  return (
    <form
      className="stack"
      style={{ gap: 12 }}
      onSubmit={async (e) => {
        e.preventDefault()
        setErr('')
        setState('sending')
        if (!requestId.current) requestId.current = newRequestId()
        const r = await sendLead({ ...extra, source, email, business_name: name || undefined, city: city || undefined, consent, website: hp,
          request_id: requestId.current, elapsed_ms: Date.now() - shownAt.current })
        if (r.ok) {
          setState('done')
          if (downloadOnSuccess) window.open(downloadOnSuccess, '_blank')
        } else {
          setState('idle')
          setErr(r.error || 'Erreur')
        }
      }}
    >
      {askName && (
        <div className="grid-280" style={{ gap: 12 }}>
          <label className="field">Nom du commerce<input value={name} onChange={(e) => setName(e.target.value)} placeholder="Plomberie Martin" /></label>
          <label className="field">Ville<input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Trappes" /></label>
        </div>
      )}
      <label className="field">Votre email
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="vous@entreprise.fr" autoComplete="email" />
      </label>
      {/* Pot de miel anti-robots : invisible pour les humains */}
      <input tabIndex={-1} autoComplete="off" aria-hidden="true" value={hp} onChange={(e) => setHp(e.target.value)} name="website" style={{ position: 'absolute', left: -9999, width: 1, height: 1 }} />
      <label className="small muted" style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
        <input type="checkbox" required checked={consent} onChange={(e) => setConsent(e.target.checked)} style={{ marginTop: 3 }} />
        J’accepte d’être recontacté par Pulse Locale PME (HoldMasto) au sujet de ma demande.
      </label>
      <PrivacyNotice />
      {err && <p role="alert" style={{ color: '#B45309', fontSize: 14 }}>{err}</p>}
      <button type="submit" className="btn btn-primary btn-sm" disabled={state === 'sending'} style={{ border: 0, cursor: 'pointer' }}>
        {state === 'sending' ? 'Envoi…' : cta}
      </button>
    </form>
  )
}
