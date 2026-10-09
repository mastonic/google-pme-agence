import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { MapPinned, Upload, Loader2, Link2, Unlink, AlertTriangle, CheckCircle2, ShieldCheck } from 'lucide-react';

// Traces GPS : export du boîtier de géolocalisation (GPX, KML, CSV) → km de
// chaque course reportés dans le bon dossier, sans saisie manuelle.

const frDateTime = (iso) => {
    if (!iso) return '—';
    const [d, t] = iso.split('T');
    return `${d.split('-').reverse().join('/')} ${t?.slice(0, 5) || ''}`;
};
const hhmm = (iso) => (iso ? iso.slice(11, 16) : '');
const km = (n) => `${(n || 0).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} km`;

function PmtTracesPanel({ businesses = [], user }) {
    const isAdmin = user?.role === 'admin';
    const [businessId, setBusinessId] = useState('');
    const [traces, setTraces] = useState([]);
    const [vouchers, setVouchers] = useState([]);
    const [filter, setFilter] = useState('');
    const [busy, setBusy] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const input = useRef(null);

    const params = () => (businessId ? { business_id: businessId } : {});

    const refresh = async () => {
        const [t, v] = await Promise.all([
            axios.get('/pmt/traces', { params: { ...params(), ...(filter ? { rattachees: filter } : {}) } }),
            axios.get('/pmt/vouchers', { params: params() }),
        ]);
        setTraces(t.data);
        setVouchers(v.data);
    };

    useEffect(() => { refresh().catch(e => setError(e?.response?.data?.detail || e.message)); }, [businessId, filter]);

    const upload = async (file) => {
        if (!file) return;
        if (isAdmin && !businessId) { setError('Choisis d’abord le client ambulancier.'); return; }
        setBusy(true); setError(''); setResult(null);
        const form = new FormData();
        form.append('file', file);
        if (businessId) form.append('business_id', businessId);
        try {
            const r = await axios.post('/pmt/traces/import', form, { timeout: 120000 });
            setResult(r.data);
            await refresh();
        } catch (e) {
            setError(e?.response?.data?.detail || e.message);
        } finally {
            setBusy(false);
            if (input.current) input.current.value = '';
        }
    };

    const attach = async (key, voucherId) => {
        if (!voucherId) return;
        await axios.post(`/pmt/traces/${key}/attach`, { voucher_id: voucherId });
        await refresh();
    };
    const detach = async (key) => {
        await axios.post(`/pmt/traces/${key}/detach`);
        await refresh();
    };

    const voucherLabel = (v) => {
        const b = v.data?.beneficiaire || {};
        return `${[b.nom, b.prenom].filter(Boolean).join(' ') || 'Patient ?'} · ${v.transport?.date_transport || '?'}`
            + `${v.transport?.heure_depart ? ' ' + v.transport.heure_depart : ''}${v.transport?.vehicule ? ' · ' + v.transport.vehicule : ''}`;
    };
    const byId = Object.fromEntries(vouchers.map(v => [v.id, v]));
    const sameDay = (t) => vouchers.filter(v => v.transport?.date_transport === (t.start || '').slice(0, 10));

    return (
        <div className="w-full h-full overflow-y-auto p-4 md:p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-11 h-11 rounded-2xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center">
                            <MapPinned className="w-6 h-6 text-sky-300" />
                        </div>
                        <div>
                            <h2 className="text-3xl font-extrabold">Traces GPS</h2>
                            <p className="text-slate-400 text-sm">Les km du boîtier de géolocalisation reportés dans chaque dossier, sans saisie.</p>
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

                <div className="flex items-start gap-2 rounded-xl border border-white/10 bg-slate-800/60 text-slate-300 text-xs p-3 mb-6">
                    <ShieldCheck className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-400" />
                    <p>Les points GPS ne sont pas conservés : seul le résumé de chaque course (véhicule, horaires, km) est gardé,
                        puis effacé après 3 mois. Les données servent uniquement à vérifier les transports facturés.</p>
                </div>

                <div className="glass rounded-2xl border-2 border-dashed border-white/15 p-5 mb-4"
                    onDragOver={e => e.preventDefault()}
                    onDrop={e => { e.preventDefault(); upload(e.dataTransfer.files?.[0]); }}>
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                        <div className="flex-1">
                            <p className="font-semibold text-sm">Importer l’export du boîtier</p>
                            <p className="text-xs text-slate-500 mt-1">
                                GPX (le plus courant), KML ou CSV / Excel (points GPS ou liste des courses avec les km).
                                Chaque course est rattachée au dossier du même véhicule, même jour, à l’heure de départ la plus proche.
                            </p>
                        </div>
                        <button onClick={() => input.current?.click()} disabled={busy}
                            className="px-4 py-2.5 rounded-xl bg-brand text-white text-sm font-semibold flex items-center gap-2 disabled:opacity-50">
                            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} Choisir un fichier
                        </button>
                        <input ref={input} type="file" className="hidden" accept=".gpx,.kml,.csv,.txt,.xlsx,application/gpx+xml"
                            onChange={e => upload(e.target.files?.[0])} />
                    </div>
                </div>

                {error && <div className="mb-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-200 text-sm px-4 py-3">{error}</div>}
                {result && (
                    <div className="mb-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-100 text-sm px-4 py-3 space-y-1">
                        <p>{result.courses_lues} course(s) lue(s) · {result.importees} nouvelle(s) · <b>{result.rattachees} rattachée(s) automatiquement</b>
                            {result.doublons_ignores > 0 && ` · ${result.doublons_ignores} déjà connue(s)`}
                            {result.avec_trous > 0 && ` · ${result.avec_trous} avec des trous`}</p>
                        {result.dossiers_sans_trace?.length > 0 && (
                            <p className="text-amber-200">
                                <AlertTriangle className="w-4 h-4 inline mr-1" />
                                {result.dossiers_sans_trace.length} dossier(s) de ces jours sans trace : {result.dossiers_sans_trace.map(d => d.patient).join(', ')}.
                                Une course facturée sans trace risque le rejet.
                            </p>
                        )}
                    </div>
                )}

                <div className="flex flex-wrap gap-2 mb-4">
                    {[['', 'Toutes'], ['non', 'À rattacher'], ['oui', 'Rattachées']].map(([k, l]) => (
                        <button key={k || 'all'} onClick={() => setFilter(k)}
                            className={`text-xs px-3 py-1.5 rounded-full border ${filter === k ? 'border-white/40 text-white' : 'border-white/10 text-slate-400'}`}>
                            {l}
                        </button>
                    ))}
                </div>

                <div className="glass rounded-2xl border border-white/10 divide-y divide-white/5">
                    {traces.length === 0 && <p className="p-6 text-sm text-slate-500 text-center">Aucune trace importée.</p>}
                    {traces.map(t => {
                        const v = t.voucher_id && byId[t.voucher_id];
                        return (
                            <div key={t.key} className="p-4 grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-center">
                                <div className="min-w-0">
                                    <p className="font-semibold text-sm">
                                        {t.vehicule || 'Véhicule non indiqué'}
                                        <span className="text-slate-400 font-normal"> · {frDateTime(t.start)} → {hhmm(t.end)}</span>
                                        <span className="ml-2 text-white">{km(t.km)}</span>
                                    </p>
                                    <p className="text-xs text-slate-500 mt-1">
                                        {t.points > 0 ? `${t.points} points` : 'km fournis par le boîtier'} · {t.source}
                                        {t.reference && ` · mission ${t.reference}`}
                                    </p>
                                    {t.warnings?.length > 0 && (
                                        <p className="text-xs text-amber-300 mt-1"><AlertTriangle className="w-3 h-3 inline mr-1" />{t.warnings.join(' · ')}</p>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 text-xs">
                                    {v ? (
                                        <>
                                            <span className="flex items-center gap-1 text-emerald-300"><CheckCircle2 className="w-4 h-4" />{voucherLabel(v)}</span>
                                            <button onClick={() => detach(t.key)} title="Détacher" className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400">
                                                <Unlink className="w-4 h-4" />
                                            </button>
                                        </>
                                    ) : (
                                        <>
                                            <Link2 className="w-4 h-4 text-slate-500" />
                                            <select defaultValue="" onChange={e => attach(t.key, e.target.value)}
                                                className="bg-slate-800 border border-white/10 rounded-lg px-2 py-1.5 max-w-[300px]">
                                                <option value="">Rattacher à un dossier…</option>
                                                {(sameDay(t).length ? sameDay(t) : vouchers).map(vv => (
                                                    <option key={vv.id} value={vv.id}>{voucherLabel(vv)}</option>
                                                ))}
                                            </select>
                                        </>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

export default PmtTracesPanel;
