import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Bot, Github, Play, Power, RefreshCw, Trash2, CheckCircle2, AlertTriangle } from 'lucide-react';

function AgentTeamsView({ businesses = [] }) {
    const [teams, setTeams] = useState([]);
    const [runs, setRuns] = useState([]);
    const [businessId, setBusinessId] = useState('');
    const [repoUrl, setRepoUrl] = useState('');
    const [manifestPath, setManifestPath] = useState('team.yaml');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const selectedBusiness = useMemo(
        () => businesses.find(b => b.id === businessId),
        [businesses, businessId]
    );

    const refresh = async () => {
        const params = businessId ? { business_id: businessId } : {};
        const [t, r] = await Promise.all([
            axios.get('/agent-teams', { params }),
            axios.get('/agent-teams/runs?limit=25'),
        ]);
        setTeams(Array.isArray(t.data) ? t.data : []);
        setRuns(Array.isArray(r.data) ? r.data : []);
    };

    useEffect(() => {
        refresh().catch(console.error);
    }, [businessId]);

    const install = async () => {
        if (!repoUrl.trim()) return;
        setLoading(true); setMessage('');
        try {
            const r = await axios.post('/agent-teams/install', {
                repo_url: repoUrl.trim(),
                manifest_path: manifestPath.trim() || 'team.yaml',
                ref: 'main',
            });
            setMessage(`Équipe ${r.data.name} installée.`);
            setRepoUrl('');
            await refresh();
        } catch (e) {
            setMessage(e?.response?.data?.detail || e.message || 'Installation impossible');
        } finally {
            setLoading(false);
        }
    };

    const toggle = async (team) => {
        await axios.patch(`/agent-teams/${team.slug}`, { enabled: !team.enabled });
        await refresh();
    };

    const remove = async (team) => {
        if (team.source_type === 'builtin') return;
        await axios.delete(`/agent-teams/${team.slug}`);
        await refresh();
    };

    const assign = async (team) => {
        if (!businessId) {
            setMessage('Choisis d’abord un commerce.');
            return;
        }
        await axios.post(`/agent-teams/${team.slug}/assign/${encodeURIComponent(businessId)}`, {
            enabled: !team.assigned,
        });
        await refresh();
    };

    const run = async (team) => {
        if (!businessId) {
            setMessage('Choisis d’abord un commerce.');
            return;
        }
        setLoading(true); setMessage('');
        try {
            const r = await axios.post(
                `/agent-teams/${team.slug}/run?business_id=${encodeURIComponent(businessId)}`
            );
            setMessage(`Équipe ${team.name} lancée · run #${r.data.run_id}`);
            setTimeout(() => refresh().catch(console.error), 1200);
        } catch (e) {
            setMessage(e?.response?.data?.detail || e.message || 'Lancement impossible');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="w-full h-full overflow-y-auto bg-slate-900 p-4 md:p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 mb-8">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-11 h-11 rounded-2xl bg-brand/15 border border-brand/30 flex items-center justify-center">
                                <Bot className="w-6 h-6 text-brand" />
                            </div>
                            <div>
                                <h2 className="text-3xl font-extrabold">Équipes d’agents</h2>
                                <p className="text-slate-400 text-sm">Installe, assigne et lance des workflows spécialisés.</p>
                            </div>
                        </div>
                    </div>
                    <div className="min-w-[280px]">
                        <label className="text-xs text-slate-400 font-bold uppercase tracking-wider">Commerce cible</label>
                        <select
                            value={businessId}
                            onChange={e => setBusinessId(e.target.value)}
                            className="mt-2 w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-3 text-sm"
                        >
                            <option value="">Choisir un commerce…</option>
                            {businesses.map(b => (
                                <option key={b.id} value={b.id}>{b.name}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="glass rounded-2xl border border-white/10 p-5 mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Github className="w-5 h-5 text-white" />
                        <h3 className="font-bold">Installer une équipe depuis GitHub</h3>
                    </div>
                    <div className="grid grid-cols-1 lg:grid-cols-[1fr_220px_auto] gap-3">
                        <input
                            value={repoUrl}
                            onChange={e => setRepoUrl(e.target.value)}
                            placeholder="https://github.com/organisation/agent-team"
                            className="bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm"
                        />
                        <input
                            value={manifestPath}
                            onChange={e => setManifestPath(e.target.value)}
                            placeholder="team.yaml"
                            className="bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm"
                        />
                        <button
                            disabled={loading || !repoUrl.trim()}
                            onClick={install}
                            className="bg-brand hover:bg-brand-dark disabled:opacity-50 rounded-xl px-5 py-3 font-bold text-sm"
                        >
                            Installer
                        </button>
                    </div>
                    <p className="text-xs text-slate-500 mt-3">
                        Sécurité V1 : seuls les manifests YAML/JSON, prompts et workflows déclaratifs sont importés. Aucun Python ou shell distant n’est exécuté.
                    </p>
                    {message && (
                        <div className="mt-3 text-sm bg-white/5 border border-white/10 rounded-xl px-4 py-3">{message}</div>
                    )}
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 mb-10">
                    {teams.map(team => (
                        <div key={team.slug} className="glass rounded-2xl border border-white/10 p-5 flex flex-col">
                            <div className="flex items-start justify-between gap-3">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-bold text-lg">{team.name}</h3>
                                        <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                                            team.enabled ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20' : 'text-slate-400 bg-white/5 border-white/10'
                                        }`}>
                                            {team.enabled ? 'ACTIVE' : 'OFF'}
                                        </span>
                                    </div>
                                    <p className="text-xs text-brand mt-1">{team.category} · v{team.version}</p>
                                </div>
                                <button onClick={() => toggle(team)} className="p-2 rounded-lg hover:bg-white/5" title="Activer/désactiver">
                                    <Power className="w-4 h-4" />
                                </button>
                            </div>

                            <p className="text-sm text-slate-400 mt-4 min-h-[40px]">{team.description}</p>

                            <div className="mt-4 space-y-2 flex-1">
                                {(team.agents || []).map((a, i) => (
                                    <div key={a.id} className="bg-white/[0.03] rounded-xl px-3 py-2.5">
                                        <p className="text-sm font-semibold">{i + 1}. {a.name || a.id}</p>
                                        <p className="text-[11px] text-slate-500">{a.role}</p>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-4 text-[11px] text-slate-500">
                                Plans : {(team.allowed_plans || []).join(' · ') || 'manuel'}
                            </div>

                            <div className="grid grid-cols-2 gap-2 mt-4">
                                <button
                                    onClick={() => assign(team)}
                                    disabled={!businessId}
                                    className={`rounded-xl py-2.5 text-xs font-bold border disabled:opacity-40 ${
                                        team.assigned
                                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                                            : 'bg-white/5 border-white/10 text-slate-300'
                                    }`}
                                >
                                    {team.assigned ? 'Assignée ✓' : 'Assigner'}
                                </button>
                                <button
                                    onClick={() => run(team)}
                                    disabled={!businessId || !team.enabled || loading}
                                    className="rounded-xl py-2.5 text-xs font-bold bg-brand hover:bg-brand-dark disabled:opacity-40 flex items-center justify-center gap-2"
                                >
                                    <Play className="w-3.5 h-3.5" /> Lancer
                                </button>
                            </div>

                            {team.source_type === 'git' && (
                                <button onClick={() => remove(team)} className="mt-2 text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1.5">
                                    <Trash2 className="w-3.5 h-3.5" /> Supprimer cette équipe Git
                                </button>
                            )}
                        </div>
                    ))}
                </div>

                <div className="glass rounded-2xl border border-white/10 overflow-hidden">
                    <div className="p-5 border-b border-white/10 flex items-center justify-between">
                        <div>
                            <h3 className="font-bold">Exécutions récentes</h3>
                            {selectedBusiness && <p className="text-xs text-slate-500 mt-1">Commerce sélectionné : {selectedBusiness.name}</p>}
                        </div>
                        <button onClick={() => refresh()} className="p-2 rounded-lg hover:bg-white/5">
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="divide-y divide-white/5">
                        {runs.length === 0 ? (
                            <div className="p-6 text-sm text-slate-500">Aucune exécution.</div>
                        ) : runs.map(runItem => (
                            <details key={runItem.id} className="p-4">
                                <summary className="cursor-pointer flex items-center gap-3 list-none">
                                    {runItem.status === 'completed'
                                        ? <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                                        : runItem.status === 'error'
                                            ? <AlertTriangle className="w-4 h-4 text-rose-400" />
                                            : <RefreshCw className="w-4 h-4 text-amber-400 animate-spin" />}
                                    <span className="font-semibold">{runItem.team_slug}</span>
                                    <span className="text-xs text-slate-500">#{runItem.id}</span>
                                    <span className="text-xs text-slate-500 ml-auto">{runItem.status}</span>
                                </summary>
                                <div className="mt-4 space-y-3">
                                    {runItem.error && <div className="text-sm text-rose-300">{runItem.error}</div>}
                                    {Object.entries(runItem.outputs || {}).map(([key, value]) => (
                                        <div key={key} className="bg-slate-950/60 rounded-xl p-4">
                                            <p className="text-xs font-bold uppercase tracking-wider text-brand mb-2">{key}</p>
                                            <pre className="text-xs text-slate-300 whitespace-pre-wrap font-sans">{String(value)}</pre>
                                        </div>
                                    ))}
                                </div>
                            </details>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AgentTeamsView;
