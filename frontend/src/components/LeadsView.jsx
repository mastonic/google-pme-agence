import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import {
    Inbox, Phone, Mail, MapPin, RefreshCw, Loader2, X, Clock, ShoppingBag, MessageSquare, AlertTriangle, Save,
} from 'lucide-react';

// Entonnoir des leads entrants (sites .fr / .store / .info) : chaque demande arrive en « À rappeler »
// (ou « Nouveau » sans téléphone). On rappelle, on note, on fait avancer jusqu'à « Gagné » ou « Perdu ».
// API : GET /admin/leads, PATCH /admin/leads/{id} {status, notes, next_call_at}
const STAGES = [
    { id: 'new',        label: 'Nouveaux',      cls: 'border-sky-500/30',     dot: 'bg-sky-400' },
    { id: 'to_call',    label: 'À contacter',   cls: 'border-amber-500/40',   dot: 'bg-amber-400' },
    { id: 'contacted',  label: 'Contactés',     cls: 'border-violet-500/30',  dot: 'bg-violet-400' },
    { id: 'quote_sent', label: 'Devis envoyé',  cls: 'border-cyan-500/30',    dot: 'bg-cyan-400' },
    { id: 'won',        label: 'Convertis',     cls: 'border-emerald-500/30', dot: 'bg-emerald-400' },
    { id: 'lost',       label: 'Clos',          cls: 'border-white/10',       dot: 'bg-slate-500' },
];
const SOURCES = { store: 'Boutique', callback: 'Demande de rappel', score_tool: 'Outil de score', guide_pdf: 'Guide PDF', contact: 'Contact' };

const fmt = (iso, opts = { dateStyle: 'short', timeStyle: 'short' }) => (iso ? new Date(iso).toLocaleString('fr-FR', opts) : '—');
const ago = (iso) => {
    if (!iso) return '';
    const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (m < 60) return `il y a ${Math.max(1, m)} min`;
    if (m < 1440) return `il y a ${Math.round(m / 60)} h`;
    return `il y a ${Math.round(m / 1440)} j`;
};
const toLocalInput = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    const p = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
};

function Row({ icon: Icon, label, children }) {
    if (children === null || children === undefined || children === '') return null;
    return (
        <div className="flex gap-3 py-2 border-b border-white/5 last:border-0 text-sm">
            <span className="text-slate-400 w-36 flex-none flex items-center gap-1.5">{Icon && <Icon className="w-3.5 h-3.5" />}{label}</span>
            <span className="text-slate-100 min-w-0 break-words">{children}</span>
        </div>
    );
}

