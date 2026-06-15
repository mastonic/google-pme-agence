import React from 'react';

const STATUS_CONFIG = {
    ok:      { bar: 'bg-emerald-500', text: 'text-emerald-400', icon: '✓' },
    partial: { bar: 'bg-amber-500',   text: 'text-amber-400',   icon: '◑' },
    low:     { bar: 'bg-red-500',     text: 'text-red-400',     icon: '▲' },
    missing: { bar: 'bg-slate-600',   text: 'text-slate-400',   icon: '✕' },
};

const PLAN_COLOR = {
    Starter: 'text-blue-400',
    Pro:     'text-purple-400',
    Elite:   'text-amber-400',
};

export default function ScoreBreakdownPanel({ breakdown }) {
    if (!breakdown) return null;
    const { criteria = [], recommendations = [] } = breakdown;

    return (
        <div className="mb-4 rounded-xl border border-white/8 bg-slate-800/60 p-3 space-y-3">
            {/* Criteria bars */}
            <div className="space-y-2">
                {criteria.map((c) => {
                    const cfg = STATUS_CONFIG[c.status] || STATUS_CONFIG.missing;
                    const pct = c.max > 0 ? Math.round((c.pts / c.max) * 100) : 0;
                    return (
                        <div key={c.label}>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-xs text-slate-300 font-medium">{c.label}</span>
                                <span className={`text-xs font-bold ${cfg.text}`}>
                                    {cfg.icon} {c.pts}/{c.max}
                                </span>
                            </div>
                            <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all ${cfg.bar}`}
                                    style={{ width: `${pct}%` }}
                                />
                            </div>
                            <p className="text-[10px] text-slate-500 mt-0.5">{c.detail}</p>
                        </div>
                    );
                })}
            </div>

            {/* Recommendations */}
            {recommendations.length > 0 && (
                <div className="border-t border-white/8 pt-2">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                        Pour atteindre 10/10
                    </p>
                    <div className="space-y-1.5">
                        {recommendations.map((r, i) => (
                            <div key={i} className="flex items-center justify-between gap-2">
                                <div className="flex items-center gap-1.5 min-w-0">
                                    <span className="text-sm">{r.icon}</span>
                                    <span className="text-xs text-slate-300 truncate">{r.action}</span>
                                </div>
                                <div className="flex items-center gap-1.5 shrink-0">
                                    <span className="text-xs font-bold text-emerald-400">+{r.gain} pt{r.gain > 1 ? 's' : ''}</span>
                                    <span className={`text-[10px] font-semibold ${PLAN_COLOR[r.plan] || 'text-slate-400'}`}>
                                        {r.plan}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
