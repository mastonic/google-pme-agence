import React, { useEffect, useState } from 'react';
import { Check, Zap, Star, Crown, TrendingUp, Users, DollarSign } from 'lucide-react';
import axios from 'axios';

const PLANS = [
    {
        slug: 'starter',
        name: 'Starter',
        price: 49,
        icon: Zap,
        color: 'text-blue-400',
        borderColor: 'border-blue-500/30',
        bgColor: 'bg-blue-500/10',
        badgeBg: 'bg-blue-500/20',
        features: [
            'Site vitrine 5 pages',
            'Hébergement inclus',
            'SSL',
            'Mise à jour mensuelle',
        ],
        isPopular: false,
    },
    {
        slug: 'pro',
        name: 'Pro',
        price: 149,
        icon: Star,
        color: 'text-brand',
        borderColor: 'border-brand/40',
        bgColor: 'bg-brand/10',
        badgeBg: 'bg-brand/20',
        features: [
            'Tout Starter',
            'SEO local',
            'Fiche Google optimisée',
            'Rapport mensuel',
        ],
        isPopular: true,
    },
    {
        slug: 'elite',
        name: 'Elite',
        price: 299,
        icon: Crown,
        color: 'text-amber-400',
        borderColor: 'border-amber-500/30',
        bgColor: 'bg-amber-500/10',
        badgeBg: 'bg-amber-500/20',
        features: [
            'Tout Pro',
            'Blog SEO auto',
            'Avis Google sync',
            'Support prioritaire',
            'Domaine personnalisé',
        ],
        isPopular: false,
    },
];

function PricingView() {
    const [kpis, setKpis] = useState(null);

    useEffect(() => {
        axios.get('/admin/kpis')
            .then(r => setKpis(r.data))
            .catch(() => {});
    }, []);

    return (
        <div
            className="w-full h-full bg-slate-900 overflow-y-auto p-8"
            style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,.1) transparent' }}
        >
            <div className="max-w-5xl mx-auto">

                {/* Header */}
                <div className="mb-10 text-center">
                    <h2 className="text-4xl font-extrabold tracking-tight text-white mb-3">
                        Offres &amp; Prix
                    </h2>
                    <p className="text-slate-400 text-lg">
                        Des sites professionnels pour les commerces locaux, avec tout ce qu'il faut.
                    </p>
                </div>

                {/* MRR Stats (if available) */}
                {kpis && (
                    <div className="grid grid-cols-3 gap-4 mb-10">
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

                {/* Plans grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {PLANS.map((plan) => {
                        const Icon = plan.icon;
                        return (
                            <div
                                key={plan.slug}
                                className={`relative flex flex-col rounded-2xl border p-6 transition-all ${plan.borderColor} ${plan.bgColor} ${
                                    plan.isPopular ? 'ring-2 ring-brand/50 scale-[1.02]' : ''
                                }`}
                            >
                                {plan.isPopular && (
                                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-brand text-white text-xs font-bold uppercase tracking-wider px-4 py-1 rounded-full shadow-lg shadow-brand/30">
                                        Le plus populaire
                                    </div>
                                )}

                                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-5 ${plan.badgeBg} border ${plan.borderColor}`}>
                                    <Icon className={`w-6 h-6 ${plan.color}`} />
                                </div>

                                <h3 className={`text-xl font-bold ${plan.color} mb-1`}>{plan.name}</h3>
                                <div className="mb-5 flex items-end gap-1">
                                    <span className="text-4xl font-extrabold text-white">{plan.price}€</span>
                                    <span className="text-slate-400 text-sm mb-1">/mois</span>
                                </div>

                                <ul className="flex-1 space-y-3 mb-6">
                                    {plan.features.map((f) => (
                                        <li key={f} className="flex items-start gap-2.5 text-sm text-slate-300">
                                            <span className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded-full ${plan.badgeBg} flex items-center justify-center`}>
                                                <Check className={`w-3 h-3 ${plan.color}`} />
                                            </span>
                                            {f}
                                        </li>
                                    ))}
                                </ul>

                                <div className={`py-2.5 text-center rounded-xl font-bold text-sm ${plan.badgeBg} ${plan.color} border ${plan.borderColor}`}>
                                    {plan.price}€ / mois · Sans engagement
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Tier breakdown (from KPIs) */}
                {kpis?.tier_breakdown && (
                    <div className="mt-10 glass p-6 rounded-2xl border border-white/10">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Répartition des abonnés</h3>
                        <div className="grid grid-cols-4 gap-4">
                            {Object.entries(kpis.tier_breakdown).map(([tier, count]) => {
                                const plan = PLANS.find(p => p.slug === tier);
                                return (
                                    <div key={tier} className="text-center">
                                        <p className={`text-2xl font-extrabold ${plan?.color || 'text-slate-400'}`}>{count}</p>
                                        <p className="text-xs text-slate-500 capitalize mt-0.5">{tier}</p>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                <p className="mt-8 text-center text-xs text-slate-600">
                    Paiement sécurisé par Stripe · Sans engagement · Résiliable à tout moment
                </p>
            </div>
        </div>
    );
}

export default PricingView;
