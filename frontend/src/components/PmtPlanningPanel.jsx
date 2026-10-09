import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import {
    CalendarDays, ChevronLeft, ChevronRight, Plus, Send, Lock, X, Save, AlertTriangle, Truck, Trash2, Ban, FileText
} from 'lucide-react';

// Planning (gérant) : courses du jour, publication aux équipiers, suivi des
// validations départ / arrivée / retour, clôture de la journée.

const STATUS_CLS = {
    planifiee: 'bg-slate-700/60 text-slate-300 border-white/10',
    acceptee: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
    en_cours: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    arrivee: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
    terminee: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    annulee: 'bg-rose-500/10 text-rose-300/70 border-rose-500/20 line-through',
};
const DAY_CLS = {
    brouillon: 'bg-slate-700/60 text-slate-300',
    publie: 'bg-sky-500/15 text-sky-300',
    valide: 'bg-emerald-500/15 text-emerald-300',
};
const TRAJETS = [['aller', 'Aller'], ['retour', 'Retour'], ['aller_retour', 'Aller-retour']];

// Date locale du téléphone / du poste (toISOString donnerait la date UTC, fausse après minuit en été).
const isoLocal = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const todayIso = () => isoLocal(new Date());
const shift = (iso, days) => {
    const d = new Date(`${iso}T12:00:00`);
    d.setDate(d.getDate() + days);
    return isoLocal(d);
};
const frLong = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });

