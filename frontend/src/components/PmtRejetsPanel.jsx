import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import {
    FileWarning, Upload, Loader2, RotateCcw, Euro, CheckCircle2, Clock3, Target, ShieldAlert, Trash2
} from 'lucide-react';

// Rejets CPAM : import des retours (fichier concentrateur, export tableur ou
// relevé PDF), explication du motif, action corrective, suivi jusqu'au paiement.

const STATUS_STYLES = {
    a_traiter: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    en_correction: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    renvoye: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
    recupere: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    abandonne: 'bg-slate-700/50 text-slate-400 border-white/10',
};

const DIAG_STYLES = {
    signale_avant_envoi: 'text-amber-300',
    non_detecte: 'text-rose-300',
    non_detectable: 'text-slate-400',
    inconnu: 'text-slate-500',
};

const euros = (n) => (n || 0).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' });
const frDate = (iso) => (iso && /^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso.split('-').reverse().join('/') : iso || '—');

function Kpi({ icon: Icon, label, value, hint, tone }) {
    return (
        <div className="glass rounded-2xl border border-white/10 p-4">
            <div className="flex items-start justify-between gap-2">
                <p className={`text-2xl font-extrabold ${tone}`}>{value}</p>
                <Icon className={`w-5 h-5 ${tone}`} />
            </div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mt-1">{label}</p>
            {hint && <p className="text-[11px] text-slate-600 mt-1">{hint}</p>}
        </div>
    );
}

