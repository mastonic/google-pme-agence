import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Bot, Radar, Globe2, Mail, Rocket, AlertTriangle, Clock3, ExternalLink,
    Play, Plus, Trash2, ToggleLeft, ToggleRight, RefreshCw, X, FolderOpen
} from 'lucide-react';

function Metric({ icon: Icon, label, value, hint, tone = 'text-white', onClick }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className="glass rounded-2xl border border-white/10 p-4 text-left hover:bg-white/[0.07] hover:border-white/20 transition-all group"
        >
            <div className="flex items-start justify-between gap-3">
                <div>
                    <p className={`text-2xl font-extrabold ${tone}`}>{value ?? 0}</p>
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mt-1">{label}</p>
                    {hint && <p className="text-[11px] text-slate-600 mt-1">{hint}</p>}
                    <p className="text-[10px] text-slate-600 mt-2 group-hover:text-slate-400">Cliquer pour voir la liste</p>
                </div>
                <Icon className={`w-5 h-5 ${tone}`} />
            </div>
        </button>
    );
}

function ProjectDrawer({ title, projects, loading, onClose, onOpenProject }) {
    return (
        <div className="fixed inset-0 z-[5000] flex">
            <div className="flex-1 bg-black/60 backdrop-blur-sm" onClick={onClose} />
            <div className="w-full md:w-[560px] h-full bg-slate-950 border-l border-white/10 overflow-y-auto">
                <div className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur border-b border-white/10 p-5 flex items-center justify-between">
                    <div>
                        <h3 className="font-bold text-lg">{title}</h3>
                        <p className="text-xs text-slate-500 mt-1">{projects.length} projet(s)</p>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-white/10"><X className="w-5 h-5"/></button>
                </div>
                {loading ? (
                    <div className="p-8 text-sm text-slate-500">Chargement…</div>
                ) : projects.length === 0 ? (
                    <div className="p-8 text-sm text-slate-500">Aucun projet dans cette étape.</div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {projects.map(p => (
                            <div key={p.id} className="p-4 hover:bg-white/[0.03]">
                                <div className="flex items-start justify-between gap-3">
                                    <div className="min-w-0">
                                        <p className="font-semibold truncate">{p.name}</p>
                                        <p className="text-xs text-slate-500 mt-1">{p.address}</p>
                                        <div className="flex flex-wrap gap-2 mt-2 text-[10px]">
                                            <span className="px-2 py-1 rounded-full bg-amber-500/10 text-amber-300">Opp. {Math.round(p.opportunity_score||0)}/100</span>
                                            <span className="px-2 py-1 rounded-full bg-slate-800 text-slate-400">{p.status}</span>
                                            {p.email_status === 'ready' && <span className="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-300">email prêt</span>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex flex-wrap gap-2 mt-3">
                                    <button onClick={() => onOpenProject?.(p.id)} className="px-3 py-2 rounded-xl bg-brand hover:bg-brand-dark text-xs font-bold flex items-center gap-2">
                                        <FolderOpen className="w-3.5 h-3.5"/> Ouvrir le projet
                                    </button>
                                    {p.deployment_url && <a href={p.deployment_url} target="_blank" rel="noreferrer" className="px-3 py-2 rounded-xl border border-white/10 text-xs text-slate-300 flex items-center gap-2">
                                        <ExternalLink className="w-3.5 h-3.5"/> Voir le site
                                    </a>}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function AutopilotPanel({ onOpenProject }) {
    const [dashboard, setDashboard] = useState(null);
    const [zones, setZones] = useState([]);
    const [query, setQuery] = useState('');
    const [radius, setRadius] = useState(1000);
    const [minScore, setMinScore] = useState(62);
    const [maxSites, setMaxSites] = useState(3);
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState('');
    const [drawer, setDrawer] = useState(null);
    const [projects, setProjects] = useState([]);
    const [listLoading, setListLoading] = useState(false);

    const refresh = async () => {
        const [d, z] = await Promise.all([axios.get('/automation/dashboard'), axios.get('/automation/zones')]);
        setDashboard(d.data);
        setZones(Array.isArray(z.data) ? z.data : []);
    };
    useEffect(() => {
        refresh().catch(console.error);
        const id = setInterval(() => refresh().catch(() => {}), 5000);
        return () => clearInterval(id);
    }, []);

    const openList = async (kind, scope, title) => {
        setDrawer({kind, scope, title}); setProjects([]); setListLoading(true);
        try {
            const r = await axios.get('/automation/projects', {params:{kind,scope}});
            setProjects(Array.isArray(r.data) ? r.data : []);
        } finally { setListLoading(false); }
    };

    const addZone = async () => {
        if (!query.trim()) return;
        setBusy(true); setMessage('');
        try {
            await axios.post('/automation/zones', {name:query.trim(), query:query.trim(), radius:Number(radius), min_opportunity_score:Number(minScore), max_sites_per_run:Number(maxSites), enabled:true});
            setQuery(''); setMessage('Zone ajoutée. Elle sera incluse dans le prochain run automatique.'); await refresh();
        } catch (e) { setMessage(e?.response?.data?.detail || e.message || 'Impossible d’ajouter la zone'); }
        finally { setBusy(false); }
    };
    const toggleZone = async z => { await axios.patch(`/automation/zones/${z.id}`,{enabled:!z.enabled}); await refresh(); };
    const removeZone = async z => { await axios.delete(`/automation/zones/${z.id}`); await refresh(); };
    const runNow = async () => {
        setBusy(true); setMessage('');
        try { await axios.post('/automation/run'); setMessage('Autopilot lancé. Suivez sa progression ci-dessus.'); setTimeout(()=>refresh().catch(()=>{}),1500); }
        catch(e){setMessage(e?.response?.data?.detail||e.message||'Impossible de lancer l’autopilot');}
        finally{setBusy(false);}
    };

    const today=dashboard?.today||{}, overnight=dashboard?.overnight||{}, queue=dashboard?.queue||{}, auto=dashboard?.autopilot||{}, scheduler=auto?.scheduler||{}, last=dashboard?.last_run||{};
    const running=last.status==='running';
    const stageLabels={demarrage:'Démarrage',design:'Design',contenu:'Analyse & contenu',generation_html:'Génération HTML',deploiement_vercel:'Déploiement Vercel',email_final:'Email final',termine:'Terminé',erreur:'Erreur'};

    return <section className="space-y-5">
        <div className="rounded-3xl border border-brand/20 bg-gradient-to-br from-brand/10 via-slate-900 to-slate-950 p-5 md:p-6">
            <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
                <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-brand/15 border border-brand/30 flex items-center justify-center"><Bot className="w-6 h-6 text-brand"/></div>
                    <div>
                        <div className="flex gap-2 items-center"><h3 className="text-xl font-extrabold">Autopilot Local Pulse</h3><span className="text-[10px] font-bold px-2 py-1 rounded-full border text-emerald-300 bg-emerald-500/10 border-emerald-500/20">{auto.enabled?'ACTIF':'DÉSACTIVÉ'}</span></div>
                        <p className="text-sm text-slate-400 mt-1">Scan → scoring → site → Vercel → email prêt. L’envoi reste soumis à validation humaine.</p>
                        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-xs text-slate-500">
                            <span className="flex gap-1.5 items-center"><Clock3 className="w-3.5 h-3.5"/>Prochain run : {scheduler?.next_run ? new Date(scheduler.next_run).toLocaleString('fr-FR') : 'à planifier'}</span>
                            <span>{auto.zones_enabled||0} zone(s) active(s)</span><span>Déploiement auto : {auto.auto_deploy?'oui':'non'}</span>
                        </div>
                        {running && <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
                            <div className="flex flex-wrap gap-2 items-center text-sm">
                                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"/>
                                <strong>Run #{last.id}</strong>
                                <span className="text-slate-300">Projet {last.current_index||0}/{last.total_selected||0}</span>
                                {last.current_business_name && <span className="text-white font-semibold">· {last.current_business_name}</span>}
                                <span className="text-amber-300">· {stageLabels[last.current_stage]||last.current_stage||'En cours'}</span>
                            </div>
                            {last.heartbeat_at && <p className="text-[10px] text-slate-500 mt-1">Dernière activité : {new Date(last.heartbeat_at).toLocaleTimeString('fr-FR')}</p>}
                        </div>}
                    </div>
                </div>
                <div className="flex gap-2"><button onClick={refresh} className="p-3 rounded-xl border border-white/10 bg-white/5"><RefreshCw className="w-4 h-4"/></button><button onClick={runNow} disabled={busy||zones.filter(z=>z.enabled).length===0||running} className="px-4 py-3 rounded-xl bg-brand disabled:opacity-40 font-bold text-sm flex gap-2 items-center"><Play className="w-4 h-4"/>Lancer maintenant</button></div>
            </div>
        </div>

        <div>
            <div className="flex items-center justify-between mb-3"><div><h4 className="font-bold">Cette nuit</h4><p className="text-xs text-slate-500">Cliquez sur une étape pour voir les projets.</p></div><span className="text-xs text-slate-500">Dernier run #{last.id||'—'} · {last.status||'—'}</span></div>
            <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
                <Metric icon={Radar} label="Scannés" value={overnight.businesses_scanned} tone="text-sky-400" onClick={()=>openList('scanned','overnight','Commerces scannés cette nuit')}/>
                <Metric icon={Radar} label="Opportunités" value={overnight.opportunities_selected} tone="text-amber-400" onClick={()=>openList('opportunities','overnight','Opportunités sélectionnées')}/>
                <Metric icon={Globe2} label="Sites générés" value={overnight.sites_generated} tone="text-violet-400" onClick={()=>openList('generated','overnight','Sites générés')}/>
                <Metric icon={Rocket} label="Vercel" value={overnight.sites_deployed} tone="text-emerald-400" onClick={()=>openList('deployed','overnight','Sites déployés sur Vercel')}/>
                <Metric icon={Mail} label="Emails prêts" value={overnight.emails_ready} tone="text-brand" onClick={()=>openList('emails','overnight','Emails prêts')}/>
                <Metric icon={AlertTriangle} label="Erreurs" value={overnight.errors} tone="text-rose-400" onClick={()=>openList('errors','overnight','Projets en erreur')}/>
            </div>
        </div>

        <div><h4 className="font-bold mb-3">Aujourd’hui</h4><div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Metric icon={Radar} label="Scannés" value={today.businesses_scanned} tone="text-sky-400" onClick={()=>openList('scanned','today','Scannés aujourd’hui')}/>
            <Metric icon={Globe2} label="Sites générés" value={today.sites_generated} tone="text-violet-400" onClick={()=>openList('generated','today','Sites générés aujourd’hui')}/>
            <Metric icon={Mail} label="Emails prêts aujourd’hui" value={today.emails_ready} tone="text-brand" onClick={()=>openList('emails','today','Emails prêts aujourd’hui')}/>
            <Metric icon={Mail} label="File prête totale" value={queue.emails_ready_total} hint={`${queue.emails_missing_recipient||0} sans destinataire vérifié`} tone="text-emerald-400" onClick={()=>openList('emails','today','Emails prêts')}/>
        </div></div>

        <div className="glass rounded-2xl border border-white/10 overflow-hidden">
            <div className="p-5 border-b border-white/10"><h4 className="font-bold">Zones de prospection automatique</h4><p className="text-xs text-slate-500 mt-1">Une fois configurées, ces zones sont scannées chaque nuit sans intervention.</p></div>
            <div className="p-4 grid grid-cols-1 xl:grid-cols-[1fr_150px_170px_150px_auto] gap-3 border-b border-white/10 items-end">
                <div><label className="block text-[11px] font-bold uppercase text-slate-400 mb-2">Ville ou code postal</label><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ex. Trappes ou 78190" className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm"/></div>
                <div><label className="block text-[11px] font-bold uppercase text-slate-400 mb-2">Rayon du scan</label><input type="number" value={radius} onChange={e=>setRadius(e.target.value)} className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm"/><p className="text-[10px] text-slate-600 mt-1">1000 = 1 km</p></div>
                <div><label className="block text-[11px] font-bold uppercase text-slate-400 mb-2">Score minimum</label><input type="number" value={minScore} onChange={e=>setMinScore(e.target.value)} className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm"/><p className="text-[10px] text-slate-600 mt-1">Opportunity Score /100</p></div>
                <div><label className="block text-[11px] font-bold uppercase text-slate-400 mb-2">Sites max / nuit</label><input type="number" value={maxSites} onChange={e=>setMaxSites(e.target.value)} className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm"/><p className="text-[10px] text-slate-600 mt-1">Par zone et par run</p></div>
                <button onClick={addZone} disabled={busy||!query.trim()} className="rounded-xl bg-white/10 border border-white/10 px-4 py-2.5 text-sm font-bold flex justify-center gap-2"><Plus className="w-4 h-4"/>Ajouter</button>
            </div>
            <div className="divide-y divide-white/5">{zones.length===0?<div className="p-6 text-sm text-slate-500">Ajoutez au moins une ville.</div>:zones.map(z=><div key={z.id} className="p-4 flex items-center gap-3"><button onClick={()=>toggleZone(z)}>{z.enabled?<ToggleRight className="w-7 h-7 text-emerald-400"/>:<ToggleLeft className="w-7 h-7 text-slate-500"/>}</button><div className="flex-1"><p className="font-semibold text-sm">{z.name}</p><p className="text-[11px] text-slate-500">rayon {z.radius} m · score ≥ {z.min_opportunity_score} · max {z.max_sites_per_run}</p></div><button onClick={()=>removeZone(z)} className="text-slate-500 hover:text-rose-400 p-2"><Trash2 className="w-4 h-4"/></button></div>)}</div>
        </div>
        {message&&<div className="text-sm bg-white/5 border border-white/10 rounded-xl px-4 py-3">{message}</div>}
        {drawer&&<ProjectDrawer title={drawer.title} projects={projects} loading={listLoading} onClose={()=>setDrawer(null)} onOpenProject={onOpenProject}/>}
    </section>;
}
export default AutopilotPanel;
