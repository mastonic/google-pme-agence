// Envoi des leads vers l'API (même domaine via la réécriture Firebase /leads).
// NEXT_PUBLIC_API_BASE permet de viser une autre URL en local.
const API = process.env.NEXT_PUBLIC_API_BASE || ''

// Type de demande : détermine la boîte qui reçoit la notification (contact@, devis@, audit@, support@).
export type LeadKind = 'contact' | 'devis' | 'demo' | 'audit' | 'support' | 'product_info' | 'guide'

export type LeadPayload = {
  source: 'score_tool' | 'guide_pdf' | 'store' | 'contact' | 'callback'
  kind?: LeadKind
  request_id?: string   // identifiant de soumission : un double clic ne crée qu'une demande
  elapsed_ms?: number   // temps de remplissage (anti-robot)
  email?: string
  contact_name?: string
  business_name?: string
  phone?: string
  city?: string
  product?: string
  message?: string
  callback_slot?: string
  score?: number
  answers?: Record<string, number>
  consent: boolean
  website?: string
}

export function newRequestId(): string {
  try {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID().replace(/-/g, '')
  } catch { /* navigateur ancien */ }
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 12)
}

export async function sendLead(p: LeadPayload): Promise<{ ok: boolean; error?: string; ref?: string }> {
  try {
    const r = await fetch(`${API}/leads`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p) })
    if (r.ok) {
      const d = await r.json().catch(() => null)
      return { ok: true, ref: d?.ref }
    }
    if (r.status === 429) return { ok: false, error: 'Trop de demandes, réessayez dans quelques minutes.' }
    if (r.status === 422) {
      // Ne blâmer la saisie que si le serveur pointe vraiment l'email ou le téléphone.
      const d = await r.json().catch(() => null)
      const fields = Array.isArray(d?.detail) ? d.detail.map((e: { loc?: string[] }) => (e.loc || []).join('.')).join(' ') : ''
      if (/email/.test(fields)) return { ok: false, error: 'Vérifiez votre adresse email.' }
      if (/phone/.test(fields)) return { ok: false, error: 'Vérifiez votre numéro de téléphone.' }
      return { ok: false, error: 'Envoi impossible pour le moment. Réessayez dans quelques minutes.' }
    }
    return { ok: false, error: 'Envoi impossible pour le moment. Réessayez plus tard.' }
  } catch {
    return { ok: false, error: 'Connexion impossible. Vérifiez votre réseau.' }
  }
}
