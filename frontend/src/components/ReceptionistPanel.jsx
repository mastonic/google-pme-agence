import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
    Loader2, PhoneCall, PhoneIncoming, PhoneForwarded, AlertTriangle, Sparkles, RefreshCw,
    Copy, Check, Settings2, MessageSquare, Send, Wrench, CheckCircle2, XCircle,
} from 'lucide-react';

// Onglet « Réceptionniste » du cockpit : activation, diagnostic Twilio (URLs des webhooks à coller),
// réglages de l'agent (mêmes que l'onboarding du client), simulateur de conversation et derniers appels.
// API : /businesses/{id}/receptionist[/activate|/settings|/test|/diagnostic]
const TRIAL_DAYS = 30;
const CHANNELS = { whatsapp: 'WhatsApp', sms: 'SMS', email: 'E-mail' };

const STATUS_UI = {
    inactive: { label: 'Non activée', cls: 'text-slate-300 bg-white/5 border-white/10' },
    trial:    { label: 'Essai gratuit', cls: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20' },
    active:   { label: 'Active', cls: 'text-sky-300 bg-sky-500/10 border-sky-500/20' },
    expired:  { label: 'Essai terminé', cls: 'text-amber-300 bg-amber-500/10 border-amber-500/20' },
};

const input = 'w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-200 focus:border-brand outline-none';

function Stat({ icon: Icon, label, value, accent }) {
    return (
        <div className="border border-white/10 rounded-xl p-4 flex flex-col gap-1">
            <span className="text-xs text-slate-400 flex items-center gap-1.5"><Icon className="w-3.5 h-3.5" /> {label}</span>
            <span className={`text-2xl font-bold ${accent || 'text-white'}`}>{Number.isFinite(value) ? value : 0}</span>
        </div>
    );
}

function CopyLine({ label, value }) {
    const [ok, setOk] = useState(false);
    return (
        <div className="space-y-1">
            <p className="text-xs text-slate-400">{label}</p>
            <div className="flex items-center gap-2">
                <input readOnly value={value} className="flex-1 min-w-0 bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-slate-300" />
                <button onClick={() => { navigator.clipboard.writeText(value); setOk(true); setTimeout(() => setOk(false), 1500); }}
                    className="p-2 rounded-xl border border-white/10 text-slate-400 hover:text-white hover:bg-white/5">
                    {ok ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
            </div>
        </div>
    );
}

function Diagnostic({ businessId }) {
    const [d, setD] = useState(null);
    useEffect(() => {
        axios.get(`/businesses/${businessId}/receptionist/diagnostic`).then(r => setD(r.data)).catch(() => setD(null));
    }, [businessId]);
    if (!d) return null;
    return (
        <div className="glass p-6 rounded-2xl space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
                <h3 className="font-bold text-white flex items-center gap-2"><Wrench className="w-4 h-4 text-brand" /> Configuration Twilio</h3>
                <span className={`text-xs font-bold px-3 py-1.5 rounded-xl border ${d.ready ? STATUS_UI.trial.cls : STATUS_UI.expired.cls}`}>
                    {d.ready ? 'Prête' : `Manque : ${d.missing.join(', ')}`} · moteur {d.engine === 'relay' ? 'ConversationRelay' : 'Gather'}
                </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {Object.entries(d.env).map(([k, v]) => (
                    <span key={k} className={`text-[11px] flex items-center gap-1 ${v ? 'text-emerald-300' : 'text-slate-500'}`}>
                        {v ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />} {k.replace('TWILIO_', '')}
                    </span>
                ))}
            </div>
            {!d.https && (
                <p className="text-xs text-amber-300">L'URL publique n'est pas en HTTPS : Twilio refusera les webhooks. Renseignez TWILIO_WEBHOOK_BASE_URL.</p>
            )}
            <CopyLine label="Numéro → Voice → « A call comes in » (POST)" value={d.webhooks.voice_incoming} />
            <CopyLine label="Numéro → Voice → « Call status changes » (POST)" value={d.webhooks.voice_status} />
            <CopyLine label="WhatsApp (Sandbox settings ou expéditeur) → « When a message comes in » (POST)" value={d.webhooks.whatsapp_incoming} />
        </div>
    );
}

function Settings({ data, businessId, onSaved }) {
    const s = data.settings || {};
    const [f, setF] = useState(null);
    const [saving, setSaving] = useState(false);
    const [msg, setMsg] = useState('');
    useEffect(() => {
        setF({ ...s, notify_phone: data.notify_phone || '', notify_email: data.notify_email || '', notify_channels: data.notify_channels || [] });
    }, [data]); // eslint-disable-line react-hooks/exhaustive-deps
    if (!f) return null;
    const set = (k, v) => setF(prev => ({ ...prev, [k]: v }));
    const toggle = (k, v) => setF(prev => ({ ...prev, [k]: prev[k].includes(v) ? prev[k].filter(x => x !== v) : [...prev[k], v] }));
    const o = data.options;

    const save = async () => {
        setSaving(true); setMsg('');
        try {
            const { notify_phone, notify_email, notify_channels, ...settings } = f;
            const r = await axios.put(`/businesses/${businessId}/receptionist/settings`,
                { settings, notify_phone, notify_email, notify_channels });
            onSaved(r.data); setMsg('Réglages enregistrés.');
        } catch (e) {
            setMsg(e.response?.data?.detail || 'Enregistrement impossible.');
        } finally { setSaving(false); }
    };

    return (
        <div className="glass p-6 rounded-2xl space-y-4">
            <h3 className="font-bold text-white flex items-center gap-2"><Settings2 className="w-4 h-4 text-brand" /> Réglages de l'agent vocal</h3>
            <p className="text-xs text-slate-500">
                Onboarding client : {data.onboarded ? 'terminé' : 'pas encore fait (proposé à sa prochaine connexion dans l\'onglet Réceptionniste)'}.
            </p>
            <div className="grid sm:grid-cols-2 gap-3">
                <label className="text-xs text-slate-400 space-y-1">Prénom de l'assistante
                    <input className={input} value={f.agent_name} maxLength={30} onChange={e => set('agent_name', e.target.value)} placeholder="Léa" /></label>
                <label className="text-xs text-slate-400 space-y-1">Voix
                    <select className={input} value={f.voice} onChange={e => set('voice', e.target.value)}>
                        {o.voices.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}
                    </select></label>
                <label className="text-xs text-slate-400 space-y-1 sm:col-span-2">Métier (questions posées)
                    <select className={input} value={f.profession} onChange={e => set('profession', e.target.value)}>
                        <option value="">Automatique ({o.professions.find(p => p.id === o.detected_profession)?.label})</option>
                        {o.professions.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                    </select></label>
                <label className="text-xs text-slate-400 space-y-1 sm:col-span-2">Message d'accueil (vide = par défaut)
                    <textarea className={input} rows={2} maxLength={400} value={f.greeting} placeholder={data.default_greeting} onChange={e => set('greeting', e.target.value)} /></label>
                <label className="text-xs text-slate-400 space-y-1 sm:col-span-2">Informations réelles que l'IA peut donner
                    <textarea className={input} rows={3} maxLength={1500} value={f.extra_info} placeholder="Devis gratuit, zone d'intervention…" onChange={e => set('extra_info', e.target.value)} /></label>
                <label className="text-xs text-slate-400 space-y-1 sm:col-span-2">Question supplémentaire
                    <input className={input} maxLength={200} value={f.custom_question} onChange={e => set('custom_question', e.target.value)} /></label>
                <label className="text-xs text-slate-400 space-y-1">Mobile du gérant
                    <input className={input} value={f.notify_phone} onChange={e => set('notify_phone', e.target.value)} /></label>
                <label className="text-xs text-slate-400 space-y-1">E-mail du gérant
                    <input className={input} value={f.notify_email} onChange={e => set('notify_email', e.target.value)} /></label>
            </div>
            <div className="flex flex-wrap gap-2">
                {o.channels.map(c => (
                    <button key={c} onClick={() => toggle('notify_channels', c)}
                        className={`text-xs px-3 py-1.5 rounded-lg border ${f.notify_channels.includes(c) ? 'border-brand text-white bg-brand/20' : 'border-white/10 text-slate-400'}`}>
                        {CHANNELS[c] || c}
                    </button>
                ))}
                <span className="w-px bg-white/10 mx-1" />
                {o.forward_modes.map(m => (
                    <button key={m.id} onClick={() => toggle('forward_modes', m.id)}
                        className={`text-xs px-3 py-1.5 rounded-lg border ${f.forward_modes.includes(m.id) ? 'border-emerald-500 text-white bg-emerald-500/15' : 'border-white/10 text-slate-400'}`}>
                        {m.label}
                    </button>
                ))}
            </div>
            <div className="flex items-center gap-3">
                <button onClick={save} disabled={saving}
                    className="flex items-center gap-2 text-sm bg-brand text-white px-4 py-2 rounded-xl font-bold hover:bg-blue-600 disabled:opacity-40">
                    {saving && <Loader2 className="w-4 h-4 animate-spin" />} Enregistrer
                </button>
                {msg && <span className="text-xs text-slate-300">{msg}</span>}
            </div>
        </div>
    );
}

function Simulator({ businessId }) {
    const [history, setHistory] = useState([]);
    const [collected, setCollected] = useState({});
    const [text, setText] = useState('');
    const [busy, setBusy] = useState(false);
    const [end, setEnd] = useState(null);

    const call = async (message) => {
        setBusy(true);
        try {
            const r = await axios.post(`/businesses/${businessId}/receptionist/test`, { message, history, collected });
            setHistory(h => [...h, ...(message ? [{ role: 'caller', text: message }] : []), { role: 'assistant', text: r.data.reply }]);
            setCollected(r.data.collected || {});
            if (r.data.done) setEnd(r.data.notification);
        } catch (e) {
            setHistory(h => [...h, { role: 'assistant', text: `⚠️ ${e.response?.data?.detail || 'Erreur'}` }]);
        } finally { setBusy(false); }
    };
    const reset = () => { setHistory([]); setCollected({}); setEnd(null); };

    return (
        <div className="glass p-6 rounded-2xl space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="font-bold text-white flex items-center gap-2"><MessageSquare className="w-4 h-4 text-brand" /> Simulateur (sans Twilio)</h3>
                <button onClick={reset} className="text-xs text-slate-400 hover:text-white border border-white/10 rounded-lg px-2 py-1">Recommencer</button>
            </div>
            <div className="bg-slate-950 rounded-xl p-3 space-y-2 max-h-80 overflow-y-auto">
                {history.length === 0 && (
                    <button onClick={() => call('')} disabled={busy} className="text-sm text-brand">Démarrer l'appel simulé →</button>
                )}
                {history.map((h, i) => (
                    <div key={i} className={`text-sm px-3 py-2 rounded-xl max-w-[85%] ${h.role === 'caller' ? 'ml-auto bg-brand text-white' : 'bg-white/5 text-slate-200'}`}>{h.text}</div>
                ))}
                {busy && <Loader2 className="w-4 h-4 animate-spin text-slate-400" />}
            </div>
            {end && <pre className="text-xs whitespace-pre-wrap text-emerald-200 bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3">{end}</pre>}
            {!end && history.length > 0 && (
                <form className="flex gap-2" onSubmit={e => { e.preventDefault(); if (text.trim()) { call(text.trim()); setText(''); } }}>
                    <input className={input} value={text} onChange={e => setText(e.target.value)} placeholder="Réponse de l'appelant…" disabled={busy} />
                    <button disabled={busy} className="px-3 rounded-xl bg-brand text-white"><Send className="w-4 h-4" /></button>
                </form>
            )}
        </div>
    );
}

function ReceptionistPanel({ businessId }) {
    const [data, setData]             = useState(null);
    const [loading, setLoading]       = useState(true);
    const [error, setError]           = useState('');
    const [activating, setActivating] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const r = await axios.get(`/businesses/${businessId}/receptionist`);
            setData(r.data || { status: 'inactive' });
            setError('');
        } catch (e) {
            if (e.response?.status === 404) { setData({ status: 'inactive' }); setError(''); }
            else setError(e.response?.data?.detail || 'Impossible de charger la réceptionniste IA.');
        } finally {
            setLoading(false);
        }
    }, [businessId]);

    useEffect(() => { setData(null); load(); }, [load]);

    const activate = async (body = {}) => {
        setActivating(true); setError('');
        try {
            const r = await axios.post(`/businesses/${businessId}/receptionist/activate`, body);
            if (r.data && r.data.status) setData(r.data); else await load();
        } catch (e) {
            setError(e.response?.data?.detail || "L'activation a échoué. Réessayez dans un instant.");
        } finally { setActivating(false); }
    };

    if (loading && !data) {
        return <div className="glass p-8 rounded-2xl flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-brand" /></div>;
    }

    const status   = STATUS_UI[data?.status] ? data.status : 'inactive';
    const ui       = STATUS_UI[status];
    const stats    = data?.stats || {};
    const daysLeft = Math.max(0, Number(data?.days_left) || 0);
    const progress = status === 'trial' ? Math.min(100, Math.round(((TRIAL_DAYS - daysLeft) / TRIAL_DAYS) * 100)) : 0;
    const on       = status !== 'inactive' && data?.options;

    return (
        <div className="space-y-4">
            <div className="glass p-6 rounded-2xl space-y-5">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                        <h3 className="font-bold text-white flex items-center gap-2"><PhoneCall className="w-4 h-4 text-brand" /> Réceptionniste IA</h3>
                        <p className="text-sm text-slate-400 mt-1 max-w-xl">
                            Répond aux appels manqués, qualifie la demande, détecte les urgences et envoie un résumé WhatsApp / SMS.
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className={`text-xs font-bold px-3 py-1.5 rounded-xl border ${ui.cls}`}>
                            {ui.label}{status === 'trial' && ` · ${daysLeft} j restant${daysLeft > 1 ? 's' : ''}`}
                        </span>
                        {(status === 'trial' || status === 'expired') && (
                            <button onClick={() => activate({ paid_active: true })} disabled={activating}
                                className="text-xs border border-white/10 px-3 py-1.5 rounded-xl text-slate-300 hover:bg-white/5">Passer en payant</button>
                        )}
                        <button onClick={load} disabled={loading} title="Actualiser"
                            className="p-2 rounded-xl border border-white/10 text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-40">
                            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>

                {error && <div className="flex items-center gap-2 text-sm text-amber-300"><AlertTriangle className="w-4 h-4" /> {error}</div>}

                {status === 'trial' && (
                    <div className="h-1.5 rounded-full bg-white/10 overflow-hidden" aria-label="Progression de l'essai">
                        <div className="h-full bg-emerald-400" style={{ width: `${progress}%` }} />
                    </div>
                )}

                {status !== 'inactive' && (
                    <>
                        <div className="grid grid-cols-3 gap-3">
                            <Stat icon={PhoneIncoming} label="Appels reçus" value={Number(stats.received)} />
                            <Stat icon={PhoneForwarded} label="Récupérés" value={Number(stats.recovered)} accent="text-emerald-300" />
                            <Stat icon={AlertTriangle} label="Urgents" value={Number(stats.urgent)} accent="text-amber-300" />
                        </div>
                        {data?.twilio_number && (
                            <p className="text-sm text-slate-300">
                                Numéro de renvoi : <span className="font-mono text-white">{data.twilio_number}</span>
                                {data.forward_codes?.length > 0 && <> · codes : {data.forward_codes.map(c => <span key={c.mode} className="font-mono text-white ml-1">{c.activate}</span>)}</>}
                            </p>
                        )}
                    </>
                )}

                {status === 'inactive' && (
                    <div className="flex items-center justify-between gap-4 flex-wrap border border-brand/30 bg-brand/5 rounded-xl p-4">
                        <p className="text-sm text-slate-300"><span className="font-bold text-white">Offerte 30 jours</span>, sans engagement. Le client verra ensuite l'onglet Réceptionniste et son onboarding.</p>
                        <button onClick={() => activate()} disabled={activating}
                            className="flex items-center gap-2 text-sm bg-brand text-white px-4 py-2 rounded-xl font-bold hover:bg-blue-600 disabled:opacity-40">
                            {activating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                            Activer les 30 jours gratuits
                        </button>
                    </div>
                )}
            </div>

            <Diagnostic businessId={businessId} />
            {on && <Settings data={data} businessId={businessId} onSaved={setData} />}
            <Simulator businessId={businessId} />

            {data?.recent_calls?.length > 0 && (
                <div className="glass p-6 rounded-2xl space-y-3">
                    <h3 className="font-bold text-white">Derniers appels</h3>
                    {data.recent_calls.map((c, i) => (
                        <div key={i} className="border border-white/10 rounded-xl p-3 text-sm">
                            <div className="flex justify-between text-xs text-slate-400">
                                <span>{c.summary?.urgence ? '🚨 ' : ''}{c.summary?.caller?.nom || c.from} · {c.mode}</span>
                                <span>{c.at && new Date(c.at).toLocaleString('fr-FR')}</span>
                            </div>
                            <p className="text-slate-200 mt-1">{c.summary?.motif || '—'}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default ReceptionistPanel;
