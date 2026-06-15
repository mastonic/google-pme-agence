import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
    BarChart3, Users, TrendingUp, TrendingDown, DollarSign,
    Settings, Palette, CreditCard, ChevronRight, Plus, Edit3,
    Trash2, ToggleLeft, ToggleRight, Globe, Check, X,
    Zap, BookOpen, Star, RefreshCw, Save, AlertCircle
} from 'lucide-react';

const API = '';

// ─── small helpers ─────────────────────────────────────────────────────────

const fmt = (n, prefix = '') => {
    if (n >= 1000) return `${prefix}${(n / 1000).toFixed(1)}k`;
    return `${prefix}${Number(n).toFixed(0)}`;
};

const Badge = ({ color, children }) => (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${color}`}>{children}</span>
);

const KpiCard = ({ label, value, sub, trend, icon: Icon, color = 'text-brand' }) => (
    <div className="glass rounded-2xl p-5 flex flex-col gap-2">
        <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">{label}</span>
            <Icon className={`w-4 h-4 ${color}`} />
        </div>
        <div className={`text-3xl font-extrabold tracking-tight ${color}`}>{value}</div>
        <div className="flex items-center gap-1.5 text-xs">
            {trend !== undefined && (
                trend >= 0
                    ? <TrendingUp className="w-3 h-3 text-emerald-400" />
                    : <TrendingDown className="w-3 h-3 text-rose-400" />
            )}
            <span className="text-slate-400">{sub}</span>
        </div>
    </div>
);

const Toggle = ({ value, onChange }) => (
    <button onClick={() => onChange(!value)}
        className={`transition-colors ${value ? 'text-emerald-400' : 'text-slate-600'}`}>
        {value ? <ToggleRight className="w-6 h-6" /> : <ToggleLeft className="w-6 h-6" />}
    </button>
);

// ─── KPI TAB ───────────────────────────────────────────────────────────────

function KpiTab() {
    const [kpis, setKpis] = useState(null);
    const load = useCallback(async () => {
        try { const r = await axios.get(`${API}/admin/kpis`); setKpis(r.data); } catch { }
    }, []);
    useEffect(() => { load(); }, []);

    if (!kpis) return (
        <div className="flex items-center justify-center h-64 text-slate-500">
            <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Chargement...
        </div>
    );

    const { tier_breakdown: tb = {}, status_breakdown: sb = {} } = kpis;
    const tiers = [
        { slug: 'free', label: 'Free', color: 'text-slate-400', bg: 'bg-slate-500/20' },
        { slug: 'starter', label: 'Starter', color: 'text-indigo-400', bg: 'bg-indigo-500/20' },
        { slug: 'pro', label: 'Pro', color: 'text-brand', bg: 'bg-brand/20' },
        { slug: 'elite', label: 'Elite', color: 'text-amber-400', bg: 'bg-amber-500/20' },
    ];
    const statuses = [
        { key: 'scanned', label: 'Scannés', color: 'bg-slate-500' },
        { key: 'processing', label: 'En cours', color: 'bg-amber-500' },
        { key: 'pending_validation', label: 'À valider', color: 'bg-blue-500' },
        { key: 'completed', label: 'Déployés', color: 'bg-emerald-500' },
        { key: 'error', label: 'Erreurs', color: 'bg-rose-500' },
    ];

    return (
        <div className="space-y-8">
            {/* Revenue row */}
            <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4">Revenus</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <KpiCard label="MRR" value={fmt(kpis.mrr, '€')} sub={`+${kpis.mrr_growth_pct}% ce mois`} trend={1} icon={DollarSign} color="text-emerald-400" />
                    <KpiCard label="ARR" value={fmt(kpis.arr, '€')} sub="Revenu annuel projeté" icon={TrendingUp} color="text-emerald-400" />
                    <KpiCard label="LTV" value={fmt(kpis.ltv, '€')} sub={`CAC: ${kpis.cac}€ · Ratio ${kpis.ltv_cac_ratio}x`} icon={BarChart3} color="text-brand" />
                    <KpiCard label="Churn" value={`${kpis.churn_rate}%`} sub="Taux de résiliation mensuel" trend={-1} icon={TrendingDown} color="text-rose-400" />
                </div>
            </div>

            {/* Clients row */}
            <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4">Clients</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <KpiCard label="Clients actifs" value={kpis.total_active_clients} sub="Abonnements payants" icon={Users} color="text-brand" />
                    <KpiCard label="Sites déployés" value={kpis.sites_deployed} sub="Commerces en ligne" icon={Globe} color="text-emerald-400" />
                    <KpiCard label="Pipeline" value={kpis.sites_pipeline} sub="En cours de traitement" icon={Zap} color="text-amber-400" />
                    <KpiCard label="Total scanné" value={kpis.total_scanned} sub="Prospects identifiés" icon={BarChart3} color="text-slate-300" />
                </div>
            </div>

            {/* Breakdowns */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Plan breakdown */}
                <div className="glass rounded-2xl p-6">
                    <h4 className="text-sm font-bold mb-4">Répartition par plan</h4>
                    <div className="space-y-3">
                        {tiers.map(t => {
                            const count = tb[t.slug] || 0;
                            const total = Object.values(tb).reduce((a, b) => a + b, 0) || 1;
                            const pct = Math.round((count / total) * 100);
                            return (
                                <div key={t.slug} className="space-y-1">
                                    <div className="flex justify-between text-xs">
                                        <span className={`font-bold ${t.color}`}>{t.label}</span>
                                        <span className="text-slate-400">{count} client{count !== 1 ? 's' : ''} · {pct}%</span>
                                    </div>
                                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                        <div className={`h-full ${t.bg} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Pipeline funnel */}
                <div className="glass rounded-2xl p-6">
                    <h4 className="text-sm font-bold mb-4">Funnel Pipeline</h4>
                    <div className="space-y-3">
                        {statuses.map(s => {
                            const count = sb[s.key] || 0;
                            const max = Math.max(...Object.values(sb), 1);
                            const pct = Math.round((count / max) * 100);
                            return (
                                <div key={s.key} className="space-y-1">
                                    <div className="flex justify-between text-xs">
                                        <span className="text-slate-300">{s.label}</span>
                                        <span className="text-slate-400 font-bold">{count}</span>
                                    </div>
                                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                        <div className={`h-full ${s.color} opacity-70 rounded-full transition-all`} style={{ width: `${pct}%` }} />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ─── PLANS TAB ─────────────────────────────────────────────────────────────

function PlansTab() {
    const [plans, setPlans] = useState([]);
    const [editing, setEditing] = useState(null); // plan object or null
    const [saving, setSaving] = useState(false);

    const load = useCallback(async () => {
        try { const r = await axios.get(`${API}/admin/plans`); setPlans(r.data); } catch { }
    }, []);
    useEffect(() => { load(); }, []);

    const save = async () => {
        if (!editing) return;
        setSaving(true);
        try {
            if (editing.id) {
                await axios.put(`${API}/admin/plans/${editing.id}`, editing);
            } else {
                await axios.post(`${API}/admin/plans`, editing);
            }
            await load();
            setEditing(null);
        } catch { }
        setSaving(false);
    };

    const toggle = async (plan) => {
        await axios.put(`${API}/admin/plans/${plan.id}`, { is_active: !plan.is_active });
        load();
    };

    const del = async (id) => {
        if (!confirm('Supprimer ce plan ?')) return;
        await axios.delete(`${API}/admin/plans/${id}`);
        load();
    };

    const addFeature = () => setEditing(e => ({ ...e, features: [...(e.features || []), { text: '', included: true }] }));
    const updateFeature = (i, field, val) => setEditing(e => {
        const features = [...e.features];
        features[i] = { ...features[i], [field]: val };
        return { ...e, features };
    });
    const removeFeature = (i) => setEditing(e => ({ ...e, features: e.features.filter((_, j) => j !== i) }));

    const COLORS = ['#6366f1', '#0071E3', '#d97706', '#10b981', '#ef4444', '#8b5cf6'];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">Grille Tarifaire</h3>
                <button onClick={() => setEditing({ name: '', slug: '', price: 49, color: '#0071E3', icon: '✨', is_popular: false, is_active: true, features: [], limits: {}, sort_order: 0 })}
                    className="flex items-center gap-2 text-sm bg-brand/20 text-brand border border-brand/30 px-3 py-1.5 rounded-xl hover:bg-brand/30 transition-colors">
                    <Plus className="w-4 h-4" /> Nouveau plan
                </button>
            </div>

            <div className="grid md:grid-cols-3 gap-5">
                {plans.map(plan => (
                    <div key={plan.id} className={`relative rounded-2xl p-5 border transition-all ${plan.is_active ? 'border-white/10 bg-white/5' : 'border-white/5 bg-white/2 opacity-50'}`}>
                        {plan.badge && (
                            <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full text-[10px] font-bold text-black"
                                 style={{ background: plan.color }}>
                                {plan.badge}
                            </div>
                        )}
                        <div className="flex items-start justify-between mb-3">
                            <div>
                                <span className="text-xl">{plan.icon}</span>
                                <span className="font-bold text-lg ml-2">{plan.name}</span>
                            </div>
                            <Toggle value={plan.is_active} onChange={() => toggle(plan)} />
                        </div>
                        <div className="text-3xl font-extrabold mb-1" style={{ color: plan.color }}>
                            {plan.price}€ <span className="text-sm font-normal text-slate-400">/mois</span>
                        </div>
                        <ul className="space-y-1.5 mt-4 mb-5">
                            {(plan.features || []).slice(0, 5).map((f, i) => (
                                <li key={i} className={`flex items-center gap-2 text-xs ${f.included ? 'text-slate-300' : 'text-slate-600 line-through'}`}>
                                    {f.included ? <Check className="w-3 h-3 text-emerald-400 flex-shrink-0" /> : <X className="w-3 h-3 flex-shrink-0" />}
                                    {f.text}
                                </li>
                            ))}
                            {(plan.features || []).length > 5 && <li className="text-xs text-slate-500">+{plan.features.length - 5} autres...</li>}
                        </ul>
                        <div className="flex gap-2">
                            <button onClick={() => setEditing({ ...plan })}
                                className="flex-1 flex items-center justify-center gap-1 text-xs border border-white/10 rounded-xl py-2 hover:bg-white/5 transition-colors">
                                <Edit3 className="w-3 h-3" /> Éditer
                            </button>
                            <button onClick={() => del(plan.id)}
                                className="p-2 rounded-xl border border-rose-500/20 text-rose-400 hover:bg-rose-500/10 transition-colors">
                                <Trash2 className="w-3 h-3" />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Edit Modal */}
            {editing && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-white/10 rounded-3xl p-8 w-full max-w-2xl max-h-[90vh] overflow-y-auto custom-scrollbar">
                        <h3 className="text-xl font-bold mb-6">{editing.id ? 'Éditer' : 'Créer'} un plan</h3>
                        <div className="grid md:grid-cols-2 gap-4 mb-6">
                            {[
                                { label: 'Nom', key: 'name', type: 'text' },
                                { label: 'Slug', key: 'slug', type: 'text', hint: 'starter / pro / elite' },
                                { label: 'Prix (€/mois)', key: 'price', type: 'number' },
                                { label: 'Icône emoji', key: 'icon', type: 'text' },
                                { label: 'Badge (optionnel)', key: 'badge', type: 'text' },
                                { label: 'Ordre d\'affichage', key: 'sort_order', type: 'number' },
                            ].map(f => (
                                <div key={f.key}>
                                    <label className="text-xs text-slate-400 mb-1 block">{f.label}</label>
                                    <input type={f.type} value={editing[f.key] || ''} placeholder={f.hint}
                                        onChange={e => setEditing(ed => ({ ...ed, [f.key]: f.type === 'number' ? parseFloat(e.target.value) : e.target.value }))}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand" />
                                </div>
                            ))}
                        </div>
                        <div className="mb-4">
                            <label className="text-xs text-slate-400 mb-2 block">Couleur</label>
                            <div className="flex gap-2">
                                {COLORS.map(c => (
                                    <button key={c} onClick={() => setEditing(e => ({ ...e, color: c }))}
                                        className={`w-8 h-8 rounded-full border-2 transition-all ${editing.color === c ? 'border-white scale-110' : 'border-transparent'}`}
                                        style={{ background: c }} />
                                ))}
                                <input type="color" value={editing.color || '#0071E3'}
                                    onChange={e => setEditing(ed => ({ ...ed, color: e.target.value }))}
                                    className="w-8 h-8 rounded-full border border-white/10 cursor-pointer" />
                            </div>
                        </div>
                        <div className="flex items-center gap-4 mb-6">
                            <label className="flex items-center gap-2 text-sm cursor-pointer">
                                <input type="checkbox" checked={editing.is_popular || false}
                                    onChange={e => setEditing(ed => ({ ...ed, is_popular: e.target.checked }))}
                                    className="rounded" />
                                Plan populaire
                            </label>
                            <label className="flex items-center gap-2 text-sm cursor-pointer">
                                <input type="checkbox" checked={editing.is_active !== false}
                                    onChange={e => setEditing(ed => ({ ...ed, is_active: e.target.checked }))}
                                    className="rounded" />
                                Actif
                            </label>
                        </div>
                        <div className="mb-6">
                            <div className="flex items-center justify-between mb-3">
                                <label className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Fonctionnalités</label>
                                <button onClick={addFeature} className="text-xs text-brand flex items-center gap-1">
                                    <Plus className="w-3 h-3" /> Ajouter
                                </button>
                            </div>
                            <div className="space-y-2 max-h-52 overflow-y-auto custom-scrollbar">
                                {(editing.features || []).map((f, i) => (
                                    <div key={i} className="flex items-center gap-2">
                                        <button onClick={() => updateFeature(i, 'included', !f.included)}
                                            className={f.included ? 'text-emerald-400' : 'text-slate-600'}>
                                            {f.included ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                                        </button>
                                        <input value={f.text} onChange={e => updateFeature(i, 'text', e.target.value)}
                                            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-xs focus:outline-none focus:border-brand"
                                            placeholder="Description de la fonctionnalité" />
                                        <button onClick={() => removeFeature(i)} className="text-rose-400 hover:text-rose-300">
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="flex justify-end gap-3">
                            <button onClick={() => setEditing(null)} className="px-5 py-2 rounded-xl border border-white/10 text-sm hover:bg-white/5 transition-colors">Annuler</button>
                            <button onClick={save} disabled={saving}
                                className="px-5 py-2 rounded-xl bg-brand text-white text-sm font-bold hover:bg-brand-dark transition-colors disabled:opacity-50 flex items-center gap-2">
                                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                Enregistrer
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── CLIENTS TAB ───────────────────────────────────────────────────────────

const TIER_COLORS = {
    free: 'bg-slate-500/20 text-slate-400',
    starter: 'bg-indigo-500/20 text-indigo-400',
    pro: 'bg-brand/20 text-brand',
    elite: 'bg-amber-500/20 text-amber-400',
};
const TIER_PRICES = { free: 0, starter: 49, pro: 149, elite: 299 };

function ClientsTab() {
    const [clients, setClients] = useState([]);
    const [selected, setSelected] = useState(null);
    const [saving, setSaving] = useState(false);
    const [search, setSearch] = useState('');
    const [checking, setChecking] = useState(false);

    const handleMonitor = async () => {
        if (!selected) return;
        setChecking(true);
        try {
            const r = await axios.post(`${API}/monitor/${selected.id}`);
            const m = r.data.monitoring || {};
            setSelected(s => ({
                ...s, monitoring: m,
                domain_ssl_active: m.ssl?.status === 'ok',
                seo_score: m.seo?.score ?? s.seo_score,
            }));
        } catch (e) {
            console.error('Monitoring error:', e);
        } finally {
            setChecking(false);
        }
    };

    const [monAll, setMonAll] = useState(false);
    const [monSummary, setMonSummary] = useState(null);
    const [sched, setSched] = useState(null);

    useEffect(() => {
        axios.get(`${API}/scheduler/status`).then(r => setSched(r.data)).catch(() => {});
    }, []);

    const handleMonitorAll = async () => {
        setMonAll(true);
        try {
            const r = await axios.post(`${API}/monitor-all`);
            setMonSummary(r.data);
            await load();
        } catch (e) {
            console.error('Monitor-all error:', e);
        } finally {
            setMonAll(false);
        }
    };

    const load = useCallback(async () => {
        try { const r = await axios.get(`${API}/admin/clients`); setClients(r.data); } catch { }
    }, []);
    useEffect(() => { load(); }, []);

    const save = async () => {
        if (!selected) return;
        setSaving(true);
        try {
            const r = await axios.patch(`${API}/admin/clients/${selected.id}`, {
                plan_tier: selected.plan_tier,
                subscription_status: selected.subscription_status,
                custom_domain: selected.custom_domain || null,
                features_booking_active: selected.features_booking_active,
                features_menu_active: selected.features_menu_active,
                features_click_collect_active: selected.features_click_collect_active,
                features_chatbot_active: selected.features_chatbot_active,
                features_seo_blog_active: selected.features_seo_blog_active,
                features_gmb_reviews_sync: selected.features_gmb_reviews_sync,
                features_multilang_active: selected.features_multilang_active,
            });
            setSelected(r.data);
            await load();
        } catch { }
        setSaving(false);
    };

    const filtered = clients.filter(c =>
        c.name?.toLowerCase().includes(search.toLowerCase()) ||
        c.address?.toLowerCase().includes(search.toLowerCase())
    );

    const features = [
        { key: 'features_booking_active',      label: 'Réservations en ligne',         icon: '📅', minPlan: 'pro' },
        { key: 'features_menu_active',          label: 'Carte / Catalogue produits',    icon: '🍽️', minPlan: 'pro' },
        { key: 'features_click_collect_active', label: 'Click & Collect',               icon: '🛒', minPlan: 'pro' },
        { key: 'features_chatbot_active',       label: 'Chatbot WhatsApp IA',           icon: '💬', minPlan: 'elite' },
        { key: 'features_seo_blog_active',      label: 'Articles SEO automatiques',     icon: '✍️', minPlan: 'elite' },
        { key: 'features_gmb_reviews_sync',     label: 'Avis Google en direct',         icon: '⭐', minPlan: 'pro' },
        { key: 'features_multilang_active',     label: 'Site multilingue (EN/ES/AR)',   icon: '🌍', minPlan: 'elite' },
    ];

    return (
        <div className="flex gap-6 h-full min-h-[600px]">
            {/* Client list */}
            <div className="w-80 flex-shrink-0 flex flex-col gap-3">
                {/* Supervision en masse */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-3">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">🛰️ Supervision</span>
                        <button onClick={handleMonitorAll} disabled={monAll}
                            className="flex items-center gap-1.5 text-xs font-bold bg-brand hover:bg-brand-dark text-white px-2.5 py-1 rounded-lg disabled:opacity-50 transition-colors">
                            {monAll ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                            {monAll ? 'Analyse…' : 'Tout vérifier'}
                        </button>
                    </div>
                    {monSummary && (
                        <p className="text-[11px] text-slate-300">
                            {monSummary.checked} sites · <span className="text-emerald-400">{monSummary.ok || 0} OK</span>
                            {monSummary.warning ? <> · <span className="text-amber-400">{monSummary.warning} ⚠️</span></> : null}
                            {monSummary.error ? <> · <span className="text-red-400">{monSummary.error} ❌</span></> : null}
                        </p>
                    )}
                    {sched?.enabled && (
                        <p className="text-[10px] text-slate-500 mt-1">
                            Auto chaque matin ({sched.window || '08:00 – 08:45'})
                            {sched.next_run ? ` · prochaine : ${sched.next_run.replace('T', ' ').slice(0, 16)}` : ''}
                        </p>
                    )}
                </div>
                <input value={search} onChange={e => setSearch(e.target.value)}
                    placeholder="🔍 Rechercher un client..."
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-brand" />
                <div className="flex-1 space-y-2 overflow-y-auto max-h-[560px] custom-scrollbar">
                    {filtered.length === 0 && <p className="text-slate-500 text-sm text-center py-8">Aucun client trouvé.</p>}
                    {filtered.map(c => (
                        <div key={c.id} onClick={() => setSelected({ ...c })}
                            className={`p-3 rounded-xl cursor-pointer border transition-all ${selected?.id === c.id ? 'bg-brand/10 border-brand/30' : 'bg-white/5 border-transparent hover:border-white/10'}`}>
                            <div className="flex items-center justify-between mb-1">
                                <span className="font-bold text-sm truncate text-white">{c.name}</span>
                                <Badge color={TIER_COLORS[c.plan_tier] || TIER_COLORS.free}>
                                    {c.plan_tier}
                                </Badge>
                            </div>
                            <p className="text-[10px] text-slate-500 truncate">{c.address}</p>
                            <div className="flex items-center gap-2 mt-1.5">
                                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${c.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-500/20 text-slate-400'}`}>
                                    {c.status}
                                </span>
                                {c.mrr_value > 0 && <span className="text-[10px] text-emerald-400 font-bold">{c.mrr_value}€/mois</span>}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Client detail panel */}
            <div className="flex-1 glass rounded-2xl p-6 overflow-y-auto custom-scrollbar">
                {!selected ? (
                    <div className="h-full flex items-center justify-center text-slate-500">
                        <div className="text-center">
                            <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
                            <p>Sélectionnez un client</p>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <h3 className="text-xl font-bold">{selected.name}</h3>
                                <p className="text-sm text-slate-400">{selected.address}</p>
                                <div className="flex items-center gap-2 mt-2">
                                    {selected.rating > 0 && <span className="text-amber-400 text-sm">★ {selected.rating}</span>}
                                    {selected.deployment_url && (
                                        <a href={selected.deployment_url} target="_blank" rel="noopener noreferrer"
                                           className="text-xs text-brand hover:underline flex items-center gap-1">
                                            <Globe className="w-3 h-3" /> Site live
                                        </a>
                                    )}
                                </div>
                            </div>
                            <button onClick={save} disabled={saving}
                                className="flex items-center gap-2 bg-brand text-white px-4 py-2 rounded-xl text-sm font-bold hover:bg-brand-dark transition-colors disabled:opacity-50">
                                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                Enregistrer
                            </button>
                        </div>

                        {/* Plan & Subscription */}
                        <div>
                            <h4 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Abonnement</h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs text-slate-400 mb-1 block">Plan</label>
                                    <select value={selected.plan_tier}
                                        onChange={e => setSelected(s => ({ ...s, plan_tier: e.target.value, mrr_value: TIER_PRICES[e.target.value] || 0 }))}
                                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand">
                                        {Object.keys(TIER_PRICES).map(t => (
                                            <option key={t} value={t} className="bg-slate-900">{t.charAt(0).toUpperCase() + t.slice(1)} — {TIER_PRICES[t]}€/mois</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs text-slate-400 mb-1 block">Statut abonnement</label>
                                    <select value={selected.subscription_status}
                                        onChange={e => setSelected(s => ({ ...s, subscription_status: e.target.value }))}
                                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand">
                                        {['inactive', 'trialing', 'active', 'cancelled'].map(st => (
                                            <option key={st} value={st} className="bg-slate-900">{st}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <div className="mt-3">
                                <label className="text-xs text-slate-400 mb-1 block">MRR (calculé automatiquement)</label>
                                <div className="text-2xl font-extrabold text-emerald-400">{selected.mrr_value || 0}€ <span className="text-sm font-normal text-slate-400">/mois</span></div>
                            </div>
                        </div>

                        {/* Domain */}
                        <div>
                            <h4 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Nom de domaine</h4>
                            <div className="flex items-center gap-3">
                                <input value={selected.custom_domain || ''}
                                    onChange={e => setSelected(s => ({ ...s, custom_domain: e.target.value }))}
                                    placeholder="www.moncommerce.fr"
                                    className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand" />
                                <div className={`px-3 py-2 rounded-xl text-xs font-bold flex items-center gap-1 ${selected.domain_ssl_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-500/20 text-slate-400'}`}>
                                    🔒 SSL {selected.domain_ssl_active ? 'Actif' : 'Inactif'}
                                </div>
                            </div>
                        </div>

                        {/* Feature Flags */}
                        <div>
                            <h4 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Modules activés</h4>
                            <div className="space-y-3">
                                {features.map(f => {
                                    const planTier = selected.plan_tier;
                                    const PLAN_ORDER = { free: 0, starter: 1, pro: 2, elite: 3 };
                                    const MIN_ORDER  = { pro: 2, elite: 3 };
                                    const isLocked = (PLAN_ORDER[planTier] ?? 0) < (MIN_ORDER[f.minPlan] ?? 0);
                                    return (
                                        <div key={f.key} className={`flex items-center justify-between p-3 rounded-xl border ${isLocked ? 'border-white/5 opacity-50' : 'border-white/10 bg-white/5'}`}>
                                            <div className="flex items-center gap-2">
                                                <span>{f.icon}</span>
                                                <span className="text-sm font-medium">{f.label}</span>
                                                {isLocked && <Badge color="bg-slate-500/20 text-slate-400">Plan supérieur requis</Badge>}
                                            </div>
                                            <Toggle value={selected[f.key]} onChange={v => !isLocked && setSelected(s => ({ ...s, [f.key]: v }))} />
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* SEO */}
                        <div>
                            <h4 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Score SEO</h4>
                            <div className="flex items-center gap-4">
                                <div className="flex-1 h-3 bg-white/5 rounded-full overflow-hidden">
                                    <div className="h-full bg-gradient-to-r from-brand to-emerald-400 rounded-full transition-all"
                                         style={{ width: `${selected.seo_score || 0}%` }} />
                                </div>
                                <span className="font-bold text-brand w-12 text-right">{selected.seo_score || 0}/100</span>
                            </div>
                        </div>

                        {/* Supervision (SSL / Avis / SEO) */}
                        <div>
                            <div className="flex items-center justify-between mb-3">
                                <h4 className="text-xs font-bold uppercase tracking-widest text-slate-500">Supervision en direct</h4>
                                <button onClick={handleMonitor} disabled={checking || !selected.deployment_url}
                                    className="flex items-center gap-1.5 text-xs font-bold text-brand hover:text-brand/80 disabled:opacity-40 transition-colors"
                                    title={selected.deployment_url ? 'Vérifie SSL, avis Google et SEO en direct' : 'Aucun site déployé à superviser'}>
                                    {checking ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                                    {checking ? 'Analyse…' : 'Rafraîchir'}
                                </button>
                            </div>
                            {selected.monitoring ? (
                                <div className="grid grid-cols-3 gap-3">
                                    {[
                                        { label: '🔒 SSL', val: selected.monitoring.ssl?.status === 'ok' ? 'Valide' : (selected.monitoring.ssl?.status || '—'),
                                          sub: selected.monitoring.ssl?.days_left != null ? `${selected.monitoring.ssl.days_left} j` : (selected.monitoring.ssl?.detail || ''),
                                          ok: selected.monitoring.ssl?.status === 'ok' },
                                        { label: '⭐ Avis', val: selected.monitoring.reviews?.rating != null ? `${selected.monitoring.reviews.rating}` : '—',
                                          sub: selected.monitoring.reviews?.total != null ? `${selected.monitoring.reviews.total} avis` : '',
                                          ok: selected.monitoring.reviews?.status === 'ok' },
                                        { label: '🔎 SEO', val: `${selected.monitoring.seo?.score ?? '—'}/100`,
                                          sub: selected.monitoring.seo?.status || '',
                                          ok: (selected.monitoring.seo?.score || 0) >= 80 },
                                    ].map(c => (
                                        <div key={c.label} className={`p-3 rounded-xl border ${c.ok ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-amber-500/20 bg-amber-500/5'}`}>
                                            <p className="text-[10px] text-slate-400 font-bold uppercase">{c.label}</p>
                                            <p className="text-sm font-bold text-white mt-1">{c.val}</p>
                                            <p className="text-[10px] text-slate-500">{c.sub}</p>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-xs text-slate-500">Cliquez sur « Rafraîchir » pour vérifier SSL, avis Google et SEO. Vérification automatique chaque matin (8h–8h45).</p>
                            )}
                            {selected.monitoring?.needs_seo_refresh && (
                                <p className="text-[11px] text-amber-400 mt-2">⚠️ Nouveaux avis détectés — republier le site rafraîchira le SEO (note/avis).</p>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ─── DESIGN LIBRARY TAB ────────────────────────────────────────────────────

function DesignLibraryTab() {
    const [presets, setPresets] = useState([]);
    const [editing, setEditing] = useState(null);
    const [saving, setSaving] = useState(false);

    const load = useCallback(async () => {
        try { const r = await axios.get(`${API}/admin/design-presets`); setPresets(r.data); } catch { }
    }, []);
    useEffect(() => { load(); }, []);

    const save = async () => {
        if (!editing) return;
        setSaving(true);
        try {
            if (editing.id) {
                await axios.put(`${API}/admin/design-presets/${editing.id}`, editing);
            } else {
                await axios.post(`${API}/admin/design-presets`, editing);
            }
            await load(); setEditing(null);
        } catch { }
        setSaving(false);
    };

    const del = async (id) => {
        if (!confirm('Supprimer ce preset ?')) return;
        await axios.delete(`${API}/admin/design-presets/${id}`);
        load();
    };

    const toggle = async (p) => {
        await axios.put(`${API}/admin/design-presets/${p.id}`, { is_active: !p.is_active });
        load();
    };

    const empty = {
        name: '', label: '', sectors: [], mood: '', is_active: true,
        colors: { primary: '#1A1A1A', secondary: '#0071E3', accent: '#E5E7EB', bg: '#FFFFFF', text: '#111827' },
        fonts: { heading: 'Inter', body: 'Inter' }
    };

    return (
        <div className="space-y-5">
            <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500">Palettes Design</h3>
                <button onClick={() => setEditing({ ...empty })}
                    className="flex items-center gap-2 text-sm bg-brand/20 text-brand border border-brand/30 px-3 py-1.5 rounded-xl hover:bg-brand/30 transition-colors">
                    <Plus className="w-4 h-4" /> Nouveau preset
                </button>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                {presets.map(p => {
                    const c = p.colors || {};
                    return (
                        <div key={p.id} className={`rounded-2xl overflow-hidden border transition-all ${p.is_active ? 'border-white/10' : 'border-white/5 opacity-50'}`}>
                            {/* Color swatch strip */}
                            <div className="flex h-10">
                                {[c.primary, c.secondary, c.accent, c.bg, c.text].map((col, i) => (
                                    <div key={i} className="flex-1" style={{ background: col }} />
                                ))}
                            </div>
                            <div className="bg-white/5 p-4">
                                <div className="flex items-start justify-between mb-1">
                                    <div>
                                        <h4 className="font-bold text-sm">{p.label}</h4>
                                        <p className="text-[10px] text-slate-500 font-mono">{p.name}</p>
                                    </div>
                                    <Toggle value={p.is_active} onChange={() => toggle(p)} />
                                </div>
                                <p className="text-[11px] text-slate-400 mb-2 line-clamp-2">{p.mood}</p>
                                <div className="flex gap-1 flex-wrap mb-3">
                                    {(p.fonts?.heading ? [p.fonts.heading, p.fonts.body] : []).map((f, i) => (
                                        <span key={i} className="text-[9px] bg-white/10 px-1.5 py-0.5 rounded font-mono">{f}</span>
                                    ))}
                                </div>
                                <div className="flex gap-1.5">
                                    <button onClick={() => setEditing({ ...p })}
                                        className="flex-1 text-xs border border-white/10 rounded-lg py-1.5 hover:bg-white/5 transition-colors flex items-center justify-center gap-1">
                                        <Edit3 className="w-3 h-3" /> Éditer
                                    </button>
                                    <button onClick={() => del(p.id)}
                                        className="p-1.5 rounded-lg border border-rose-500/20 text-rose-400 hover:bg-rose-500/10 transition-colors">
                                        <Trash2 className="w-3 h-3" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Edit modal */}
            {editing && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-white/10 rounded-3xl p-8 w-full max-w-xl max-h-[90vh] overflow-y-auto custom-scrollbar">
                        <h3 className="text-xl font-bold mb-6">{editing.id ? 'Éditer' : 'Créer'} un preset design</h3>
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-slate-400 mb-1 block">Nom (slug)</label>
                                    <input value={editing.name} onChange={e => setEditing(ed => ({ ...ed, name: e.target.value }))}
                                        placeholder="luxury-dining"
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand" />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-400 mb-1 block">Label affiché</label>
                                    <input value={editing.label} onChange={e => setEditing(ed => ({ ...ed, label: e.target.value }))}
                                        placeholder="Restaurant / Café"
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand" />
                                </div>
                            </div>
                            <div>
                                <label className="text-xs text-slate-400 mb-1 block">Secteurs (séparés par virgule)</label>
                                <input value={(editing.sectors || []).join(', ')}
                                    onChange={e => setEditing(ed => ({ ...ed, sectors: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }))}
                                    placeholder="restaurant, food, cafe"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand" />
                            </div>
                            <div>
                                <label className="text-xs text-slate-400 mb-1 block">Mood / ambiance</label>
                                <input value={editing.mood || ''} onChange={e => setEditing(ed => ({ ...ed, mood: e.target.value }))}
                                    placeholder="chaleureux, artisanal, premium"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand" />
                            </div>
                            <div>
                                <label className="text-xs text-slate-400 mb-3 block">Palette de couleurs</label>
                                <div className="grid grid-cols-5 gap-2">
                                    {['primary', 'secondary', 'accent', 'bg', 'text'].map(key => (
                                        <div key={key} className="text-center">
                                            <input type="color" value={editing.colors?.[key] || '#000000'}
                                                onChange={e => setEditing(ed => ({ ...ed, colors: { ...ed.colors, [key]: e.target.value } }))}
                                                className="w-full h-10 rounded-lg border border-white/10 cursor-pointer" />
                                            <span className="text-[9px] text-slate-500 mt-1 block capitalize">{key}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-slate-400 mb-1 block">Police Titres (Google Fonts)</label>
                                    <input value={editing.fonts?.heading || ''}
                                        onChange={e => setEditing(ed => ({ ...ed, fonts: { ...ed.fonts, heading: e.target.value } }))}
                                        placeholder="Playfair Display"
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand" />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-400 mb-1 block">Police Corps</label>
                                    <input value={editing.fonts?.body || ''}
                                        onChange={e => setEditing(ed => ({ ...ed, fonts: { ...ed.fonts, body: e.target.value } }))}
                                        placeholder="Lato"
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand" />
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-6">
                            <button onClick={() => setEditing(null)} className="px-5 py-2 rounded-xl border border-white/10 text-sm hover:bg-white/5 transition-colors">Annuler</button>
                            <button onClick={save} disabled={saving}
                                className="px-5 py-2 rounded-xl bg-brand text-white text-sm font-bold disabled:opacity-50 flex items-center gap-2 hover:bg-brand-dark transition-colors">
                                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                Enregistrer
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── MAIN ADMIN VIEW ───────────────────────────────────────────────────────

const TABS = [
    { id: 'kpis',    label: 'KPIs & MRR',       icon: BarChart3 },
    { id: 'plans',   label: 'Plans & Tarifs',    icon: CreditCard },
    { id: 'clients', label: 'Clients',           icon: Users },
    { id: 'design',  label: 'Design Library',    icon: Palette },
];

function AdminView({ onBack }) {
    const [tab, setTab] = useState('kpis');

    return (
        <div className="flex-1 h-full bg-slate-900 overflow-y-auto custom-scrollbar">
            {/* Header */}
            <div className="sticky top-0 z-10 bg-slate-950/80 backdrop-blur border-b border-white/5 px-8 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button onClick={onBack} className="p-2 rounded-xl hover:bg-white/5 transition-colors text-slate-400 hover:text-white">
                        <ChevronRight className="w-5 h-5 rotate-180" />
                    </button>
                    <div>
                        <h1 className="text-xl font-extrabold tracking-tight flex items-center gap-2">
                            <Settings className="w-5 h-5 text-brand" /> Panel Admin
                        </h1>
                        <p className="text-xs text-slate-500">Local-Pulse SaaS — Centre de contrôle</p>
                    </div>
                </div>
                <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-3 py-1.5 rounded-full text-xs font-bold">
                    <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                    Système opérationnel
                </div>
            </div>

            <div className="p-8">
                {/* Tab nav */}
                <div className="flex items-center gap-2 mb-8 border-b border-white/10 pb-4 overflow-x-auto custom-scrollbar">
                    {TABS.map(t => (
                        <button key={t.id} onClick={() => setTab(t.id)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold text-sm whitespace-nowrap transition-all ${tab === t.id ? 'bg-brand text-white shadow-lg shadow-brand/25' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>
                            <t.icon className="w-4 h-4" />
                            {t.label}
                        </button>
                    ))}
                </div>

                {/* Tab content */}
                {tab === 'kpis'    && <KpiTab />}
                {tab === 'plans'   && <PlansTab />}
                {tab === 'clients' && <ClientsTab />}
                {tab === 'design'  && <DesignLibraryTab />}
            </div>
        </div>
    );
}

export default AdminView;
