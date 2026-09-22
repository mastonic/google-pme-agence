import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Activity, ArrowRight, CheckCircle2, Eye, Flame, Loader2,
    RefreshCw, Target, TrendingUp, Users, Zap,
} from 'lucide-react';

const TEMP = {
    hot:  'bg-rose-500/10 border-rose-500/20 text-rose-300',
    warm: 'bg-amber-500/10 border-amber-500/20 text-amber-300',
    cool: 'bg-blue-500/10 border-blue-500/20 text-blue-300',
    cold: 'bg-slate-500/10 border-slate-500/20 text-slate-400',
};

export default function BusinessDashboard({ onOpenCrm }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        try {
            const r = await axios.get('/business-dashboard');
            setData(r.data);
        } catch (e) {
            console.error('Business dashboard error:', e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
        const id = setInterval(load, 30000);
        return () => clearInterval(id);
    }, []);

    if (loading) {
        return <div className="w-full h-full flex items-center justify-center bg-slate-900"><Loader2 className="w-8 h-8 animate-spin text-brand" /></div>;
    }

    const k = data?.kpis || {};
    const funnel = data?.funnel || {};
    const maxFunnel = Math.max(1, funnel.prospects || 0);

    const cards = [
        { label: 'Opportunités fortes', value: k.strong_opportunities || 0, icon: Target, color: 'text-brand' },
        { label: 'Prospects chauds', value: k.hot_leads || 0, icon: Flame, color: 'text-rose-400' },
        { label: "Actions aujourd'hui", value: k.actions_due || 0, icon: Zap, color: 'text-amber-400' },
        { label: 'Clients gagnés', value: k.won_clients || 0, icon: CheckCircle2, color: 'text-emerald-400' },
        { label: 'MRR actif', value: `${Number(k.active_mrr || 0).toFixed(0)} €`, icon: TrendingUp, color: 'text-emerald-400' },
        { label: 'MRR pipeline', value: `${Number(k.pipeline_mrr || 0).toFixed(0)} €`, icon: Activity, color: 'text-violet-400' },
        { label: 'Vues des démos', value: k.demo_views || 0, icon: Eye, color: 'text-blue-400' },
        { label: "Clics d'intérêt", value: k.interest_clicks || 0, icon: Flame, color: 'text-rose-400' },
    ];

    const funnelRows = [
        ['Prospects', funnel.prospects || 0],
        ['Contactés', funnel.contacted || 0],
        ['Démo envoyée', funnel.demo_sent || 0],
        ['Négociation', funnel.negotiating || 0],
        ['Clients', funnel.won || 0],
    ];

    return (
        <div className="w-full h-full bg-slate-900 overflow-y-auto p-4 sm:p-6 md:p-8">
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between gap-4">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Pilotage Local Pulse</h2>
                        <p className="text-sm text-slate-400 mt-1">Ce qu'il faut vendre, relancer et convertir maintenant.</p>
                    </div>
                    <button onClick={load} className="p-2.5 rounded-xl border border-white/10 text-slate-400 hover:text-white">
                        <RefreshCw className="w-4 h-4" />
                    </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {cards.map(({ label, value, icon: Icon, color }) => (
                        <div key={label} className="glass p-4 rounded-2xl border border-white/5">
                            <div className="flex items-center justify-between mb-3">
                                <Icon className={`w-5 h-5 ${color}`} />
                                <span className="text-[9px] uppercase tracking-wider text-slate-600">live</span>
                            </div>
                            <p className={`text-2xl font-bold ${color}`}>{value}</p>
                            <p className="text-[10px] text-slate-500 uppercase tracking-wider mt-1">{label}</p>
                        </div>
                    ))}
                </div>

                <div className="grid lg:grid-cols-5 gap-5">
                    <div className="lg:col-span-2 glass rounded-2xl p-5 border border-white/5">
                        <div className="flex items-center gap-2 mb-5">
                            <TrendingUp className="w-4 h-4 text-brand" />
                            <h3 className="font-bold">Tunnel commercial</h3>
                        </div>
                        <div className="space-y-4">
                            {funnelRows.map(([label, value]) => (
                                <div key={label}>
                                    <div className="flex items-center justify-between text-xs mb-1.5">
                                        <span className="text-slate-400">{label}</span>
                                        <span className="font-bold text-white">{value}</span>
                                    </div>
                                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-brand rounded-full transition-all"
                                            style={{ width: `${Math.max(value > 0 ? 4 : 0, Math.min(100, value / maxFunnel * 100))}%` }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="lg:col-span-3 glass rounded-2xl p-5 border border-white/5">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <Flame className="w-4 h-4 text-rose-400" />
                                <h3 className="font-bold">Prospects à surveiller</h3>
                            </div>
                            <button onClick={onOpenCrm} className="text-xs text-brand font-bold hover:underline">Ouvrir le CRM →</button>
                        </div>
                        <div className="space-y-2">
                            {(data?.top_leads || []).length === 0 ? (
                                <p className="text-sm text-slate-500 py-8 text-center">Aucun prospect à afficher pour le moment.</p>
                            ) : data.top_leads.map(lead => (
                                <div key={lead.id} className="rounded-xl border border-white/5 bg-slate-800/50 p-3 flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center font-bold text-sm flex-shrink-0">
                                        {lead.name?.charAt(0) || '?'}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <p className="font-semibold text-sm truncate">{lead.name}</p>
                                            <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${TEMP[lead.lead_temperature] || TEMP.cold}`}>
                                                {lead.lead_temperature === 'hot' ? '🔥 chaud' : lead.lead_temperature}
                                            </span>
                                        </div>
                                        <p className="text-[10px] text-slate-500 mt-1 truncate">{lead.next_action_reason || 'À qualifier'}</p>
                                    </div>
                                    <div className="text-right flex-shrink-0">
                                        <p className="text-sm font-bold text-rose-300">{Math.round(lead.lead_heat_score || 0)}</p>
                                        <p className="text-[9px] text-slate-600">{lead.demo_views || 0} vue(s)</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="glass rounded-2xl p-5 border border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="flex items-start gap-3">
                        <Users className="w-5 h-5 text-brand mt-0.5" />
                        <div>
                            <p className="font-bold text-sm">{k.scanned || 0} entreprises analysées</p>
                            <p className="text-xs text-slate-500 mt-1">
                                {k.demos_ready || 0} démos prêtes · {k.active_clients || 0} clients actifs
                            </p>
                        </div>
                    </div>
                    <button onClick={onOpenCrm}
                        className="flex items-center gap-2 bg-brand hover:bg-brand-dark text-white px-4 py-2 rounded-xl text-sm font-bold">
                        Travailler le pipeline <ArrowRight className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
