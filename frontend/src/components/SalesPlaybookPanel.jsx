import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import {
    AlertTriangle, ArrowRight, Ban, Check, Copy, Loader2,
    Mail, Phone, Play, RefreshCw, Target,
} from 'lucide-react';

const STATUS = {
    strong: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    weak: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
};

export default function SalesPlaybookPanel({ business, onUpdate }) {
    const [playbook, setPlaybook] = useState(null);
    const [loading, setLoading] = useState(true);
    const [working, setWorking] = useState(false);
    const [copied, setCopied] = useState(null);
    const businessId = business?.id;

    const load = async () => {
        if (!businessId) return;
        setLoading(true);
        try {
            const r = await axios.get(`/businesses/${businessId}/sales-playbook`);
            setPlaybook(r.data);
        } catch (e) {
            console.error('Sales playbook error:', e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, [businessId]);

    const sequence = playbook?.sequence || [];
    const currentStep = playbook?.outreach_step || 0;
    const status = playbook?.outreach_status || 'not_started';
    const next = playbook?.next_action || {};
    const snapshot = playbook?.snapshot || {};

    const dueText = useMemo(() => {
        if (!next?.due_at) return 'Dès que possible';
        const d = new Date(next.due_at);
        if (Number.isNaN(d.getTime())) return 'Dès que possible';
        return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }, [next?.due_at]);

    const start = async () => {
        setWorking(true);
        try {
            const r = await axios.post(`/businesses/${businessId}/outreach/start`);
            if (onUpdate) onUpdate(businessId, r.data);
            await load();
        } catch (e) {
            console.error('Start outreach error:', e);
        } finally {
            setWorking(false);
        }
    };

    const complete = async (index) => {
        setWorking(true);
        try {
            const r = await axios.post(`/businesses/${businessId}/outreach/complete-step`, { index });
            if (onUpdate) onUpdate(businessId, r.data);
            await load();
        } catch (e) {
            console.error('Complete outreach step error:', e);
        } finally {
            setWorking(false);
        }
    };

    const stop = async () => {
        if (!window.confirm('Marquer ce prospect comme « ne pas contacter » ?')) return;
        setWorking(true);
        try {
            const r = await axios.post(`/businesses/${businessId}/outreach/opt-out`);
            if (onUpdate) onUpdate(businessId, r.data);
            await load();
        } catch (e) {
            console.error('Opt-out error:', e);
        } finally {
            setWorking(false);
        }
    };

    const copy = async (step) => {
        const text = step.subject
            ? `Objet : ${step.subject}\n\n${step.content}`
            : step.content;
        await navigator.clipboard.writeText(text || '');
        setCopied(step.index);
        setTimeout(() => setCopied(null), 1800);
    };

    if (loading) {
        return (
            <div className="rounded-2xl border border-white/10 bg-slate-800/50 p-5 flex items-center gap-2 text-sm text-slate-400">
                <Loader2 className="w-4 h-4 animate-spin text-brand" />
                Préparation du plan commercial…
            </div>
        );
    }

    if (!playbook) {
        return (
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-5 text-sm text-rose-300">
                Plan commercial indisponible.
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Next action */}
            <div className="rounded-2xl border border-brand/20 bg-brand/5 p-4">
                <div className="flex items-start justify-between gap-3">
                    <div>
                        <p className="text-[10px] uppercase tracking-widest font-bold text-brand">Prochaine action</p>
                        <h3 className="font-bold text-white mt-1">{next.label || 'Revoir le prospect'}</h3>
                        <p className="text-xs text-slate-400 mt-1">{next.reason}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                        <p className="text-xs font-bold text-white">{dueText}</p>
                        <p className="text-[10px] text-slate-500">échéance</p>
                    </div>
                </div>
            </div>

            {/* Before / after */}
            <div className="rounded-2xl border border-white/10 bg-slate-800/50 p-4">
                <div className="flex items-center gap-2 mb-3">
                    <Target className="w-4 h-4 text-brand" />
                    <div>
                        <p className="font-bold text-sm">{snapshot.headline || 'Avant / Après'}</p>
                        <p className="text-[10px] text-slate-500">
                            Opportunité {snapshot.opportunity_score || 0}/100 · Digital {snapshot.digital_health_score || 0}/100
                        </p>
                    </div>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed mb-4">{snapshot.hook}</p>

                <div className="grid md:grid-cols-2 gap-3">
                    <div className="rounded-xl bg-slate-900/60 border border-white/5 p-3">
                        <p className="text-[10px] uppercase tracking-wider font-bold text-slate-500 mb-2">Aujourd'hui</p>
                        <div className="space-y-2">
                            {(snapshot.current || []).map((item, i) => (
                                <div key={i} className="flex items-center justify-between gap-2">
                                    <span className="text-xs text-slate-400">{item.label}</span>
                                    <span className={`text-[10px] font-bold px-2 py-1 rounded-lg border ${STATUS[item.status] || STATUS.medium}`}>
                                        {item.value}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="rounded-xl bg-slate-900/60 border border-white/5 p-3">
                        <p className="text-[10px] uppercase tracking-wider font-bold text-emerald-500 mb-2">Ce que la démo corrige</p>
                        <div className="space-y-2">
                            {(snapshot.proposed || []).map((item, i) => (
                                <div key={i} className="flex gap-2 text-xs">
                                    <ArrowRight className="w-3 h-3 text-emerald-400 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <span className="font-semibold text-slate-200">{item.label}</span>
                                        <span className="text-slate-500"> · {item.result}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {(snapshot.talking_points || []).length > 0 && (
                    <div className="mt-3 border-t border-white/5 pt-3">
                        <p className="text-[10px] uppercase tracking-wider font-bold text-slate-500 mb-2">Angle d'appel</p>
                        <div className="space-y-1">
                            {snapshot.talking_points.map((x, i) => (
                                <p key={i} className="text-[11px] text-slate-400">• {x}</p>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Sequence */}
            <div className="rounded-2xl border border-white/10 bg-slate-800/50 p-4">
                <div className="flex items-center justify-between gap-3 mb-3">
                    <div>
                        <p className="font-bold text-sm">Séquence de prospection</p>
                        <p className="text-[10px] text-slate-500">J0 · J2 · J5 · J10 — validation humaine avant chaque contact</p>
                    </div>
                    {status === 'not_started' && !playbook.prospecting_opt_out && (
                        <button onClick={start} disabled={working || !business?.generated_html}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand text-white text-xs font-bold disabled:opacity-40">
                            {working ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                            Démarrer
                        </button>
                    )}
                    {status !== 'not_started' && (
                        <button onClick={load} disabled={working}
                            className="p-2 rounded-lg border border-white/10 text-slate-400 hover:text-white">
                            <RefreshCw className="w-3.5 h-3.5" />
                        </button>
                    )}
                </div>

                {!business?.generated_html && (
                    <div className="mb-3 flex gap-2 text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-xl p-3">
                        <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                        La démo doit être générée avant de démarrer la séquence.
                    </div>
                )}

                <div className="space-y-2">
                    {sequence.map((step) => {
                        const done = status !== 'not_started' && step.index < currentStep;
                        const active = status === 'active' && step.index === currentStep;
                        const Icon = step.channel === 'phone' ? Phone : Mail;
                        return (
                            <div key={step.index}
                                className={`rounded-xl border p-3 ${done ? 'border-emerald-500/20 bg-emerald-500/5' : active ? 'border-brand/30 bg-brand/5' : 'border-white/5 bg-slate-900/40'}`}>
                                <div className="flex items-start gap-3">
                                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${done ? 'bg-emerald-500/10 text-emerald-400' : 'bg-white/5 text-slate-400'}`}>
                                        {done ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <p className="text-xs font-bold text-white">J+{step.day_offset} · {step.title}</p>
                                            {active && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-brand/10 text-brand font-bold">À faire</span>}
                                        </div>
                                        {step.subject && <p className="text-[10px] text-slate-500 mt-1">Objet : {step.subject}</p>}
                                        <p className="text-[11px] text-slate-400 mt-1 line-clamp-3 whitespace-pre-line">{step.content}</p>
                                        <p className="text-[10px] text-slate-600 mt-1">{step.why}</p>
                                    </div>
                                    <div className="flex flex-col gap-1.5">
                                        <button onClick={() => copy(step)}
                                            className="p-2 rounded-lg border border-white/10 text-slate-400 hover:text-white"
                                            title="Copier">
                                            {copied === step.index ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                                        </button>
                                        {active && (
                                            <button onClick={() => complete(step.index)} disabled={working}
                                                className="px-2 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold disabled:opacity-50">
                                                Fait
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {!playbook.prospecting_opt_out && (
                    <div className="mt-3 pt-3 border-t border-white/5 flex justify-end">
                        <button onClick={stop} disabled={working}
                            className="flex items-center gap-1.5 text-[10px] text-slate-500 hover:text-rose-400">
                            <Ban className="w-3 h-3" />
                            Ne plus contacter
                        </button>
                    </div>
                )}
                {playbook.prospecting_opt_out && (
                    <div className="mt-3 flex items-center gap-2 text-xs text-rose-400">
                        <Ban className="w-3.5 h-3.5" />
                        Prospect marqué « ne pas contacter ».
                    </div>
                )}
            </div>
        </div>
    );
}
