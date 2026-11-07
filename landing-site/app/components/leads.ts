// Envoi des leads vers l'API (même domaine via la réécriture Firebase /leads).
// NEXT_PUBLIC_API_BASE permet de viser une autre URL en local.
const API = process.env.NEXT_PUBLIC_API_BASE || ''

export type LeadPayload = {
  source: 'score_tool' | 'guide_pdf' | 'store' | 'contact'
  email: string
  business_name?: string
  phone?: string
  city?: string
  score?: number
  answers?: Record<string, number>
  consent: boolean
  website?: string
}

export async function sendLead(p: LeadPayload): Promise<{ ok: boolean; error?: string }> {
  try {
    const r = await fetch(`${API}/leads`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p) })
    if (r.ok) return { ok: true }
    if (r.status === 429) return { ok: false, error: 'Trop de demandes, réessayez dans quelques minutes.' }
    if (r.status === 422) return { ok: false, error: 'Vérifiez votre adresse email.' }
    return { ok: false, error: 'Envoi impossible pour le moment. Réessayez plus tard.' }
  } catch {
    return { ok: false, error: 'Connexion impossible. Vérifiez votre réseau.' }
  }
}
