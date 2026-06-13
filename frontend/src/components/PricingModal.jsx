import React, { useState } from 'react';
import { X, Check, Loader2, CreditCard, Zap, Star, Crown } from 'lucide-react';
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

function PricingModal({ isOpen, onClose, businessId, businessName }) {
    const [loadingPlan, setLoadingPlan] = useState(null);
    const [error, setError] = useState(null);

    if (!isOpen) return null;

    const handleSubscribe = async (plan) => {
        setLoadingPlan(plan);
        setError(null);
        try {
            const res = await axios.post(
                `/create-checkout-session?business_id=${encodeURIComponent(businessId)}&plan=${plan}`
            );
            if (res.data?.checkout_url) {
                window.location.href = res.data.checkout_url;
            } else {
                setError('URL de paiement introuvable.');
            }
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                err.message ||
                'Erreur lors de la création de la session de paiement.'
            );
        } finally {
            setLoadingPlan(null);
        }
    };

    return (
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            {/* Overlay */}
            <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

            {/* Modal */}
            <div className="relative z-10 w-full max-w-3xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-white/10">
                    <div>
                        <h2 className="text-xl font-bold text-white">Choisir un abonnement</h2>
                        {businessName && (
                            <p className="text-sm text-slate-400 mt-0.5">
                                Pour <span className="text-white font-medium">{businessName}</span>
                            </p>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Error banner */}
                {error && (
                    <div className="mx-6 mt-4 px-4 py-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm rounded-xl">
                        {error}
                    </div>
                )}

                {/* Plans grid */}
                <div className="p-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {PLANS.map((plan) => {
                        const Icon = plan.icon;
                        const isLoading = loadingPlan === plan.slug;
                        return (
                            <div
                                key={plan.slug}
                                className={`relative flex flex-col rounded-2xl border p-5 transition-all ${plan.borderColor} ${plan.bgColor} ${
                                    plan.isPopular ? 'ring-2 ring-brand/50' : ''
                                }`}
                            >
                                {plan.isPopular && (
                                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand text-white text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full shadow-lg shadow-brand/30">
                                        Le plus populaire
                                    </div>
                                )}

                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${plan.bgColor} border ${plan.borderColor}`}>
                                    <Icon className={`w-5 h-5 ${plan.color}`} />
                                </div>

                                <h3 className={`text-lg font-bold ${plan.color} mb-1`}>{plan.name}</h3>
                                <div className="mb-4">
                                    <span className="text-3xl font-extrabold text-white">{plan.price}€</span>
                                    <span className="text-slate-400 text-sm">/mois</span>
                                </div>

                                <ul className="flex-1 space-y-2 mb-5">
                                    {plan.features.map((f) => (
                                        <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                                            <Check className={`w-4 h-4 mt-0.5 flex-shrink-0 ${plan.color}`} />
                                            {f}
                                        </li>
                                    ))}
                                </ul>

                                <button
                                    onClick={() => handleSubscribe(plan.slug)}
                                    disabled={!!loadingPlan}
                                    className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-bold text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed ${
                                        plan.isPopular
                                            ? 'bg-brand hover:bg-brand-dark text-white shadow-lg shadow-brand/30'
                                            : 'bg-white/10 hover:bg-white/20 text-white border border-white/10'
                                    }`}
                                >
                                    {isLoading ? (
                                        <><Loader2 className="w-4 h-4 animate-spin" /> Redirection...</>
                                    ) : (
                                        <><CreditCard className="w-4 h-4" /> S'abonner</>
                                    )}
                                </button>
                            </div>
                        );
                    })}
                </div>

                <p className="pb-5 text-center text-xs text-slate-500">
                    Paiement sécurisé par Stripe · Sans engagement · Résiliable à tout moment
                </p>
            </div>
        </div>
    );
}

export default PricingModal;
