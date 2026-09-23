import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Bot, Radar, Globe2, Mail, Rocket, AlertTriangle, Clock3,
    Play, Plus, Trash2, ToggleLeft, ToggleRight, RefreshCw
} from 'lucide-react';

function Metric({ icon: Icon, label, value, hint, tone = 'text-white' }) {
    return (
        <div className="glass rounded-2xl border border-white/10 p-4">
            <div className="flex items-start justify-between gap-3">
                <div>
                    <p className={`text-2xl font-extrabold ${tone}`}>{value ?? 0}</p>
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mt-1">{label}</p>
                    {hint && <p className="text-[11px] text-slate-600 mt-1">{hint}</p>}
                </div>
                <Icon className={`w-5 h-5 ${tone}`} />
            </div>
        </div>
    );
}

function AutopilotPanel() {
    const [dashboard, setDashboard] = useState(null);
    const [zones, setZones] = useState([]);
    const [query, setQuery] = useState('');
    const [radius, setRadius] = useState(1000);
    const [minScore, setMinScore] = useState(62);
    const [maxSites, setMaxSites] = useState(3);
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState('');

    const refresh = async () => {
        const [d, z] = await Promise.all([
            axios.get('/automation/dashboard'),
            axios.get('/automation/zones'),
        ]);
        setDashboard(d.data);
        setZones(Array.isArray(z.data) ? z.data : []);
    };

    useEffect(() => {
        refresh().catch(console.error);
        const id = setInterval(() => refresh().catch(() => {}), 15000);
        return () => clearInterval(id);
    }, []);

    const addZone = async () => {
        if (!query.trim()) return;
        setBusy(true); setMessage('');
        try {
            await axios.post('/automation/zones', {
                name: query.trim(),
                query: query.trim(),
                radius: Number(radius),
                min_opportunity_score: Number(minScore),
                max_sites_per_run: Number(maxSites),
                enabled: true,
            });
            setQuery('');
            setMessage('Zone ajoutée. Elle sera incluse dans le prochain run automatique.');
            await refresh();
        } catch (e) {
            setMessage(e?.response?.data?.detail || e.message || 'Impossible d’ajouter la zone');
        } finally {
            setBusy(false);
        }
    };

    const toggleZone = async (zone) => {
        await axios.patch(`/automation/zones/${zone.id}`, { enabled: !zone.enabled });
        await refresh();
    };

    const removeZone = async (zone) => {
        await axios.delete(`/automation/zones/${zone.id}`);
        await refresh();
    };

    const runNow = async () => {
        setBusy(true); setMessage('');
        try {
            await axios.post('/automation/run');
            setMessage('Autopilot lancé. Le dashboard va se mettre à jour automatiquement.');
            setTimeout(() => refresh().catch(() => {}), 2000);
        } catch (e) {
            setMessage(e?.response?.data?.detail || e.message || 'Impossible de lancer l’autopilot');
        } finally {
            setBusy(false);
        }
    };

    const today = dashboard?.today || {};
    const overnight = dashboard?.overnight || {};
    const queue = dashboard?.queue || {};
    const auto = dashboard?.autopilot || {};
    const scheduler = auto?.scheduler || {};

    return (
        <section className="space-y-5">
            <div className="rounded-3xl border border-brand/20 bg-gradient-to-br from-brand/10 via-slate-900 to-slate-950 p-5 md:p-6">
                <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-brand/15 border border-brand/30 flex items-center justify-center shrink-0">
                            <Bot className="w-6 h-6 text-brand" />
                        </div>
                        <div>
                            <div className="flex flex-wrap items-center gap-2">
                                <h3 className="text-xl font-extrabold">Autopilot Local Pulse</h3>
                                <span className={`text-[10px] font-bold px-2 py-1 rounded-full border ${
                                    auto.enabled
                                        ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20'
                                        : 'text-rose-300 bg-rose-500/10 border-rose-500/20'
                                }`}>
                                    {auto.enabled ? 'ACTIF' : 'DÉSACTIVÉ'}
                                </span>
                            </div>
                            <p className="text-sm text-slate-400 mt-1">
                                Scan → scoring → site → Vercel → email prêt. L’envoi reste soumis à validation humaine.
                            </p>
                            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-xs text-slate-500">
                                <span className="flex items-center gap-1.5">
                                    <Clock3 className="w-3.5 h-3.5" />
                                    Prochain run : {scheduler?.next_run ? new Date(scheduler.next_run).toLocaleString('fr-FR') : 'à planifier'}
                                </span>
                                <span>{auto.zones_enabled || 0} zone(s) active(s)</span>
                                <span>Déploiement auto : {auto.auto_deploy ? 'oui' : 'non'}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => refresh()}
                            className="p-3 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10"
                            title="Actualiser"
                        >
                            <RefreshCw className="w-4 h-4" />
                        </button>
                        <button
                            onClick={runNow}
                            disabled={busy || zones.filter(z => z.enabled).length === 0}
                            className="px-4 py-3 rounded-xl bg-brand hover:bg-brand-dark disabled:opacity-40 font-bold text-sm flex items-center gap-2"
                        >
                            <Play className="w-4 h-4" /> Lancer maintenant
                        </button>
                    </div>
                </div>
            </div>

            <div>
                <div className="flex items-center justify-between mb-3">
                    <div>
                        <h4 className="font-bold">Cette nuit</h4>
                        <p className="text-xs text-slate-500">Ce que Local Pulse a préparé pendant votre absence.</p>
                    </div>
                    {dashboard?.last_run && (
                        <span className="text-xs text-slate-500">
                            Dernier run #{dashboard.last_run.id} · {dashboard.last_run.status}
                        </span>
                    )}
                </div>
                <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
                    <Metric icon={Radar} label="Scannés" value={overnight.businesses_scanned} tone="text-sky-400" />
                    <Metric icon={Radar} label="Opportunités" value={overnight.opportunities_selected} tone="text-amber-400" />
                    <Metric icon={Globe2} label="Sites générés" value={overnight.sites_generated} tone="text-violet-400" />
                    <Metric icon={Rocket} label="Vercel" value={overnight.sites_deployed} tone="text-emerald-400" />
                    <Metric icon={Mail} label="Emails prêts" value={overnight.emails_ready} tone="text-brand" />
                    <Metric icon={AlertTriangle} label="Erreurs" value={overnight.errors} tone="text-rose-400" />
                </div>
            </div>

            <div>
                <h4 className="font-bold mb-3">Aujourd’hui</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <Metric icon={Radar} label="Scannés" value={today.businesses_scanned} tone="text-sky-400" />
                    <Metric icon={Globe2} label="Sites générés" value={today.sites_generated} tone="text-violet-400" />
                    <Metric icon={Mail} label="Emails prêts aujourd’hui" value={today.emails_ready} tone="text-brand" />
                    <Metric icon={Mail} label="File prête totale" value={queue.emails_ready_total} hint={`${queue.emails_missing_recipient || 0} sans destinataire vérifié`} tone="text-emerald-400" />
                </div>
            </div>

            <div className="glass rounded-2xl border border-white/10 overflow-hidden">
                <div className="p-5 border-b border-white/10">
                    <h4 className="font-bold">Zones de prospection automatique</h4>
                    <p className="text-xs text-slate-500 mt-1">
                        Une fois configurées, ces zones sont scannées chaque nuit sans intervention.
                    </p>
                </div>

                <div className="p-4 grid grid-cols-1 xl:grid-cols-[1fr_150px_170px_150px_auto] gap-3 border-b border-white/10 items-end">
                    <div>
                        <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                            Ville ou code postal
                        </label>
                        <input
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                            placeholder="Ex. Trappes ou 78190"
                            className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm"
                        />
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                            Rayon du scan
                        </label>
                        <input
                            type="number"
                            min="100"
                            max="5000"
                            value={radius}
                            onChange={e => setRadius(e.target.value)}
                            className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm"
                        />
                        <p className="text-[10px] text-slate-600 mt-1">En mètres · 1000 = 1 km</p>
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                            Score minimum
                        </label>
                        <input
                            type="number"
                            min="0"
                            max="100"
                            value={minScore}
                            onChange={e => setMinScore(e.target.value)}
                            className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm"
                        />
                        <p className="text-[10px] text-slate-600 mt-1">Opportunity Score /100</p>
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                            Sites max / nuit
                        </label>
                        <input
                            type="number"
                            min="0"
                            max="20"
                            value={maxSites}
                            onChange={e => setMaxSites(e.target.value)}
                            className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm"
                        />
                        <p className="text-[10px] text-slate-600 mt-1">Limite par zone et par run</p>
                    </div>

                    <button
                        onClick={addZone}
                        disabled={busy || !query.trim()}
                        className="rounded-xl bg-white/10 hover:bg-white/15 border border-white/10 px-4 py-2.5 text-sm font-bold flex items-center justify-center gap-2 disabled:opacity-40 min-h-[42px]"
                    >
                        <Plus className="w-4 h-4" /> Ajouter
                    </button>
                </div>

                <div className="divide-y divide-white/5">
                    {zones.length === 0 ? (
                        <div className="p-6 text-sm text-slate-500">
                            Ajoutez au moins une ville pour démarrer l’autopilot.
                        </div>
                    ) : zones.map(zone => (
                        <div key={zone.id} className="p-4 flex flex-col md:flex-row md:items-center gap-3">
                            <button onClick={() => toggleZone(zone)} className="shrink-0">
                                {zone.enabled
                                    ? <ToggleRight className="w-7 h-7 text-emerald-400" />
                                    : <ToggleLeft className="w-7 h-7 text-slate-500" />}
                            </button>
                            <div className="flex-1">
                                <p className="font-semibold text-sm">{zone.name}</p>
                                <p className="text-[11px] text-slate-500 mt-1">
                                    rayon {zone.radius} m · score ≥ {zone.min_opportunity_score} · max {zone.max_sites_per_run} site(s)/run
                                </p>
                            </div>
                            <button
                                onClick={() => removeZone(zone)}
                                className="text-slate-500 hover:text-rose-400 p-2"
                                title="Supprimer"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {message && (
                <div className="text-sm bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-slate-300">
                    {message}
                </div>
            )}
        </section>
    );
}

export default AutopilotPanel;