function LeadDetail({ lead, onClose, onSaved }) {
    const [notes, setNotes] = useState(lead.notes || '');
    const [next, setNext] = useState(toLocalInput(lead.next_call_at));
    const [saving, setSaving] = useState(false);
    const [msg, setMsg] = useState('');

    useEffect(() => { setNotes(lead.notes || ''); setNext(toLocalInput(lead.next_call_at)); setMsg(''); }, [lead.id]); // eslint-disable-line react-hooks/exhaustive-deps

    const save = async (patch) => {
        setSaving(true); setMsg('');
        try {
            const r = await axios.patch(`/admin/leads/${lead.id}`, patch);
            onSaved(r.data); setMsg('Enregistré.');
        } catch (e) {
            setMsg(e.response?.data?.detail || 'Enregistrement impossible.');
        } finally { setSaving(false); }
    };
    const saveNotes = () => save({ notes, next_call_at: next ? new Date(next).toISOString() : '' });
    const tel = (lead.phone || '').replace(/[^\d+]/g, '');
    const who = lead.contact_name || lead.business_name || lead.email || lead.phone || `Lead #${lead.id}`;

    return (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
            <aside className="w-full max-w-xl h-full overflow-y-auto bg-slate-900 border-l border-white/10 p-6 space-y-5">
                <div className="flex items-start justify-between gap-3">
                    <div>
                        <p className="text-xs text-slate-400">{SOURCES[lead.source] || lead.source} · reçu {fmt(lead.created_at)} ({ago(lead.created_at)})</p>
                        <h2 className="text-xl font-bold text-white mt-1">{who}</h2>
                        {lead.contact_name && lead.business_name && <p className="text-sm text-slate-300">{lead.business_name}</p>}
                    </div>
                    <button onClick={onClose} className="p-2 rounded-xl border border-white/10 text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
                </div>

                <div className="flex flex-wrap gap-2">
                    {tel && (
                        <a href={`tel:${tel}`} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl font-bold text-sm">
                            <Phone className="w-4 h-4" /> Appeler {lead.phone}
                        </a>
                    )}
                    {lead.email && (
                        <a href={`mailto:${lead.email}`} className="flex items-center gap-2 border border-white/10 hover:bg-white/5 text-slate-200 px-4 py-2 rounded-xl text-sm">
                            <Mail className="w-4 h-4" /> Email
                        </a>
                    )}
                </div>

                <div>
                    <p className="text-xs uppercase tracking-wider text-slate-400 mb-2">Étape</p>
                    <div className="flex flex-wrap gap-2">
                        {STAGES.map(s => (
                            <button key={s.id} disabled={saving} onClick={() => save({ status: s.id })}
                                className={`text-xs px-3 py-1.5 rounded-lg border flex items-center gap-1.5 ${lead.status === s.id ? 'border-brand bg-brand/20 text-white' : 'border-white/10 text-slate-400 hover:text-white'}`}>
                                <span className={`w-2 h-2 rounded-full ${s.dot}`} />{s.label}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="bg-slate-800/60 border border-white/10 rounded-xl px-4 py-2">
                    <Row icon={ShoppingBag} label="Demande">{lead.product}</Row>
                    <Row icon={Clock} label="Rappel souhaité">{lead.callback_label}</Row>
                    <Row label="Type de demande">{lead.kind_label}{lead.ref ? ` · ${lead.ref}` : ''}</Row>
                    <Row label="Site d'origine">{lead.site}</Row>
                    <Row label="Nom">{lead.contact_name}</Row>
                    <Row label="Commerce">{lead.business_name}</Row>
                    <Row icon={Phone} label="Téléphone">{lead.phone}</Row>
                    <Row icon={Mail} label="Email">{lead.email}</Row>
                    <Row icon={MapPin} label="Ville">{lead.city}</Row>
                    <Row label="Score digital">{lead.score != null ? `${lead.score}/100` : null}</Row>
                    <Row icon={MessageSquare} label="Message"><span className="whitespace-pre-wrap">{lead.message}</span></Row>
                    {lead.answers && Object.keys(lead.answers).length > 0 && (
                        <Row label="Réponses au test">
                            {Object.entries(lead.answers).map(([k, v]) => <span key={k} className="block">{k} : {v}</span>)}
                        </Row>
                    )}
                    <Row label="Page d'origine">{lead.referrer && /^https?:\/\//i.test(lead.referrer) && <a href={lead.referrer} target="_blank" rel="noopener noreferrer" className="text-brand underline break-all">{lead.referrer}</a>}</Row>
                    <Row label="Mis à jour">{lead.updated_at ? fmt(lead.updated_at) : null}</Row>
                </div>

                <div className="space-y-3">
                    <label className="block text-xs uppercase tracking-wider text-slate-400">Prochain rappel
                        <input type="datetime-local" value={next} onChange={e => setNext(e.target.value)}
                            className="mt-1 w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-200" />
                    </label>
                    <label className="block text-xs uppercase tracking-wider text-slate-400">Notes d'appel
                        <textarea rows={6} value={notes} onChange={e => setNotes(e.target.value)} placeholder="Ex. rappelé le 8/11, intéressé par le pack Pro, rappeler mardi"
                            className="mt-1 w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-200 normal-case tracking-normal" />
                    </label>
                    <div className="flex items-center gap-3">
                        <button onClick={saveNotes} disabled={saving}
                            className="flex items-center gap-2 text-sm bg-brand text-white px-4 py-2 rounded-xl font-bold hover:bg-blue-600 disabled:opacity-40">
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Enregistrer
                        </button>
                        {msg && <span className="text-xs text-slate-300">{msg}</span>}
                    </div>
                </div>
            </aside>
        </div>
    );
}

function LeadCard({ lead, onOpen }) {
    const late = lead.next_call_at && new Date(lead.next_call_at) < new Date() && !['won', 'lost'].includes(lead.status);
    return (
        <button onClick={() => onOpen(lead)} className="w-full text-left bg-slate-800 hover:bg-slate-700/80 border border-white/10 rounded-xl p-3 space-y-1.5 transition-colors">
            <div className="flex items-start justify-between gap-2">
                <span className="font-semibold text-white text-sm truncate">{lead.contact_name || lead.business_name || lead.email || lead.phone}</span>
                <span className="text-[10px] text-slate-500 whitespace-nowrap">{ago(lead.created_at)}</span>
            </div>
            {lead.contact_name && lead.business_name && <p className="text-xs text-slate-400 truncate">{lead.business_name}{lead.city ? ` · ${lead.city}` : ''}</p>}
            {lead.product && <p className="text-xs text-brand truncate">{lead.product}</p>}
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-400">
                {lead.phone && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{lead.phone}</span>}
                {lead.callback_label && lead.status === 'to_call' && <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{lead.callback_label}</span>}
                {lead.next_call_at && <span className={`flex items-center gap-1 ${late ? 'text-amber-300' : ''}`}><Clock className="w-3 h-3" />{late ? 'En retard · ' : ''}{fmt(lead.next_call_at)}</span>}
            </div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">{SOURCES[lead.source] || lead.source}</p>
        </button>
    );
}

export default function LeadsView() {
    const [leads, setLeads] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [source, setSource] = useState('all');
    const [q, setQ] = useState('');
    const [open, setOpen] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const r = await axios.get('/admin/leads', { params: { limit: 1000 } });
            setLeads(r.data); setError('');
        } catch (e) {
            setError(e.response?.data?.detail || 'Impossible de charger les leads.');
        } finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t); }, [load]);

    const filtered = useMemo(() => (leads || []).filter(l => {
        if (source !== 'all' && l.source !== source) return false;
        if (!q.trim()) return true;
        const hay = [l.contact_name, l.business_name, l.email, l.phone, l.city, l.product, l.message, l.notes].join(' ').toLowerCase();
        return hay.includes(q.trim().toLowerCase());
    }), [leads, source, q]);

    const onSaved = (lead) => {
        setLeads(prev => prev.map(l => (l.id === lead.id ? lead : l)));
        setOpen(lead);
    };

    const toCall = (leads || []).filter(l => l.status === 'to_call').length;
    const won = (leads || []).filter(l => l.status === 'won').length;
    const total = (leads || []).length;

    return (
        <div className="p-4 md:p-8 space-y-6 h-full overflow-y-auto">
            <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Inbox className="w-6 h-6 text-brand" /> Leads entrants</h1>
                    <p className="text-sm text-slate-400 mt-1">
                        Demandes reçues depuis le site, la boutique et les ressources. Chaque demande avec un téléphone arrive en « À rappeler ».
                    </p>
                </div>
                <div className="flex items-center gap-3 text-sm">
                    <span className="px-3 py-1.5 rounded-xl border border-amber-500/30 text-amber-300 bg-amber-500/10 font-bold">{toCall} à rappeler</span>
                    <span className="px-3 py-1.5 rounded-xl border border-white/10 text-slate-300">{total} au total · {total ? Math.round((won / total) * 100) : 0} % gagnés</span>
                    <button onClick={load} disabled={loading} title="Actualiser" className="p-2 rounded-xl border border-white/10 text-slate-400 hover:text-white">
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            <div className="flex flex-wrap gap-2 items-center">
                <input value={q} onChange={e => setQ(e.target.value)} placeholder="Rechercher (nom, téléphone, ville, demande…)"
                    className="flex-1 min-w-[220px] bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-200" />
                {['all', ...Object.keys(SOURCES)].map(s => (
                    <button key={s} onClick={() => setSource(s)}
                        className={`text-xs px-3 py-1.5 rounded-lg border ${source === s ? 'border-brand bg-brand/20 text-white' : 'border-white/10 text-slate-400 hover:text-white'}`}>
                        {s === 'all' ? 'Toutes les sources' : SOURCES[s]}
                    </button>
                ))}
            </div>

            {error && <div className="flex items-center gap-2 text-sm text-amber-300"><AlertTriangle className="w-4 h-4" /> {error}</div>}
            {!leads && !error && <div className="flex justify-center p-10"><Loader2 className="w-6 h-6 animate-spin text-brand" /></div>}

            {leads && (
                <div className="grid gap-4 grid-cols-1 md:grid-cols-3 xl:grid-cols-5 items-start">
                    {STAGES.map(stage => {
                        const items = filtered.filter(l => l.status === stage.id);
                        return (
                            <section key={stage.id} className={`bg-slate-900/60 border ${stage.cls} rounded-2xl p-3 space-y-2 min-h-[120px]`}>
                                <h2 className="flex items-center justify-between text-sm font-bold text-white px-1">
                                    <span className="flex items-center gap-2"><span className={`w-2 h-2 rounded-full ${stage.dot}`} />{stage.label}</span>
                                    <span className="text-xs text-slate-400">{items.length}</span>
                                </h2>
                                {items.length === 0
                                    ? <p className="text-xs text-slate-600 px-1 py-4 text-center">Aucun lead</p>
                                    : items.map(l => <LeadCard key={l.id} lead={l} onOpen={setOpen} />)}
                            </section>
                        );
                    })}
                </div>
            )}

            {open && <LeadDetail lead={open} onClose={() => setOpen(null)} onSaved={onSaved} />}
        </div>
    );
}