function MissionDrawer({ mission, date, businessId, employees, onClose, onSaved }) {
    const [form, setForm] = useState(() => ({
        heure_prevue: '08:00', duree_min: 60, patient_nom: '', adresse_depart: '', adresse_arrivee: '',
        type_trajet: 'aller', mode: 'ambulance', vehicule: '', equipage_ids: [], notes: '', ...(mission || {}),
    }));
    const [error, setError] = useState('');
    const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
    const field = 'mt-1 w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white';

    const save = async () => {
        setError('');
        try {
            const body = { ...form, date: mission?.date || date, business_id: businessId || undefined };
            if (mission?.id) await axios.put(`/pmt/planning/missions/${mission.id}`, body);
            else await axios.post('/pmt/planning/missions', body);
            onSaved();
        } catch (e) { setError(e?.response?.data?.detail || e.message); }
    };

    const input = (k, label, type = 'text') => (
        <label className="block text-xs text-slate-400">{label}
            <input type={type} value={form[k] ?? ''} onChange={e => set(k, type === 'number' ? Number(e.target.value) : e.target.value)} className={field} />
        </label>
    );

    return createPortal(
        <div className="fixed inset-0 z-[5000] flex">
            <div className="flex-1 bg-black/60 backdrop-blur-sm" onClick={onClose} />
            <div className="w-full md:w-[520px] h-full bg-slate-950 border-l border-white/10 overflow-y-auto">
                <div className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur border-b border-white/10 p-5 flex items-center justify-between">
                    <h3 className="font-bold text-lg">{mission?.id ? 'Modifier la course' : 'Nouvelle course'} · {frLong(mission?.date || date)}</h3>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-white/10"><X className="w-5 h-5" /></button>
                </div>
                <div className="p-5 space-y-4">
                    {error && <div className="rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-200 text-sm px-4 py-3">{error}</div>}
                    <div className="grid grid-cols-2 gap-3">
                        {input('heure_prevue', 'Heure de prise en charge', 'time')}
                        {input('duree_min', 'Durée prévue (min)', 'number')}
                    </div>
                    {input('patient_nom', 'Patient')}
                    {input('adresse_depart', 'Départ')}
                    {input('adresse_arrivee', 'Arrivée')}
                    <div className="grid grid-cols-2 gap-3">
                        <label className="block text-xs text-slate-400">Trajet
                            <select value={form.type_trajet} onChange={e => set('type_trajet', e.target.value)} className={field}>
                                {TRAJETS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                            </select>
                        </label>
                        <label className="block text-xs text-slate-400">Véhicule
                            <select value={form.mode} onChange={e => set('mode', e.target.value)} className={field}>
                                <option value="ambulance">Ambulance</option>
                                <option value="tap">VSL</option>
                            </select>
                        </label>
                    </div>
                    {input('vehicule', 'Immatriculation / n° du véhicule')}
                    <div className="grid grid-cols-2 gap-3">
                        {[0, 1].map(i => (
                            <label key={i} className="block text-xs text-slate-400">{i === 0 ? 'Équipier 1' : 'Équipier 2'}
                                <select value={form.equipage_ids[i] || ''}
                                    onChange={e => { const n = [...form.equipage_ids]; n[i] = e.target.value; set('equipage_ids', n.filter(Boolean)); }}
                                    className={field}>
                                    <option value="">—</option>
                                    {employees.map(emp => (
                                        <option key={emp.id} value={emp.id}>
                                            {emp.prenom} {emp.nom} · {emp.qualification}{emp.conformite?.status === 'non_conforme' ? ' ⚠' : ''}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        ))}
                    </div>
                    <label className="block text-xs text-slate-400">Consignes
                        <textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={2} className={field} />
                    </label>
                    <p className="text-[11px] text-slate-500">Pas d’information médicale ici : le motif reste sur la prescription.</p>
                    <div className="flex justify-end">
                        <button onClick={save} className="px-4 py-2 rounded-xl bg-brand text-white text-sm font-semibold flex items-center gap-1">
                            <Save className="w-4 h-4" /> Enregistrer
                        </button>
                    </div>
                </div>
            </div>
        </div>,
        document.body,
    );
}

function PmtPlanningPanel({ businesses = [], user, onOpenVoucher }) {
    const isAdmin = user?.role === 'admin';
    const [businessId, setBusinessId] = useState('');
    const [date, setDate] = useState(todayIso);
    const [day, setDay] = useState(null);
    const [employees, setEmployees] = useState([]);
    const [editing, setEditing] = useState(null);
    const [message, setMessage] = useState('');

    const params = () => ({ date, ...(businessId ? { business_id: businessId } : {}) });
    const refresh = async () => {
        if (isAdmin && !businessId) { setDay(null); return; }
        const [d, e] = await Promise.all([
            axios.get('/pmt/planning/jour', { params: params() }),
            axios.get('/pmt/equipe', { params: businessId ? { business_id: businessId } : {} }),
        ]);
        setDay(d.data);
        setEmployees(e.data.filter(x => x.actif));
    };
    useEffect(() => { setMessage(''); refresh().catch(e => setMessage(e?.response?.data?.detail || e.message)); }, [date, businessId]);

    const call = async (fn, ok) => {
        setMessage('');
        try { await fn(); if (ok) setMessage(ok); await refresh(); } catch (e) { setMessage(e?.response?.data?.detail || e.message); }
    };
    const publish = () => call(() => axios.post('/pmt/planning/jour/publier', { date, business_id: businessId || undefined }),
        'Planning publié : les équipiers voient leurs missions.');
    const validate = () => call(async () => {
        try {
            await axios.post('/pmt/planning/jour/valider', { date, business_id: businessId || undefined });
        } catch (e) {
            if (e?.response?.status === 409 && window.confirm(`${e.response.data.detail}.\nValider quand même la journée ?`)) {
                await axios.post('/pmt/planning/jour/valider', { date, business_id: businessId || undefined, forcer: true });
            } else throw e;
        }
    }, 'Journée validée.');
    const cancel = (m) => window.confirm('Annuler cette course ?') &&
        call(() => axios.post(`/pmt/planning/missions/${m.id}/action`, { action: 'annuler' }));
    const remove = (m) => window.confirm('Supprimer cette course ?') && call(() => axios.delete(`/pmt/planning/missions/${m.id}`));

    const locked = day?.status === 'valide';
    const time = (m, action) => (m.events || []).filter(e => e.action === action).pop()?.at?.slice(11, 16);

    return (
        <div className="w-full h-full overflow-y-auto p-4 md:p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-11 h-11 rounded-2xl bg-brand/15 border border-brand/30 flex items-center justify-center">
                            <CalendarDays className="w-6 h-6 text-brand" />
                        </div>
                        <div>
                            <h2 className="text-3xl font-extrabold">Planning</h2>
                            <p className="text-slate-400 text-sm">Courses du jour, validations de l’équipage, clôture.</p>
                        </div>
                    </div>
                    {isAdmin && (
                        <select value={businessId} onChange={e => setBusinessId(e.target.value)}
                            className="bg-slate-800 border border-white/10 rounded-xl px-3 py-3 text-sm min-w-[220px]">
                            <option value="">Choisir un client…</option>
                            {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                        </select>
                    )}
                </div>

                <div className="glass rounded-2xl border border-white/10 p-4 mb-4 flex flex-wrap items-center gap-3">
                    <button onClick={() => setDate(shift(date, -1))} className="p-2 rounded-xl hover:bg-white/10"><ChevronLeft className="w-5 h-5" /></button>
                    <input type="date" value={date} onChange={e => e.target.value && setDate(e.target.value)}
                        className="bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm" />
                    <button onClick={() => setDate(shift(date, 1))} className="p-2 rounded-xl hover:bg-white/10"><ChevronRight className="w-5 h-5" /></button>
                    <span className="font-semibold capitalize">{frLong(date)}</span>
                    {day && <span className={`text-xs px-2 py-1 rounded-full ${DAY_CLS[day.status]}`}>{day.status_label}</span>}
                    <div className="flex-1" />
                    {day && !locked && (
                        <>
                            <button onClick={() => setEditing({})} className="px-3 py-2 rounded-xl bg-slate-800 border border-white/10 text-sm flex items-center gap-1">
                                <Plus className="w-4 h-4" /> Course
                            </button>
                            <button onClick={publish} className="px-3 py-2 rounded-xl bg-sky-600 text-white text-sm font-semibold flex items-center gap-1">
                                <Send className="w-4 h-4" /> {day.status === 'publie' ? 'Republier' : 'Publier'}
                            </button>
                            <button onClick={validate} className="px-3 py-2 rounded-xl bg-emerald-600 text-white text-sm font-semibold flex items-center gap-1">
                                <Lock className="w-4 h-4" /> Valider la journée
                            </button>
                        </>
                    )}
                    {locked && <span className="text-xs text-emerald-300">Validée par {day.validated_by}</span>}
                </div>

                {day && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
                        {[['Courses', day.resume.total, 'text-white'],
                          ['En route', day.resume.par_statut.en_cours + day.resume.par_statut.arrivee, 'text-amber-300'],
                          ['Terminées', day.resume.par_statut.terminee, 'text-emerald-300'],
                          ['Non terminées', day.resume.non_terminees, 'text-slate-300'],
                          ['En retard au départ', day.resume.en_retard.length, 'text-rose-300']].map(([l, v, tone]) => (
                            <div key={l} className="glass rounded-2xl border border-white/10 p-3">
                                <p className={`text-xl font-extrabold ${tone}`}>{v}</p>
                                <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mt-1">{l}</p>
                            </div>
                        ))}
                    </div>
                )}
                {message && <div className="mb-4 rounded-xl bg-slate-800 border border-white/10 text-sm px-4 py-3">{message}</div>}
                {isAdmin && !businessId && <p className="text-sm text-slate-500">Choisis un client pour voir son planning.</p>}

                <div className="space-y-3">
                    {day && day.missions.length === 0 && (
                        <div className="glass rounded-2xl border border-white/10 p-8 text-center text-sm text-slate-500">Aucune course planifiée ce jour.</div>
                    )}
                    {day?.missions.map(m => (
                        <div key={m.id} className="glass rounded-2xl border border-white/10 p-4">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                                <div className="min-w-0">
                                    <p className="font-semibold">
                                        <span className="text-xl font-extrabold mr-2">{m.heure_prevue}</span>
                                        {m.patient_nom || 'Patient ?'}
                                        <span className="text-slate-400 font-normal text-sm"> · {m.adresse_depart || '?'} → {m.adresse_arrivee || '?'}</span>
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                                        <Truck className="w-3 h-3" /> {m.mode === 'tap' ? 'VSL' : 'Ambulance'} {m.vehicule || '—'}
                                        {' · '}{m.equipage_noms.join(' + ') || 'équipage non affecté'}
                                        {' · '}{TRAJETS.find(t => t[0] === m.type_trajet)?.[1]}
                                    </p>
                                    <p className="text-xs text-slate-500 mt-1">
                                        {time(m, 'accepter') && `Acceptée ${time(m, 'accepter')} · `}
                                        {time(m, 'depart') && `Départ ${time(m, 'depart')} · `}
                                        {time(m, 'arrivee') && `Déposé ${time(m, 'arrivee')} · `}
                                        {time(m, 'retour') && `Retour ${time(m, 'retour')}`}
                                        {m.km_compteur != null && ` · ${m.km_compteur} km au compteur`}
                                    </p>
                                    {m.problemes?.length > 0 && m.status !== 'annulee' && (
                                        <p className="text-xs text-amber-300 mt-1"><AlertTriangle className="w-3 h-3 inline mr-1" />{m.problemes.join(' · ')}</p>
                                    )}
                                    {m.notes && <p className="text-xs text-slate-400 mt-1 italic">{m.notes}</p>}
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`text-xs px-2 py-1 rounded-full border ${STATUS_CLS[m.status]}`}>{m.status_label}</span>
                                    {m.voucher_id && onOpenVoucher && (
                                        <button onClick={() => onOpenVoucher(m.voucher_id)} title="Dossier de facturation"
                                            className="p-1.5 rounded-lg hover:bg-white/10 text-sky-300"><FileText className="w-4 h-4" /></button>
                                    )}
                                    {!locked && ['planifiee', 'acceptee'].includes(m.status) && (
                                        <button onClick={() => setEditing(m)} className="text-xs px-2 py-1 rounded-lg bg-slate-800 border border-white/10">Modifier</button>
                                    )}
                                    {!locked && !['terminee', 'annulee'].includes(m.status) && (
                                        <button onClick={() => cancel(m)} title="Annuler" className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400"><Ban className="w-4 h-4" /></button>
                                    )}
                                    {!locked && ['planifiee', 'acceptee', 'annulee'].includes(m.status) && (
                                        <button onClick={() => remove(m)} title="Supprimer" className="p-1.5 rounded-lg hover:bg-white/10 text-rose-300"><Trash2 className="w-4 h-4" /></button>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            {editing && (
                <MissionDrawer mission={editing.id ? editing : null} date={date} businessId={businessId} employees={employees}
                    onClose={() => setEditing(null)} onSaved={async () => { setEditing(null); await refresh(); }} />
            )}
        </div>
    );
}

export default PmtPlanningPanel;
