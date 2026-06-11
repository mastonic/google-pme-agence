import React, { useState, useEffect, useRef } from 'react';
import { Bot, Loader2, CheckCircle2, CircleDashed, AlertCircle, Activity, Zap, BarChart3, Radio } from 'lucide-react';
import axios from 'axios';

const AGENT_COLORS = {
    "Le Designer":     { bg: 'bg-violet-500/10', border: 'border-violet-500/30', text: 'text-violet-400' },
    "L'Éclaireur":     { bg: 'bg-sky-500/10',    border: 'border-sky-500/30',    text: 'text-sky-400' },
    "Le Stratège":     { bg: 'bg-amber-500/10',  border: 'border-amber-500/30',  text: 'text-amber-400' },
    "Visions Artist":  { bg: 'bg-pink-500/10',   border: 'border-pink-500/30',   text: 'text-pink-400' },
    "L'Ingénieur":     { bg: 'bg-emerald-500/10',border: 'border-emerald-500/30',text: 'text-emerald-400' },
    "Le Closer":       { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400' },
    "Système":         { bg: 'bg-slate-500/10',  border: 'border-slate-500/30',  text: 'text-slate-400' },
};

function AgentStream({ businessId, businessName, status, onStatusChange }) {
    const [logs, setLogs]           = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isFinished, setIsFinished]   = useState(false);
    const sinceRef   = useRef(0);
    const intervalRef = useRef(null);
    const logsEndRef = useRef(null);

    useEffect(() => {
        if (logsEndRef.current) logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    useEffect(() => {
        if (status !== 'processing') return;

        sinceRef.current = 0;
        setIsConnected(true);
        setIsFinished(false);
        setLogs([{ agent: 'Système', message: 'Connexion aux agents...', type: 'system' }]);

        const poll = async () => {
            try {
                const r = await axios.get(`/businesses/${businessId}/logs?since=${sinceRef.current}`);
                const { logs: newLogs, total, finished } = r.data;
                if (newLogs.length > 0) {
                    sinceRef.current = total;
                    setLogs(prev => {
                        const base = prev.length === 1 && prev[0].message === 'Connexion aux agents...' ? [] : prev;
                        return [...base, ...newLogs].slice(-50);
                    });
                }
                if (finished) {
                    setIsConnected(false);
                    setIsFinished(true);
                    clearInterval(intervalRef.current);
                    if (onStatusChange) onStatusChange(businessId);
                }
            } catch { /* network blip */ }
        };

        poll();
        intervalRef.current = setInterval(poll, 2500);

        return () => { clearInterval(intervalRef.current); setIsConnected(false); };
    }, [businessId, status]);

    const colors = AGENT_COLORS["Système"];

    return (
        <div className="glass rounded-2xl overflow-hidden border border-white/10 flex flex-col" style={{ minHeight: '320px', maxHeight: '400px' }}>
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-slate-800/50 border-b border-white/10 flex-shrink-0">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-brand/20 border border-brand/30 flex items-center justify-center font-bold text-sm text-brand">
                        {businessName.charAt(0)}
                    </div>
                    <div>
                        <p className="font-bold text-sm">{businessName}</p>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            {isConnected && !isFinished ? (
                                <>
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                    <span className="text-[10px] text-emerald-400 font-medium">En cours</span>
                                </>
                            ) : isFinished ? (
                                <>
                                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                                    <span className="text-[10px] text-emerald-400 font-medium">Terminé</span>
                                </>
                            ) : (
                                <>
                                    <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                                    <span className="text-[10px] text-slate-500">En attente</span>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Log stream */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2 font-mono text-xs custom-scrollbar min-h-0"
                 style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,.1) transparent' }}>
                {logs.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-slate-600 text-xs gap-2">
                        <CircleDashed className="w-4 h-4" />
                        <span>En attente du flux d'activité...</span>
                    </div>
                ) : (
                    logs.map((log, i) => {
                        const c = AGENT_COLORS[log.agent] || colors;
                        return (
                            <div key={i} className={`flex flex-col ${log.type === 'system' || log.type === 'error' ? 'items-center' : 'items-start'}`}>
                                {log.type === 'chat' && (
                                    <span className={`text-[9px] font-bold mb-0.5 ${c.text}`}>{log.agent} :</span>
                                )}
                                <span className={`break-words whitespace-pre-wrap max-w-full leading-relaxed ${
                                    log.type === 'system' ? 'text-slate-500 italic' :
                                    log.type === 'error'  ? 'text-rose-400' :
                                    `${c.bg} ${c.border} border px-2 py-1.5 rounded-lg rounded-tl-none text-slate-200`
                                }`}>
                                    {log.message}
                                </span>
                            </div>
                        );
                    })
                )}
                {isConnected && (
                    <div className="flex items-center gap-1.5 text-slate-500 italic py-1">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>Analyse en cours...</span>
                    </div>
                )}
                <div ref={logsEndRef} />
            </div>
        </div>
    );
}

function LiveCockpit({ businesses, onRefresh }) {
    const [kpis, setKpis] = useState(null);
    const [tick, setTick] = useState(0);

    const processing = businesses.filter(b => b.status === 'processing');
    const pending    = businesses.filter(b => b.status === 'pending_validation');
    const completed  = businesses.filter(b => b.status === 'completed');
    const errors     = businesses.filter(b => b.status === 'error');

    useEffect(() => {
        axios.get('/admin/kpis').then(r => setKpis(r.data)).catch(() => {});
    }, [tick]);

    // Auto-refresh KPIs every 15 s
    useEffect(() => {
        const id = setInterval(() => setTick(t => t + 1), 15000);
        return () => clearInterval(id);
    }, []);

    const handleStatusChange = () => {
        if (onRefresh) onRefresh();
        setTick(t => t + 1);
    };

    return (
        <div className="w-full h-full bg-slate-900 overflow-y-auto p-8"
             style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,.1) transparent' }}>
            <div className="max-w-7xl mx-auto space-y-8">

                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                            <Activity className="w-7 h-7 text-brand" />
                            Live Cockpit
                        </h2>
                        <p className="text-slate-400 mt-1 text-sm">Supervision en temps réel des agents IA</p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800 border border-white/10 px-3 py-1.5 rounded-full">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        Mise à jour toutes les 15s
                    </div>
                </div>

                {/* KPI bar */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                        { label: 'En traitement',   value: processing.length, color: 'text-amber-400',  icon: Loader2,       extra: 'animate-spin' },
                        { label: 'À valider',        value: pending.length,   color: 'text-blue-400',   icon: CircleDashed,  extra: '' },
                        { label: 'Déployés',         value: completed.length, color: 'text-emerald-400',icon: CheckCircle2,  extra: '' },
                        { label: 'Erreurs',          value: errors.length,    color: 'text-rose-400',   icon: AlertCircle,   extra: '' },
                    ].map(({ label, value, color, icon: Icon, extra }) => (
                        <div key={label} className="glass p-5 rounded-2xl flex items-center gap-4">
                            <Icon className={`w-6 h-6 ${color} ${extra}`} />
                            <div>
                                <p className={`text-2xl font-bold ${color}`}>{value}</p>
                                <p className="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5">{label}</p>
                            </div>
                        </div>
                    ))}
                </div>

                {/* MRR row (if available) */}
                {kpis && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                            { label: 'MRR',            value: `${kpis.mrr.toFixed(0)} €`,     color: 'text-brand' },
                            { label: 'Clients actifs', value: kpis.total_active_clients,       color: 'text-white' },
                            { label: 'Scannés total',  value: kpis.total_scanned,              color: 'text-slate-300' },
                            { label: 'LTV / CAC',      value: `×${kpis.ltv_cac_ratio}`,       color: 'text-emerald-400' },
                        ].map(({ label, value, color }) => (
                            <div key={label} className="glass p-4 rounded-2xl text-center border border-white/5">
                                <p className={`text-xl font-bold ${color}`}>{value}</p>
                                <p className="text-[10px] text-slate-500 uppercase tracking-wider mt-1">{label}</p>
                            </div>
                        ))}
                    </div>
                )}

                {/* Active streams */}
                {processing.length > 0 ? (
                    <div>
                        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                            <Zap className="w-4 h-4 text-amber-400" />
                            Agents en cours ({processing.length})
                        </h3>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {processing.map(biz => (
                                <AgentStream
                                    key={biz.id}
                                    businessId={biz.id}
                                    businessName={biz.name}
                                    status={biz.status}
                                    onStatusChange={handleStatusChange}
                                />
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="border border-white/10 bg-slate-800/50 p-12 rounded-2xl text-center">
                        <Bot className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-lg font-bold text-white mb-2">Aucun agent actif</h3>
                        <p className="text-slate-400 text-sm">
                            Sélectionnez un commerce et cliquez sur <strong className="text-white">✨ Créer les Actifs Numériques</strong> pour lancer les agents.
                        </p>
                    </div>
                )}

                {/* Recent pipeline */}
                {(pending.length > 0 || errors.length > 0) && (
                    <div>
                        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                            <BarChart3 className="w-4 h-4 text-slate-400" />
                            Pipeline récent
                        </h3>
                        <div className="space-y-3">
                            {[...pending, ...errors].map(biz => (
                                <div key={biz.id} className="glass p-4 rounded-xl flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${biz.status === 'error' ? 'bg-rose-400' : 'bg-blue-400'}`} />
                                        <span className="font-medium text-sm">{biz.name}</span>
                                        <span className="text-xs text-slate-500">{biz.address}</span>
                                    </div>
                                    <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                                        biz.status === 'error'
                                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                                            : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                    }`}>
                                        {biz.status === 'error' ? '❌ Erreur' : '👁️ À valider'}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default LiveCockpit;
