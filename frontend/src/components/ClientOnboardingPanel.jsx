import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Check, CheckCircle2, Loader2, Rocket, UserCheck } from 'lucide-react';

export default function ClientOnboardingPanel({ business, onUpdate }) {
    const [plans, setPlans] = useState([]);
    const [plan, setPlan] = useState(business?.plan_tier && business.plan_tier !== 'free' ? business.plan_tier : 'pro');
    const [working, setWorking] = useState(false);
    const [checklist, setChecklist] = useState(business?.onboarding_checklist || []);
    const isClient = business?.crm_stage === 'won';

    useEffect(() => {
        axios.get(`/pricing-page?business_id=${encodeURIComponent(business.id)}`)
            .then(r => setPlans(r.data?.plans || []))
            .catch(() => {});
    }, [business.id]);

    useEffect(() => {
        setChecklist(business?.onboarding_checklist || []);
    }, [business?.onboarding_checklist]);

    const convert = async () => {
        setWorking(true);
        try {
            const r = await axios.post(`/businesses/${business.id}/convert-client`, { plan_tier: plan });
            setChecklist(r.data?.onboarding_checklist || []);
            if (onUpdate) onUpdate(business.id, r.data);
        } catch (e) {
            console.error('Convert client error:', e);
        } finally {
            setWorking(false);
        }
    };

    const toggle = async (item) => {
        setWorking(true);
        try {
            const r = await axios.post(`/businesses/${business.id}/onboarding/${item.key}`, { done: !item.done });
            setChecklist(r.data?.onboarding_checklist || []);
            if (onUpdate) onUpdate(business.id, r.data);
        } catch (e) {
            console.error('Onboarding update error:', e);
        } finally {
            setWorking(false);
        }
    };

    if (!isClient) {
        return (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.04] p-4">
                <div className="flex items-center gap-2 mb-3">
                    <UserCheck className="w-4 h-4 text-emerald-400" />
                    <div>
                        <p className="text-sm font-bold text-white">Le prospect a accepté ?</p>
                        <p className="text-[10px] text-slate-500">Passe-le en client et lance l'onboarding sans marquer le paiement comme confirmé.</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <select value={plan} onChange={e => setPlan(e.target.value)}
                        className="flex-1 bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-xs text-white">
                        {(plans || []).map(p => (
                            <option key={p.slug} value={p.slug}>{p.name} — {p.price}€/mois</option>
                        ))}
                    </select>
                    <button onClick={convert} disabled={working}
                        className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-2 rounded-lg text-xs font-bold disabled:opacity-50">
                        {working ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Rocket className="w-3.5 h-3.5" />}
                        Convertir
                    </button>
                </div>
            </div>
        );
    }

    const done = checklist.filter(x => x.done).length;
    const total = checklist.length || 1;
    const pct = Math.round(done / total * 100);

    return (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.04] p-4">
            <div className="flex items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <div>
                        <p className="text-sm font-bold text-white">Onboarding client</p>
                        <p className="text-[10px] text-slate-500">{business.plan_tier} · paiement {business.subscription_status || 'pending'}</p>
                    </div>
                </div>
                <span className="text-xs font-bold text-emerald-400">{pct}%</span>
            </div>
            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden mb-3">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${pct}%` }} />
            </div>
            <div className="space-y-1.5">
                {checklist.map(item => (
                    <button key={item.key} onClick={() => toggle(item)} disabled={working}
                        className="w-full flex items-center gap-2 text-left rounded-lg hover:bg-white/5 px-2 py-1.5 transition-colors">
                        <span className={`w-4 h-4 rounded border flex items-center justify-center ${item.done ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-slate-600'}`}>
                            {item.done && <Check className="w-3 h-3" />}
                        </span>
                        <span className={`text-[11px] ${item.done ? 'text-slate-500 line-through' : 'text-slate-300'}`}>{item.label}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}
