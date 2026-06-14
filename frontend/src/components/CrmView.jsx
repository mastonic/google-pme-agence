import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import {
    Users, Phone, Mail, Globe, Calendar,
    ChevronRight, Plus, Loader2, Check, X,
    TrendingUp, Target, Award,
    PhoneCall, Send, Video, FileText,
    Columns, List, AlertTriangle,
    ExternalLink, Copy, Star, Sparkles, User,
} from 'lucide-react';

const STAGES = [
    { id: 'prospect',    label: 'Prospects',       emoji: '🔍', description: 'Scannés, non contactés' },
    { id: 'contacted',   label: 'Contactés',       emoji: '📞', description: 'Premier contact effectué' },
    { id: 'demo_sent',   label: 'Démo envoyée',    emoji: '🌐', description: 'Site démo partagé' },
    { id: 'negotiating', label: 'En négociation',  emoji: '💬', description: 'Discussion en cours' },
    { id: 'won',         label: 'Clients',         emoji: '✅', description: 'Abonnement signé' },
    { id: 'lost',        label: 'Perdus',          emoji: '❌', description: 'Sans suite' },
];

const STAGE_COLORS = {
    prospect:    { bg: 'bg-slate-500/10',   border: 'border-slate-500/20',   text: 'text-slate-400',   dot: 'bg-slate-400',   header: 'bg-slate-500/5' },
    contacted:   { bg: 'bg-blue-500/10',    border: 'border-blue-500/20',    text: 'text-blue-400',    dot: 'bg-blue-400',    header: 'bg-blue-500/5' },
    demo_sent:   { bg: 'bg-violet-500/10',  border: 'border-violet-500/20',  text: 'text-violet-400',  dot: 'bg-violet-400',  header: 'bg-violet-500/5' },
    negotiating: { bg: 'bg-amber-500/10',   border: 'border-amber-500/20',   text: 'text-amber-400',   dot: 'bg-amber-400',   header: 'bg-amber-500/5' },
    won:         { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', dot: 'bg-emerald-400', header: 'bg-emerald-500/5' },
    lost:        { bg: 'bg-rose-500/10',    border: 'border-rose-500/20',    text: 'text-rose-400',    dot: 'bg-rose-400',    header: 'bg-rose-500/5' },
};

const PRIORITY = {
    low:    { text: 'text-slate-400',  bg: 'bg-slate-500/10',  label: 'Faible' },
    medium: { text: 'text-blue-400',   bg: 'bg-blue-500/10',   label: 'Moyen' },
    high:   { text: 'text-amber-400',  bg: 'bg-amber-500/10',  label: 'Élevé' },
    urgent: { text: 'text-rose-400',   bg: 'bg-rose-500/10',   label: 'Urgent' },
};

const ACTIVITY_META = {
    call:      { icon: PhoneCall, color: 'text-emerald-400', label: 'Appel' },
    email:     { icon: Send,      color: 'text-blue-400',    label: 'Email' },
    meeting:   { icon: Video,     color: 'text-violet-400',  label: 'Réunion' },
    demo_sent: { icon: Globe,     color: 'text-sky-400',     label: 'Démo' },
    note:      { icon: FileText,  color: 'text-slate-400',   label: 'Note' },
};

function ActivityItem({ a }) {
    const meta = ACTIVITY_META[a.type] || ACTIVITY_META.note;
    const Icon = meta.icon;
    const d = new Date(a.created_at);
    return (
        <div className="flex gap-3 py-2.5 border-b border-white/5 last:border-0">
            <div className="w-6 h-6 rounded-full bg-white/5 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Icon className={`w-3 h-3 ${meta.color}`} />
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${meta.color}`}>{meta.label}</span>
                    <span className="text-[10px] text-slate-500">
                        {d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })} {d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                </div>
                {a.content && <p className="text-xs text-slate-300 mt-0.5 break-words">{a.content}</p>}
            </div>
        </div>
    );
}

function ContactPanel({ contact, onClose, onUpdate }) {
    const [notes, setNotes]           = useState(contact.crm_notes || '');
    const [stage, setStage]           = useState(contact.crm_stage || 'prospect');
    const [priority, setPriority]     = useState(contact.priority || 'medium');
    const [ownerEmail, setOwnerEmail] = useState(contact.owner_email || '');
    const [ownerPhone, setOwnerPhone] = useState(contact.owner_phone || '');
    const [dealValue, setDealValue]   = useState(contact.deal_value || 0);
    const [nextContact, setNextContact] = useState(
        contact.next_contact_at ? contact.next_contact_at.split('T')[0] : ''
    );
    const [dirigeant, setDirigeant] = useState({
        first: contact.owner_first_name || '', last: contact.owner_last_name || '',
        role: contact.owner_role || '', siren: contact.siren || '',
    });
    const [enriching, setEnriching] = useState(false);
    const [activities, setActivities] = useState([]);
    const [loadingActs, setLoadingActs] = useState(true);
    const [actType, setActType]       = useState('call');
    const [actContent, setActContent] = useState('');
    const [saving, setSaving]         = useState(false);
    const [copied, setCopied]         = useState(false);
    const saveTimer = useRef(null);

    useEffect(() => {
        setNotes(contact.crm_notes || '');
        setStage(contact.crm_stage || 'prospect');
        setPriority(contact.priority || 'medium');
        setOwnerEmail(contact.owner_email || '');
        setOwnerPhone(contact.owner_phone || '');
        setDirigeant({
            first: contact.owner_first_name || '', last: contact.owner_last_name || '',
            role: contact.owner_role || '', siren: contact.siren || '',
        });
        setDealValue(contact.deal_value || 0);
        setNextContact(contact.next_contact_at ? contact.next_contact_at.split('T')[0] : '');
        setLoadingActs(true);
        axios.get(`/businesses/${contact.id}/activities`)
            .then(r => setActivities(r.data))
            .catch(() => {})
            .finally(() => setLoadingActs(false));
    }, [contact.id]);

    const patch = useCallback(async (fields) => {
        setSaving(true);
        try {
            await axios.patch(`/businesses/${contact.id}/crm`, fields);
            if (onUpdate) onUpdate(contact.id, fields);
        } finally {
            setSaving(false);
        }
    }, [contact.id, onUpdate]);

    const handleEnrich = async () => {
        setEnriching(true);
        try {
            const r = await axios.post(`/businesses/${contact.id}/enrich`);
            const d = r.data || {};
            if (d.owner_email) setOwnerEmail(d.owner_email);
            if (d.owner_phone) setOwnerPhone(d.owner_phone);
            setDirigeant({
                first: d.owner_first_name || '', last: d.owner_last_name || '',
                role: d.owner_role || '', siren: d.siren || '',
            });
            if (onUpdate) onUpdate(contact.id, d);
        } catch (e) {
            console.error('Enrichment error:', e);
        } finally {
            setEnriching(false);
        }
    };

    const handleStageChange = (s) => {
        setStage(s);
        patch({ crm_stage: s });
    };

    const handleNotesBlur = () => patch({ crm_notes: notes });
    const handleNotesChange = (v) => {
        setNotes(v);
        clearTimeout(saveTimer.current);
        saveTimer.current = setTimeout(() => patch({ crm_notes: v }), 1200);
    };

    const logActivity = async () => {
        if (!actContent.trim()) return;
        const r = await axios.post(`/businesses/${contact.id}/activities`, { type: actType, content: actContent });
        setActivities(prev => [r.data, ...prev]);
        setActContent('');
    };

    const sc = STAGE_COLORS[stage] || STAGE_COLORS.prospect;
    const pm = PRIORITY[priority] || PRIORITY.medium;
    const demoUrl = `${window.location.origin}/demo/${contact.id}`;

    return (
        <div className="fixed inset-0 z-50 flex">
            <div className="flex-1 bg-black/50 backdrop-blur-sm" onClick={onClose} />
            <div className="w-[460px] bg-slate-900 border-l border-white/10 flex flex-col h-full overflow-y-auto"
                 style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,.1) transparent' }}>

                {/* Header */}
                <div className="sticky top-0 bg-slate-900 z-10 px-6 pt-6 pb-4 border-b border-white/10">
                    <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                            <h2 className="text-lg font-bold truncate">{contact.name}</h2>
                            <p className="text-xs text-slate-400 truncate mt-0.5">{contact.address}</p>
                            <div className="flex items-center gap-2 mt-2 flex-wrap">
                                <span className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${sc.bg} ${sc.border} border ${sc.text}`}>
                                    <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
                                    {STAGES.find(s => s.id === stage)?.label}
                                </span>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${pm.bg} ${pm.text}`}>
                                    {pm.label}
                                </span>
                                {contact.potential_score < 4 && (
                                    <span className="flex items-center gap-0.5 text-[10px] font-bold text-red-400">
                                        <Star className="w-3 h-3" />Cible {contact.potential_score}/10
                                    </span>
                                )}
                                {saving && <Loader2 className="w-3 h-3 animate-spin text-slate-500" />}
                            </div>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-colors flex-shrink-0">
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                <div className="flex-1 p-6 space-y-6">

                    {/* Pipeline Stage */}
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">Étape pipeline</p>
                        <div className="grid grid-cols-3 gap-1.5">
                            {STAGES.map(s => {
                                const c = STAGE_COLORS[s.id];
                                return (
                                    <button key={s.id} onClick={() => handleStageChange(s.id)}
                                        className={`flex flex-col items-center gap-1 p-2 rounded-xl border text-center transition-all ${
                                            stage === s.id
                                                ? `${c.bg} ${c.border} ${c.text}`
                                                : 'border-white/5 text-slate-500 hover:bg-white/5'
                                        }`}>
                                        <span className="text-base">{s.emoji}</span>
                                        <span className="text-[9px] font-bold leading-tight">{s.label}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Coordonnées */}
                    <div>
                        <div className="flex items-center justify-between mb-3">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Coordonnées</p>
                            <button onClick={handleEnrich} disabled={enriching}
                                className="flex items-center gap-1 text-[10px] font-bold text-brand hover:text-brand/80 disabled:opacity-50 transition-colors"
                                title="Retrouve le gérant, l'email et le téléphone (Pappers + Perplexity)">
                                {enriching ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                                {enriching ? 'Recherche…' : 'Enrichir'}
                            </button>
                        </div>
                        {(dirigeant.first || dirigeant.last) && (
                            <div className="flex items-center gap-2 mb-2 text-sm">
                                <User className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                                <span className="text-white font-medium">{[dirigeant.first, dirigeant.last].filter(Boolean).join(' ')}</span>
                                {dirigeant.role && <span className="text-[10px] text-slate-500">· {dirigeant.role}</span>}
                                {dirigeant.siren && <span className="text-[10px] text-slate-600 ml-auto">SIREN {dirigeant.siren}</span>}
                            </div>
                        )}
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Phone className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                                <input type="tel" value={ownerPhone}
                                    onChange={e => setOwnerPhone(e.target.value)}
                                    onBlur={() => patch({ owner_phone: ownerPhone })}
                                    placeholder="Téléphone..."
                                    className="flex-1 bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand" />
                                {ownerPhone && (
                                    <a href={`tel:${ownerPhone}`} className="p-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 hover:bg-emerald-500/20 transition-colors">
                                        <PhoneCall className="w-3.5 h-3.5" />
                                    </a>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                <Mail className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                                <input type="email" value={ownerEmail}
                                    onChange={e => setOwnerEmail(e.target.value)}
                                    onBlur={() => patch({ owner_email: ownerEmail })}
                                    placeholder="Email du gérant..."
                                    className="flex-1 bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand" />
                                {ownerEmail && (
                                    <a href={`mailto:${ownerEmail}`} className="p-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400 hover:bg-blue-500/20 transition-colors">
                                        <Send className="w-3.5 h-3.5" />
                                    </a>
                                )}
                            </div>
                            {contact.website && (
                                <div className="flex items-center gap-2">
                                    <Globe className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                                    <a href={contact.website} target="_blank" rel="noopener noreferrer"
                                       className="text-sm text-brand hover:underline truncate flex-1">{contact.website}</a>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Deal + Priorité */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Valeur deal (€/mois)</p>
                            <input type="number" min="0" value={dealValue}
                                onChange={e => setDealValue(e.target.value)}
                                onBlur={() => patch({ deal_value: parseFloat(dealValue) || 0 })}
                                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-brand" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Priorité</p>
                            <select value={priority}
                                onChange={e => { setPriority(e.target.value); patch({ priority: e.target.value }); }}
                                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-brand">
                                <option value="low">Faible</option>
                                <option value="medium">Moyen</option>
                                <option value="high">Élevé</option>
                                <option value="urgent">Urgent 🔴</option>
                            </select>
                        </div>
                    </div>

                    {/* Prochain contact */}
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Prochain contact</p>
                        <div className="flex items-center gap-2">
                            <Calendar className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                            <input type="date" value={nextContact}
                                onChange={e => { setNextContact(e.target.value); patch({ next_contact_at: e.target.value }); }}
                                className="flex-1 bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-brand" />
                        </div>
                    </div>

                    {/* Notes */}
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Notes</p>
                        <textarea value={notes}
                            onChange={e => handleNotesChange(e.target.value)}
                            onBlur={handleNotesBlur}
                            rows={4}
                            placeholder="Objections, points clés, détails du prospect..."
                            className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand resize-none" />
                    </div>

                    {/* Actions rapides */}
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">Actions rapides</p>
                        <div className="grid grid-cols-2 gap-2">
                            <button onClick={() => {
                                navigator.clipboard.writeText(demoUrl);
                                setCopied(true);
                                setTimeout(() => setCopied(false), 2000);
                                axios.post(`/businesses/${contact.id}/activities`, { type: 'demo_sent', content: `Démo partagée : ${demoUrl}` })
                                    .then(r => setActivities(prev => [r.data, ...prev])).catch(() => {});
                                if (['prospect', 'contacted'].includes(stage)) handleStageChange('demo_sent');
                            }} className="flex items-center gap-2 p-2.5 bg-violet-500/10 border border-violet-500/20 rounded-xl text-xs text-violet-400 hover:bg-violet-500/20 transition-colors">
                                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                                {copied ? 'Copié !' : 'Copier démo'}
                            </button>
                            <a href={`https://maps.google.com/?q=${encodeURIComponent((contact.name || '') + ' ' + (contact.address || ''))}`}
                               target="_blank" rel="noopener noreferrer"
                               className="flex items-center gap-2 p-2.5 bg-slate-500/10 border border-slate-500/20 rounded-xl text-xs text-slate-400 hover:bg-slate-500/20 transition-colors">
                                <ExternalLink className="w-3.5 h-3.5" />
                                Google Maps
                            </a>
                        </div>
                    </div>

                    {/* Log activité */}
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">Enregistrer une activité</p>
                        <div className="space-y-2">
                            <div className="flex gap-1 flex-wrap">
                                {Object.entries(ACTIVITY_META).map(([key, meta]) => {
                                    const Icon = meta.icon;
                                    return (
                                        <button key={key} onClick={() => setActType(key)}
                                            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                                                actType === key ? `${meta.color} bg-white/10` : 'text-slate-500 hover:text-white hover:bg-white/5'
                                            }`}>
                                            <Icon className="w-3 h-3" />{meta.label}
                                        </button>
                                    );
                                })}
                            </div>
                            <div className="flex gap-2">
                                <input type="text" value={actContent}
                                    onChange={e => setActContent(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && logActivity()}
                                    placeholder="Détails de l'activité..."
                                    className="flex-1 bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand" />
                                <button onClick={logActivity} disabled={!actContent.trim()}
                                    className="px-3 py-1.5 bg-brand rounded-lg font-bold disabled:opacity-30 hover:bg-blue-600 transition-colors">
                                    <Plus className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Historique activités */}
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">
                            Historique ({activities.length})
                        </p>
                        {loadingActs ? (
                            <div className="flex items-center justify-center py-6">
                                <Loader2 className="w-5 h-5 animate-spin text-slate-500" />
                            </div>
                        ) : activities.length === 0 ? (
                            <p className="text-xs text-slate-600 text-center py-4">Aucune activité enregistrée</p>
                        ) : (
                            activities.map(a => <ActivityItem key={a.id} a={a} />)
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function KanbanCard({ contact, onClick }) {
    const sc = STAGE_COLORS[contact.crm_stage] || STAGE_COLORS.prospect;
    const pm = PRIORITY[contact.priority || 'medium'];
    const isOverdue = contact.next_contact_at && new Date(contact.next_contact_at) < new Date();

    return (
        <div onClick={onClick}
             className="bg-slate-800/60 border border-white/[0.06] hover:border-white/20 rounded-xl p-3 cursor-pointer transition-all hover:bg-slate-800 group">
            <div className="flex items-start justify-between gap-2 mb-1.5">
                <h4 className="text-sm font-semibold leading-tight group-hover:text-brand transition-colors line-clamp-2 flex-1">{contact.name}</h4>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded flex-shrink-0 ${
                    contact.potential_score >= 7 ? 'bg-emerald-500/20 text-emerald-400' :
                    contact.potential_score >= 2.5 ? 'bg-amber-500/20 text-amber-400' :
                    'bg-red-500/20 text-red-400'
                }`}>{contact.potential_score}</span>
            </div>
            {contact.address && (
                <p className="text-[11px] text-slate-500 truncate mb-2">{contact.address}</p>
            )}
            <div className="flex items-center gap-1.5 flex-wrap">
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${pm.bg} ${pm.text}`}>
                    {pm.label}
                </span>
                {contact.deal_value > 0 && (
                    <span className="text-[9px] font-bold text-brand">{contact.deal_value}€/m</span>
                )}
                {isOverdue && (
                    <span className="text-[9px] font-bold text-rose-400 flex items-center gap-0.5">
                        <AlertTriangle className="w-2.5 h-2.5" />En retard
                    </span>
                )}
                {contact.next_contact_at && !isOverdue && (
                    <span className="text-[9px] text-slate-500 flex items-center gap-0.5">
                        <Calendar className="w-2.5 h-2.5" />
                        {new Date(contact.next_contact_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                    </span>
                )}
                {contact.owner_phone && <Phone className="w-2.5 h-2.5 text-slate-500" />}
                {contact.owner_email && <Mail className="w-2.5 h-2.5 text-slate-500" />}
            </div>
        </div>
    );
}

function CrmView() {
    const [pipeline, setPipeline] = useState({});
    const [stats, setStats]       = useState(null);
    const [loading, setLoading]   = useState(true);
    const [selected, setSelected] = useState(null);
    const [viewMode, setViewMode] = useState('kanban');
    const [filterStage, setFilterStage] = useState('all');
    const [sortField, setSortField]     = useState('potential_score');

    const fetchPipeline = useCallback(async () => {
        try {
            const r = await axios.get('/crm/pipeline');
            if (r.data && typeof r.data === 'object' && r.data.pipeline) {
                setPipeline(r.data.pipeline);
                setStats(r.data.stats);
            }
        } catch (e) {
            console.error('CRM fetch error:', e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchPipeline(); }, [fetchPipeline]);

    const handleUpdate = useCallback((id, fields) => {
        setPipeline(prev => {
            const next = {};
            let contact = null;
            for (const [stage, cards] of Object.entries(prev)) {
                const idx = cards.findIndex(c => c.id === id);
                if (idx !== -1) {
                    contact = { ...cards[idx], ...fields };
                    next[stage] = cards.filter(c => c.id !== id);
                } else {
                    next[stage] = cards;
                }
            }
            if (contact) {
                const newStage = contact.crm_stage || 'prospect';
                if (!next[newStage]) next[newStage] = [];
                next[newStage] = [contact, ...next[newStage]];
            }
            return next;
        });
        setSelected(prev => prev?.id === id ? { ...prev, ...fields } : prev);
    }, []);

    const allContacts = Object.values(pipeline || {}).flat();
    const listContacts = allContacts
        .filter(c => filterStage === 'all' || c.crm_stage === filterStage)
        .sort((a, b) => {
            if (sortField === 'potential_score') return (b.potential_score || 0) - (a.potential_score || 0);
            if (sortField === 'deal_value') return (b.deal_value || 0) - (a.deal_value || 0);
            if (sortField === 'name') return (a.name || '').localeCompare(b.name || '');
            return 0;
        });

    if (loading) return (
        <div className="w-full h-full flex items-center justify-center bg-slate-900">
            <Loader2 className="w-8 h-8 animate-spin text-brand" />
        </div>
    );

    return (
        <div className="w-full h-full bg-slate-900 flex flex-col overflow-hidden">

            {/* Header + Stats */}
            <div className="flex-shrink-0 px-8 pt-8 pb-5 border-b border-white/5">
                <div className="flex items-center justify-between mb-5">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                            <Users className="w-7 h-7 text-brand" />
                            CRM Pipeline
                        </h2>
                        <p className="text-slate-400 mt-1 text-sm">Suivi commercial de vos prospects TPE/PME</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <button onClick={() => setViewMode('kanban')}
                            className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${viewMode === 'kanban' ? 'bg-brand/10 text-brand border border-brand/20' : 'text-slate-400 hover:bg-white/5 border border-transparent'}`}>
                            <Columns className="w-4 h-4" />Kanban
                        </button>
                        <button onClick={() => setViewMode('list')}
                            className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${viewMode === 'list' ? 'bg-brand/10 text-brand border border-brand/20' : 'text-slate-400 hover:bg-white/5 border border-transparent'}`}>
                            <List className="w-4 h-4" />Liste
                        </button>
                    </div>
                </div>

                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                            { label: 'Total prospects',   value: stats.total_prospects,                  color: 'text-white',         icon: Users },
                            { label: 'Pipeline négoc.',   value: `${stats.pipeline_value.toFixed(0)}€/m`, color: 'text-amber-400',    icon: TrendingUp },
                            { label: 'Clients signés',    value: stats.won_clients,                      color: 'text-emerald-400',   icon: Award },
                            { label: 'Taux conversion',   value: `${stats.conversion_rate}%`,            color: 'text-brand',         icon: Target },
                        ].map(({ label, value, color, icon: Icon }) => (
                            <div key={label} className="glass p-4 rounded-2xl flex items-center gap-4">
                                <Icon className={`w-5 h-5 ${color}`} />
                                <div>
                                    <p className={`text-xl font-bold ${color}`}>{value}</p>
                                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5">{label}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto"
                 style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,.1) transparent' }}>

                {viewMode === 'kanban' ? (
                    /* ── Kanban ── */
                    <div className="flex gap-4 p-6 h-full" style={{ minWidth: 'max-content' }}>
                        {STAGES.map(stage => {
                            const cards = pipeline[stage.id] || [];
                            const sc = STAGE_COLORS[stage.id];
                            const colValue = cards.reduce((s, c) => s + (c.deal_value || 0), 0);
                            return (
                                <div key={stage.id} className="flex flex-col w-72 flex-shrink-0">
                                    <div className={`flex items-center justify-between px-3 py-2.5 rounded-xl mb-3 ${sc.header} border ${sc.border}`}>
                                        <div className="flex items-center gap-2">
                                            <span>{stage.emoji}</span>
                                            <span className={`text-sm font-bold ${sc.text}`}>{stage.label}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {colValue > 0 && <span className={`text-[10px] font-bold ${sc.text} opacity-70`}>{colValue}€</span>}
                                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full bg-black/20 ${sc.text}`}>{cards.length}</span>
                                        </div>
                                    </div>
                                    <div className="flex-1 space-y-2.5 overflow-y-auto"
                                         style={{ scrollbarWidth: 'none', maxHeight: 'calc(100vh - 280px)' }}>
                                        {cards.length === 0 ? (
                                            <div className="border border-dashed border-white/10 rounded-xl p-4 text-center text-slate-600 text-xs">
                                                {stage.description}
                                            </div>
                                        ) : (
                                            cards.map(c => (
                                                <KanbanCard key={c.id} contact={c} onClick={() => setSelected(c)} />
                                            ))
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    /* ── Liste ── */
                    <div className="p-6 max-w-6xl mx-auto">
                        <div className="flex items-center gap-3 mb-4 flex-wrap">
                            <select value={filterStage} onChange={e => setFilterStage(e.target.value)}
                                className="bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-sm text-white focus:outline-none focus:border-brand">
                                <option value="all">Toutes les étapes</option>
                                {STAGES.map(s => <option key={s.id} value={s.id}>{s.emoji} {s.label}</option>)}
                            </select>
                            <select value={sortField} onChange={e => setSortField(e.target.value)}
                                className="bg-slate-800 border border-white/10 rounded-xl px-3 py-1.5 text-sm text-white focus:outline-none focus:border-brand">
                                <option value="potential_score">Trier par score</option>
                                <option value="deal_value">Trier par valeur deal</option>
                                <option value="name">Trier par nom</option>
                            </select>
                            <span className="text-xs text-slate-500">{listContacts.length} résultats</span>
                        </div>
                        <div className="space-y-2">
                            {listContacts.map(c => {
                                const sc = STAGE_COLORS[c.crm_stage] || STAGE_COLORS.prospect;
                                const stage = STAGES.find(s => s.id === c.crm_stage);
                                const isOverdue = c.next_contact_at && new Date(c.next_contact_at) < new Date();
                                return (
                                    <div key={c.id} onClick={() => setSelected(c)}
                                         className="glass p-4 rounded-xl flex items-center gap-4 cursor-pointer hover:border-white/20 transition-colors group">
                                        <span className="text-lg flex-shrink-0">{stage?.emoji || '🔍'}</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <h4 className="font-semibold text-sm group-hover:text-brand transition-colors truncate">{c.name}</h4>
                                                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${sc.bg} ${sc.text} flex-shrink-0`}>
                                                    {stage?.label}
                                                </span>
                                            </div>
                                            <p className="text-[11px] text-slate-500 truncate mt-0.5">{c.address}</p>
                                        </div>
                                        <div className="hidden md:flex items-center gap-6 flex-shrink-0">
                                            <div className="text-right">
                                                <p className={`text-sm font-bold ${c.potential_score >= 7 ? 'text-emerald-400' : c.potential_score >= 2.5 ? 'text-amber-400' : 'text-red-400'}`}>{c.potential_score}/10</p>
                                                <p className="text-[10px] text-slate-500">Score</p>
                                            </div>
                                            {c.deal_value > 0 && (
                                                <div className="text-right">
                                                    <p className="text-sm font-bold text-brand">{c.deal_value}€</p>
                                                    <p className="text-[10px] text-slate-500">/mois</p>
                                                </div>
                                            )}
                                            {c.next_contact_at && (
                                                <div className="text-right">
                                                    <p className={`text-sm font-bold ${isOverdue ? 'text-rose-400' : 'text-slate-300'}`}>
                                                        {new Date(c.next_contact_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                                                    </p>
                                                    <p className="text-[10px] text-slate-500">{isOverdue ? 'En retard !' : 'Prochain contact'}</p>
                                                </div>
                                            )}
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 flex-shrink-0" />
                                    </div>
                                );
                            })}
                            {listContacts.length === 0 && (
                                <div className="text-center py-16 text-slate-600">
                                    <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
                                    <p className="text-sm">Aucun prospect dans cette étape</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Contact Side Panel */}
            {selected && (
                <ContactPanel
                    contact={selected}
                    onClose={() => setSelected(null)}
                    onUpdate={handleUpdate}
                />
            )}
        </div>
    );
}

export default CrmView;
