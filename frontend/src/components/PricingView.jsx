import React, { useEffect, useState } from 'react';
import { Check, X, Zap, Star, Crown, TrendingUp, Users, DollarSign, Bot } from 'lucide-react';
import axios from 'axios';

const PLAN_STYLE = {
    starter: { icon: Zap, color: 'text-blue-400', borderColor: 'border-blue-500/30', bgColor: 'bg-blue-500/10', badgeBg: 'bg-blue-500/20' },
    pro: { icon: Star, color: 'text-brand', borderColor: 'border-brand/40', bgColor: 'bg-brand/10', badgeBg: 'bg-brand/20' },
    elite: { icon: Crown, color: 'text-amber-400', borderColor: 'border-amber-500/30', bgColor: 'bg-amber-500/10', badgeBg: 'bg-amber-500/20' },
};

function PricingView() {
    const [kpis, setKpis] = useState(null);
    const [plans, setPlans] = useState([]);

    useEffect(() => {
        axios.get('/admin/kpis').then(r => setKpis(r.data)).catch(() => {});
        axios.get('/pricing-page')
            .then(r => setPlans(Array.isArray(r.data?.plans) ? r.data.plans : []))
            .catch(() => setPlans([]));
    }, []);

    return (
        <div className="w-full h-full bg-slate-900 overflow-y-auto p-4 md:p-8">
            <div className="max-w-6xl mx-auto">
                <div className="mb-10 text-center">
                    <h2 className="text-4xl font-extrabold tracking-tight text-white mb-3">Offres &amp; services</h2>
                    <p className="text-slate-400 text-lg">Chaque formule correspond à un niveau de service réellement activé pour le client.</p>
                </div>

                {kpis && (
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
                        {[
                            { label: 'MRR actuel', value: `${kpis.mrr.toLocaleString('fr-FR')} €`, icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
                            { label: 'Clients actifs', value: kpis.total_active_clients, icon: Users, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
                            { label: 'Croissance MRR', value: `+${kpis.mrr_growth_pct}%`, icon: TrendingUp, color: 'text-brand', bg: 'bg-brand/10', border: 'border-brand/20' },
                        ].map(({ label, value, icon: Icon, color, bg, border }) => (
                            <div key={label} className={`glass p-5 rounded-2xl border ${border} ${bg} flex items-center gap-4`}>
                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${bg} border ${border}`}>
                                    <Icon className={`w-5 h-5 ${color}`} />
                                </div>
                                <div>
                                    <p className={`text-2xl font-extrabold ${color}`}>{value}</p>
                                    <p className="text-xs text-slate-400 uppercase tracking-wider font-bold mt-0.5">{label}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                    {plans.map((plan) => {
                        const style = PLAN_STYLE[plan.slug] || PLAN_STYLE.starter;
                        const Icon = style.icon;
                        return (
                            <div
                                key={plan.slug}
                                className={`relative flex flex-col rounded-2xl border p-6 ${style.borderColor} ${style.bgColor} ${plan.is_popular ? 'ring-2 ring-brand/50' : ''}`}
                            >
                                {plan.is_popular && (
                                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-brand text-white text-xs font-bold uppercase tracking-wider px-4 py-1 rounded-full">
                                        Le plus populaire
                                    </div>
                                )}

                                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-5 ${style.badgeBg} border ${style.borderColor}`}>
                                    <Icon className={`w-6 h-6 ${style.color}`} />
                                </div>

                                <h3 className={`text-xl font-bold ${style.color}`}>{plan.name}</h3>
                                <p className="text-sm font-semibold text-white mt-1">{plan.positioning}</p>
                                <p className="text-sm text-slate-400 mt-2 min-h-[42px]">{plan.summary}</p>

                                <div className="my-5 flex items-end gap-1">
                                    <span className="text-4xl font-extrabold text-white">{plan.price}€</span>
                                    <span className="text-slate-400 text-sm mb-1">/mois</span>
                                </div>

                                <div className="space-y-3 flex-1">
                                    {(plan.features || []).map((f) => (
                                        <div key={f} className="flex items-start gap-2.5 text-sm text-slate-200">
                                            <span className={`mt-0.5 w-5 h-5 rounded-full ${style.badgeBg} flex items-center justify-center shrink-0`}>
                                                <Check className={`w-3 h-3 ${style.color}`} />
                                            </span>
                                            <span>{f}</span>
                                        </div>
                                    ))}
                                </div>

                                {(plan.agent_teams || []).length > 0 && (
                                    <div className="mt-5 rounded-xl bg-slate-950/40 border border-white/10 p-4">
                                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                                            <Bot className="w-4 h-4" /> Équipes d’agents incluses
                                        </div>
                                        <p className="text-sm text-slate-300">{plan.agent_teams.join(' · ')}</p>
                                    </div>
                                )}

                                {(plan.not_included || []).length > 0 && (
                                    <details className="mt-4 text-xs text-slate-500">
                                        <summary className="cursor-pointer">Non inclus dans cette formule</summary>
                                        <div className="mt-2 space-y-1.5">
                                            {plan.not_included.map(f => (
                                                <div key={f} className="flex items-start gap-2">
                                                    <X className="w-3.5 h-3.5 mt-0.5" /> {f}
                                                </div>
                                            ))}
                                        </div>
                                    </details>
                                )}

                                <div className={`mt-6 py-2.5 text-center rounded-xl font-bold text-sm ${style.badgeBg} ${style.color} border ${style.borderColor}`}>
                                    {plan.price}€ / mois · Sans engagement
                                </div>
                            </div>
                        );
                    })}
                </div>

                <p className="mt-8 text-center text-xs text-slate-600">
                    Paiement sécurisé par Stripe · Sans engagement · Résiliable à tout moment
                </p>
            </div>
        </div>
    );
}

export default PricingView;