function RejetCard({ r, statuts, onChange, onReopen, onDelete }) {
    const [note, setNote] = useState(r.note || '');
    return (
        <div className="glass rounded-2xl border border-white/10 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                    <p className="font-semibold">{r.nom_patient || 'Patient non indiqué'}
                        <span className="text-slate-500 font-normal text-sm"> · transport {frDate(r.date_soins)}
                            {r.numero_facture && ` · facture ${r.numero_facture}`}</span>
                    </p>
                    <p className="text-sm mt-1">
                        <span className="font-semibold text-white">{r.motif_label}</span>
                        {r.part && <span className="text-slate-500"> · {r.part === 'rc' ? 'mutuelle' : r.part === 'ro' ? 'CPAM' : 'CPAM + mutuelle'}</span>}
                    </p>
                    {(r.code_rejet || r.libelle_rejet) && (
                        <p className="text-xs text-slate-400 mt-1">Libellé caisse : {[r.code_rejet, r.libelle_rejet].filter(Boolean).join(' — ')}</p>
                    )}
                </div>
                <div className="text-right">
                    <p className="text-lg font-extrabold text-white">{euros(r.montant_en_jeu)}</p>
                    <select value={r.status} onChange={e => onChange(r.id, { status: e.target.value })}
                        className={`mt-1 text-xs rounded-full border px-2 py-1 bg-transparent ${STATUS_STYLES[r.status]}`}>
                        {Object.entries(statuts).map(([k, l]) => <option key={k} value={k} className="bg-slate-900">{l}</option>)}
                    </select>
                </div>
            </div>
            {r.action && (
                <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="rounded-xl bg-slate-800/60 p-3">
                        <p className="text-slate-500 font-bold uppercase tracking-wider text-[10px] mb-1">Cause probable</p>
                        <p className="text-slate-300">{r.cause}</p>
                    </div>
                    <div className="rounded-xl bg-slate-800/60 p-3">
                        <p className="text-slate-500 font-bold uppercase tracking-wider text-[10px] mb-1">
                            Que faire {r.recuperable === false && <span className="text-rose-300 normal-case">· difficilement récupérable</span>}
                        </p>
                        <p className="text-slate-300">{r.action}</p>
                    </div>
                </div>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
                <span className={DIAG_STYLES[r.diagnostic] || 'text-slate-500'}>{r.diagnostic_label}</span>
                {r.voucher_id ? (
                    <button onClick={() => onReopen(r.id)} className="flex items-center gap-1 text-sky-300 hover:text-sky-200">
                        <RotateCcw className="w-3 h-3" /> Rouvrir le dossier pour correction
                    </button>
                ) : <span className="text-slate-500">Aucun dossier rattaché</span>}
                <input value={note} onChange={e => setNote(e.target.value)} onBlur={() => note !== (r.note || '') && onChange(r.id, { note })}
                    placeholder="Note (appel caisse, pièce renvoyée…)"
                    className="flex-1 min-w-[180px] bg-slate-800 border border-white/10 rounded-lg px-2 py-1" />
                <button onClick={() => onDelete(r.id)} title="Supprimer" className="text-slate-500 hover:text-rose-300"><Trash2 className="w-4 h-4" /></button>
            </div>
        </div>
    );
}

function PmtRejetsPanel({ businesses = [], user }) {
    const isAdmin = user?.role === 'admin';
    const [businessId, setBusinessId] = useState('');
    const [rows, setRows] = useState([]);
    const [stats, setStats] = useState(null);
    const [catalogue, setCatalogue] = useState({ statuts: {} });
    const [filter, setFilter] = useState('ouverts');
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState(null);
    const input = useRef(null);

    const params = () => ({ ...(businessId ? { business_id: businessId } : {}) });

    const refresh = async () => {
        const [r, s] = await Promise.all([
            axios.get('/pmt/rejets', { params: { ...params(), ...(filter ? { status: filter } : {}) } }),
            axios.get('/pmt/rejets/stats', { params: params() }),
        ]);
        setRows(r.data);
        setStats(s.data);
    };

    useEffect(() => { axios.get('/pmt/rejets/catalogue').then(r => setCatalogue(r.data)).catch(() => {}); }, []);
    useEffect(() => { refresh().catch(e => setMessage({ error: e?.response?.data?.detail || e.message })); }, [businessId, filter]);

    const upload = async (file) => {
        if (!file) return;
        if (isAdmin && !businessId) {
            setMessage({ error: 'Choisis d’abord le client ambulancier concerné par ce retour.' });
            return;
        }
        setBusy(true); setMessage(null);
        const form = new FormData();
        form.append('file', file);
        if (businessId) form.append('business_id', businessId);
        try {
            const r = await axios.post('/pmt/rejets/import', form, { timeout: 180000 });
            setMessage({ ok: r.data });
            await refresh();
        } catch (e) {
            setMessage({ error: e?.response?.data?.detail || e.message });
        } finally {
            setBusy(false);
            if (input.current) input.current.value = '';
        }
    };

    const change = async (id, patch) => {
        await axios.patch(`/pmt/rejets/${id}`, patch);
        await refresh();
    };
    const reopen = async (id) => {
        await axios.post(`/pmt/rejets/${id}/reopen`);
        setMessage({ info: 'Dossier rouvert : corrige-le dans l’onglet Dossiers, il repartira au prochain export.' });
        await refresh();
    };
    const remove = async (id) => {
        if (!window.confirm('Supprimer cette ligne de retour ?')) return;
        await axios.delete(`/pmt/rejets/${id}`);
        await refresh();
    };

    return (
        <div className="w-full h-full overflow-y-auto p-4 md:p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-11 h-11 rounded-2xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center">
                            <FileWarning className="w-6 h-6 text-rose-300" />
                        </div>
                        <div>
                            <h2 className="text-3xl font-extrabold">Rejets CPAM</h2>
                            <p className="text-slate-400 text-sm">Chaque rejet expliqué, rattaché à son dossier et suivi jusqu’au paiement.</p>
                        </div>
                    </div>
                    {isAdmin && (
                        <div className="min-w-[260px]">
                            <label className="text-xs text-slate-400 font-bold uppercase tracking-wider">Client ambulancier</label>
                            <select value={businessId} onChange={e => setBusinessId(e.target.value)}
                                className="mt-2 w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-3 text-sm">
                                <option value="">Tous les clients</option>
                                {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                            </select>
                        </div>
                    )}
                </div>

                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
                        <Kpi icon={Euro} label="Argent en attente" value={euros(stats.montant_en_jeu)} hint={`${stats.ouverts} rejet(s) ouvert(s)`} tone="text-rose-300" />
                        <Kpi icon={CheckCircle2} label="Récupéré" value={euros(stats.montant_recupere)} hint={`${stats.taux_recuperation} % des rejets`} tone="text-emerald-300" />
                        <Kpi icon={Clock3} label="Ouverts > 30 jours" value={stats.ouverts_plus_30_jours} hint="à relancer en priorité" tone="text-amber-300" />
                        <Kpi icon={FileWarning} label="Rejets reçus" value={stats.rejets} hint="depuis le début du suivi" tone="text-white" />
                        <Kpi icon={Target} label="Signalés avant envoi" value={stats.evitables_detectes == null ? '—' : `${stats.evitables_detectes} %`}
                            hint="des rejets évitables" tone="text-sky-300" />
                    </div>
                )}

                {stats?.par_motif?.length > 0 && (
                    <div className="glass rounded-2xl border border-white/10 p-4 mb-6">
                        <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-3">Rejets par motif</p>
                        <div className="space-y-2">
                            {stats.par_motif.map(m => {
                                const max = stats.par_motif[0].nombre || 1;
                                const label = (catalogue.motifs || []).find(c => c.categorie === m.categorie)?.label || m.categorie;
                                return (
                                    <div key={m.categorie} className="grid grid-cols-[minmax(0,220px)_1fr_auto] items-center gap-3 text-xs">
                                        <span className="truncate text-slate-300">{label}</span>
                                        <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                                            <div className="h-full bg-rose-400/70 rounded-full" style={{ width: `${(100 * m.nombre) / max}%` }} />
                                        </div>
                                        <span className="text-slate-400 tabular-nums">{m.nombre} · {euros(m.montant)}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                <div className="glass rounded-2xl border-2 border-dashed border-white/15 p-5 mb-4"
                    onDragOver={e => e.preventDefault()}
                    onDrop={e => { e.preventDefault(); upload(e.dataTransfer.files?.[0]); }}>
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                        <div className="flex-1">
                            <p className="font-semibold text-sm">Importer un retour CPAM</p>
                            <p className="text-xs text-slate-500 mt-1">
                                Export des rejets ou paiements de ton logiciel (CSV, Excel), fichier retour du concentrateur,
                                ou relevé PDF / photo. Les paiements ferment automatiquement les rejets récupérés.
                            </p>
                        </div>
                        <button onClick={() => input.current?.click()} disabled={busy}
                            className="px-4 py-2.5 rounded-xl bg-brand text-white text-sm font-semibold flex items-center gap-2 disabled:opacity-50">
                            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} Choisir un fichier
                        </button>
                        <input ref={input} type="file" className="hidden"
                            accept=".csv,.txt,.noe,.xlsx,.xlsm,application/pdf,image/*"
                            onChange={e => upload(e.target.files?.[0])} />
                    </div>
                </div>

                {message?.error && <div className="mb-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-200 text-sm px-4 py-3">{message.error}</div>}
                {message?.info && <div className="mb-4 rounded-xl bg-slate-800 border border-white/10 text-sm px-4 py-3">{message.info}</div>}
                {message?.ok && (
                    <div className="mb-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-100 text-sm px-4 py-3">
                        {message.ok.importees} ligne(s) importée(s) sur {message.ok.lignes_lues}
                        {' '}· {message.ok.rattachees} rattachée(s) à un dossier
                        {message.ok.paiements > 0 && ` · ${message.ok.paiements} paiement(s)`}
                        {message.ok.rejets_recuperes > 0 && ` · ${message.ok.rejets_recuperes} rejet(s) récupéré(s)`}
                        {message.ok.doublons_ignores > 0 && ` · ${message.ok.doublons_ignores} déjà connue(s)`}
                        {Object.keys(message.ok.colonnes_reconnues || {}).length > 0 && (
                            <p className="text-xs text-emerald-200/80 mt-1">
                                Colonnes reconnues : {Object.keys(message.ok.colonnes_reconnues).join(', ')}
                                {message.ok.colonnes_ignorees?.length > 0 && ` · ignorées : ${message.ok.colonnes_ignorees.join(', ')}`}
                            </p>
                        )}
                    </div>
                )}

                <div className="flex flex-wrap gap-2 mb-4">
                    {[['ouverts', 'À traiter'], ['', 'Tous'], ['recupere', 'Récupérés'], ['abandonne', 'Abandonnés']].map(([k, l]) => (
                        <button key={k || 'all'} onClick={() => setFilter(k)}
                            className={`text-xs px-3 py-1.5 rounded-full border ${filter === k ? 'border-white/40 text-white' : 'border-white/10 text-slate-400'}`}>
                            {l}
                        </button>
                    ))}
                </div>

                <div className="space-y-3">
                    {rows.length === 0 && (
                        <div className="glass rounded-2xl border border-white/10 p-8 text-center text-sm text-slate-500 flex flex-col items-center gap-2">
                            <ShieldAlert className="w-6 h-6" /> Aucun rejet dans cette vue.
                        </div>
                    )}
                    {rows.map(r => (
                        <RejetCard key={r.id} r={r} statuts={catalogue.statuts || {}} onChange={change} onReopen={reopen} onDelete={remove} />
                    ))}
                </div>
            </div>
        </div>
    );
}

export default PmtRejetsPanel;
