import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import { FileDown, Loader2, Settings2, X, ArrowUp, ArrowDown, Trash2, Save } from 'lucide-react';

// Export des dossiers vers le logiciel de facturation du client ambulancier.
// Formats prédéfinis + profils personnalisés (colonnes, séparateur, encodage…)
// pour coller au modèle d'import de chaque logiciel.

const SCOPES = [
    ['a_exporter', 'Nouveaux dossiers prêts'],
    ['exportables', 'Tous les dossiers prêts (réexport)'],
    ['tous', 'Tous, y compris à corriger'],
];

const FORMAT_LABELS = { csv: 'CSV', xlsx: 'Excel (.xlsx)', json: 'JSON', zip: 'ZIP dossiers complets' };

const filenameFrom = (headers, fallback) => {
    const m = /filename="([^"]+)"/.exec(headers['content-disposition'] || '');
    return m ? m[1] : fallback;
};

const errorText = async (e) => {
    const data = e?.response?.data;
    if (data instanceof Blob) {
        try { return JSON.parse(await data.text()).detail; } catch { /* corps non JSON */ }
    }
    return data?.detail || e.message;
};

function ProfileEditor({ options, profile, businessId, onClose, onSaved }) {
    const [draft, setDraft] = useState(() => structuredClone(profile));
    const [error, setError] = useState('');
    const selected = new Set(draft.columns.map(c => c.key));
    const fieldLabel = Object.fromEntries(options.fields.map(f => [f.key, f.label]));
    const groups = options.fields.reduce((acc, f) => ({ ...acc, [f.group]: [...(acc[f.group] || []), f] }), {});

    const set = (k, v) => setDraft(d => ({ ...d, [k]: v }));
    const toggle = (key) => set('columns', selected.has(key)
        ? draft.columns.filter(c => c.key !== key)
        : [...draft.columns, { key, label: '' }]);
    const move = (i, delta) => {
        const cols = [...draft.columns];
        const j = i + delta;
        if (j < 0 || j >= cols.length) return;
        [cols[i], cols[j]] = [cols[j], cols[i]];
        set('columns', cols);
    };
    const rename = (i, label) => set('columns', draft.columns.map((c, k) => (k === i ? { ...c, label } : c)));

    const save = async () => {
        setError('');
        try {
            const body = { ...draft, business_id: draft.business_id ?? (businessId || null) };
            const r = draft.id
                ? await axios.put(`/pmt/export/profiles/${draft.id}`, body)
                : await axios.post('/pmt/export/profiles', body);
            onSaved(r.data);
        } catch (e) {
            setError(e?.response?.data?.detail || e.message);
        }
    };

    const remove = async () => {
        if (!draft.id || !window.confirm('Supprimer ce profil d’export ?')) return;
        await axios.delete(`/pmt/export/profiles/${draft.id}`);
        onSaved(null);
    };

    const select = (k, entries) => (
        <select value={draft[k]} onChange={e => set(k, e.target.value)}
            className="mt-1 w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm">
            {entries.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
    );

    return (
        <div className="fixed inset-0 z-[5000] flex">
            <div className="flex-1 bg-black/60 backdrop-blur-sm" onClick={onClose} />
            <div className="w-full md:w-[760px] h-full bg-slate-950 border-l border-white/10 overflow-y-auto">
                <div className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur border-b border-white/10 p-5 flex items-center justify-between">
                    <div>
                        <h3 className="font-bold text-lg">Profil d’export</h3>
                        <p className="text-xs text-slate-500 mt-1">Reproduis le modèle d’import du logiciel de facturation du client.</p>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-white/10"><X className="w-5 h-5" /></button>
                </div>
                <div className="p-5 space-y-5">
                    {error && <div className="rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-200 text-sm px-4 py-3">{error}</div>}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-400">
                        <label className="sm:col-span-2">Nom du profil
                            <input value={draft.name} onChange={e => set('name', e.target.value)}
                                placeholder="ex. Import ISIS — Ambulances Dupont"
                                className="mt-1 w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white" />
                        </label>
                        <label>Format{select('format', options.formats.map(f => [f, FORMAT_LABELS[f]]))}</label>
                        <label>Séparateur{select('delimiter', Object.entries(options.delimiters))}</label>
                        <label>Encodage{select('encoding', Object.entries(options.encodings))}</label>
                        <label>Dates{select('date_format', Object.entries(options.date_formats))}</label>
                        <label>Cases à cocher{select('bool_format', options.bool_formats.map(b => [b, b === 'X/' ? 'X / vide' : b]))}</label>
                        <label>Décimales{select('decimal', [[',', 'Virgule (12,5)'], ['.', 'Point (12.5)']])}</label>
                        <label className="flex items-center gap-2 text-sm text-white">
                            <input type="checkbox" checked={draft.header} onChange={e => set('header', e.target.checked)} className="accent-sky-500" />
                            Ligne d’en-tête
                        </label>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <div>
                            <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Champs disponibles</p>
                            <div className="space-y-3 max-h-[52vh] overflow-y-auto pr-1">
                                {Object.entries(groups).map(([group, fields]) => (
                                    <div key={group}>
                                        <p className="text-[11px] text-slate-500 mb-1">{group}</p>
                                        {fields.map(f => (
                                            <label key={f.key} className="flex items-center gap-2 text-sm py-0.5 cursor-pointer">
                                                <input type="checkbox" checked={selected.has(f.key)} onChange={() => toggle(f.key)} className="accent-sky-500" />
                                                {f.label}
                                            </label>
                                        ))}
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                                Colonnes exportées ({draft.columns.length}) — ordre et intitulés
                            </p>
                            <div className="space-y-1 max-h-[52vh] overflow-y-auto pr-1">
                                {draft.columns.map((c, i) => (
                                    <div key={c.key} className="flex items-center gap-1">
                                        <span className="text-[10px] text-slate-600 w-5 text-right">{i + 1}</span>
                                        <input value={c.label} onChange={e => rename(i, e.target.value)} placeholder={fieldLabel[c.key]}
                                            className="flex-1 min-w-0 bg-slate-800 border border-white/10 rounded-lg px-2 py-1 text-xs" />
                                        <button onClick={() => move(i, -1)} className="p-1 rounded hover:bg-white/10"><ArrowUp className="w-3 h-3" /></button>
                                        <button onClick={() => move(i, 1)} className="p-1 rounded hover:bg-white/10"><ArrowDown className="w-3 h-3" /></button>
                                        <button onClick={() => toggle(c.key)} className="p-1 rounded hover:bg-white/10 text-rose-300"><X className="w-3 h-3" /></button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-between gap-2">
                        {draft.id ? (
                            <button onClick={remove} className="px-3 py-2 rounded-xl border border-rose-500/30 text-rose-300 text-sm flex items-center gap-1">
                                <Trash2 className="w-4 h-4" /> Supprimer
                            </button>
                        ) : <span />}
                        <button onClick={save} className="px-4 py-2 rounded-xl bg-brand text-white text-sm font-semibold flex items-center gap-1">
                            <Save className="w-4 h-4" /> Enregistrer le profil
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function PmtExportPanel({ businessId, toExport, onExported }) {
    const [options, setOptions] = useState(null);
    const [profiles, setProfiles] = useState([]);
    const [choice, setChoice] = useState(() => {
        try { return localStorage.getItem('lp_pmt_export_choice') || 'preset:standard'; } catch { return 'preset:standard'; }
    });
    const [scope, setScope] = useState('a_exporter');
    const [editing, setEditing] = useState(null);
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState('');

    const loadProfiles = async () => {
        const r = await axios.get('/pmt/export/profiles', { params: businessId ? { business_id: businessId } : {} });
        setProfiles(Array.isArray(r.data) ? r.data : []);
    };

    useEffect(() => { axios.get('/pmt/export/options').then(r => setOptions(r.data)).catch(() => {}); }, []);
    useEffect(() => { loadProfiles().catch(() => {}); }, [businessId]);
    useEffect(() => { try { localStorage.setItem('lp_pmt_export_choice', choice); } catch { /* indisponible */ } }, [choice]);

    const [kind, id] = choice.split(':');

    const run = async () => {
        setBusy(true); setMessage('');
        try {
            const body = { business_id: businessId || null, scope, ...(kind === 'preset' ? { preset: id } : { profile_id: Number(id) }) };
            const r = await axios.post('/pmt/export', body, { responseType: 'blob', timeout: 120000 });
            const url = URL.createObjectURL(r.data);
            const a = document.createElement('a');
            a.href = url;
            a.download = filenameFrom(r.headers, 'transports');
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            setMessage(`${r.headers['x-export-count'] || ''} dossier(s) exporté(s).`);
            onExported?.();
        } catch (e) {
            setMessage(await errorText(e));
        } finally {
            setBusy(false);
        }
    };

    const openEditor = () => {
        if (!options) return;
        if (kind === 'profile') {
            setEditing(profiles.find(p => String(p.id) === id));
        } else {
            const base = options.presets.find(p => p.id === id) || options.presets[0];
            setEditing({ ...base, id: undefined, name: `${base.name} (personnalisé)` });
        }
    };

    return (
        <div className="glass rounded-2xl border border-white/10 p-4">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Export vers le logiciel de facturation</p>
            <div className="space-y-2">
                <select value={choice} onChange={e => setChoice(e.target.value)}
                    className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm">
                    <optgroup label="Formats prêts à l’emploi">
                        {(options?.presets || []).map(p => <option key={p.id} value={`preset:${p.id}`}>{p.name}</option>)}
                    </optgroup>
                    {profiles.length > 0 && (
                        <optgroup label="Profils du client">
                            {profiles.map(p => <option key={p.id} value={`profile:${p.id}`}>{p.name}</option>)}
                        </optgroup>
                    )}
                </select>
                <select value={scope} onChange={e => setScope(e.target.value)}
                    className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm">
                    {SCOPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
                <div className="flex gap-2">
                    <button onClick={run} disabled={busy}
                        className="flex-1 px-3 py-2 rounded-xl bg-brand text-white text-sm font-semibold flex items-center justify-center gap-1 disabled:opacity-50">
                        {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                        Exporter{scope === 'a_exporter' ? ` (${toExport})` : ''}
                    </button>
                    <button onClick={openEditor} title="Adapter les colonnes au logiciel du client"
                        className="px-3 py-2 rounded-xl bg-slate-800 border border-white/10 text-sm flex items-center gap-1">
                        <Settings2 className="w-4 h-4" /> {kind === 'profile' ? 'Modifier' : 'Personnaliser'}
                    </button>
                </div>
            </div>
            {message && <p className="text-xs text-slate-300 mt-2">{message}</p>}
            <p className="text-[11px] text-slate-500 mt-2">
                Seuls les dossiers prêts (ou vérifiés) partent. Une fois exportés, ils ne repartent pas en double.
            </p>
            {/* Portail : .glass (backdrop-filter) emprisonnerait le tiroir en position fixe. */}
            {editing && options && createPortal(
                <ProfileEditor
                    options={options}
                    profile={editing}
                    businessId={businessId}
                    onClose={() => setEditing(null)}
                    onSaved={async (saved) => {
                        setEditing(null);
                        await loadProfiles();
                        setChoice(saved ? `profile:${saved.id}` : 'preset:standard');
                    }}
                />,
                document.body,
            )}
        </div>
    );
}

export default PmtExportPanel;
