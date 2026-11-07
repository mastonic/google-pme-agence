import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Loader2, X, RefreshCw, ExternalLink, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';

// Vue « comme le client » + informations de maintenance détaillées (cockpit uniquement).

const LEVEL = {
    high: 'text-red-300 bg-red-500/10 border-red-500/30',
    medium: 'text-amber-300 bg-amber-500/10 border-amber-500/30',
    low: 'text-sky-300 bg-sky-500/10 border-sky-500/30',
};
const STATUS_FR = {
    active: 'Actif', trialing: 'Essai', inactive: 'Inactif', past_due: 'Paiement en retard',
    unpaid: 'Impayé', canceled: 'Résilié', cancelled: 'Résilié',
};
const FEATURE_FR = {
    booking: 'Réservations', menu: 'Carte / catalogue', click_collect: 'Click & Collect', chatbot: 'Chatbot WhatsApp',
    seo_blog: 'Articles SEO', gmb_reviews_sync: 'Avis Google live', multilang: 'Multilingue',
};

const fmtDate = (iso) => (iso ? new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '—');
const pct = (a, b) => (b ? Math.round(((a - b) / b) * 100) : null);

function Section({ title, children, right }) {
    return (
        <section className="bg-slate-800 border border-white/10 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-300">{title}</h4>
                {right}
            </div>
            {children}
        </section>
    );
}

function Row({ label, value, tone }) {
    return (
        <div className="flex justify-between gap-3 text-sm py-1 border-b border-white/5 last:border-0">
            <span className="text-slate-400">{label}</span>
            <span className={`font-medium text-right ${tone || 'text-slate-100'}`}>{value ?? '—'}</span>
        </div>
    );
}

function Bar({ value, max = 100 }) {
    const p = Math.max(0, Math.min(100, Math.round(((value || 0) / max) * 100)));
    const color = p >= 75 ? 'bg-emerald-500' : p >= 45 ? 'bg-amber-500' : 'bg-red-500';
    return (
        <div className="h-1.5 bg-slate-950 rounded-full overflow-hidden">
            <div className={`h-full rounded-full ${color}`} style={{ width: `${p}%` }} />
        </div>
    );
}

export function MaintenancePanel({ m, onSupervise, supervising }) {
    const s = m.stats;
    const statRows = [
        ['Visites', 'visits'], ['Appels', 'calls'], ['WhatsApp', 'whatsapp'], ['Itinéraires', 'directions'],
    ];
    const sup = m.supervision || {};
    const r = m.receptionist || {};
    return (
        <div className="space-y-3">
            {/* Alertes */}
            <Section title={`Points d'attention (${m.alerts.length})`}>
                {m.alerts.length === 0 ? (
                    <p className="text-sm text-emerald-300 flex items-center gap-2"><ShieldCheck className="w-4 h-4" /> Rien à signaler.</p>
                ) : (
                    <ul className="space-y-1.5">
                        {m.alerts.map((a, i) => (
                            <li key={i} className={`text-xs border rounded-lg px-3 py-2 ${LEVEL[a.level] || LEVEL.low}`}>{a.text}</li>
                        ))}
                    </ul>
                )}
            </Section>

            <Section title="Abonnement">
                <Row label="Formule" value={m.subscription.plan} />
                <Row label="Statut" value={STATUS_FR[m.subscription.status] || m.subscription.status}
                    tone={['active', 'trialing'].includes(m.subscription.status) ? 'text-emerald-300' : 'text-amber-300'} />
                <Row label="MRR" value={`${m.subscription.mrr || 0} €`} />
                <Row label="Signé le" value={fmtDate(m.subscription.signed_at)} />
                <Row label="Client Stripe" value={m.subscription.stripe_customer ? 'Oui' : 'Non'} />
            </Section>

            <Section title="Site"
                right={m.site.url && (
                    <a href={m.site.url} target="_blank" rel="noopener noreferrer" className="text-xs text-brand flex items-center gap-1">
                        Ouvrir <ExternalLink className="w-3 h-3" />
                    </a>
                )}>
                <Row label="URL" value={m.site.url || 'Non déployé'} tone={m.site.url ? 'text-slate-100 break-all' : 'text-amber-300'} />
                <Row label="Domaine perso" value={m.site.custom_domain || '—'} />
                {(() => {
                    const ok = sup.ssl?.status ? sup.ssl.status === 'ok' : m.site.ssl_active;
                    const label = sup.ssl?.status ? (ok ? 'Actif' : sup.ssl.status === 'warning' ? 'Expire bientôt' : 'Invalide') : (m.site.ssl_active ? 'Actif' : 'Non vérifié');
                    return <Row label="SSL" value={label} tone={ok ? 'text-emerald-300' : 'text-amber-300'} />;
                })()}
                <Row label="Généré le" value={fmtDate(m.site.generated_at)} />
                <Row label="Déployé le" value={fmtDate(m.site.deployed_at)} />
                <Row label="Options actives"
                    value={Object.entries(m.site.features).filter(([, v]) => v).map(([k]) => FEATURE_FR[k] || k).join(', ') || 'Aucune'} />
            </Section>

            <Section title="Supervision"
                right={
                    <button onClick={onSupervise} disabled={supervising || !m.site.url}
                        className="text-xs flex items-center gap-1 border border-white/10 rounded-lg px-2 py-1 hover:bg-white/5 disabled:opacity-40">
                        {supervising ? <Loader2 className="w-3 h-3 animate-spin" /> : <Activity className="w-3 h-3" />} Lancer
                    </button>
                }>
                {Object.keys(sup).length === 0 ? (
                    <p className="text-sm text-slate-400">Jamais supervisé.</p>
                ) : (
                    <>
                        <Row label="SSL" value={sup.ssl?.status ? `${sup.ssl.status}${sup.ssl.days_left != null ? ` · expire dans ${sup.ssl.days_left} j` : ''}` : '—'}
                            tone={sup.ssl?.status === 'ok' ? 'text-emerald-300' : 'text-amber-300'} />
                        <Row label="SEO (supervision)" value={sup.seo?.score != null ? `${sup.seo.score}/100` : '—'} />
                        <Row label="Avis Google" value={sup.reviews?.rating ? `${sup.reviews.rating}★ · ${sup.reviews.total ?? '?'} avis${sup.reviews.new_reviews ? ` (+${sup.reviews.new_reviews})` : ''}` : '—'} />
                        <Row label="Contrôlé le" value={fmtDate(sup.checked_at || sup.timestamp)} />
                    </>
                )}
            </Section>

            <Section title="Audit technique du site"
                right={m.audit.score != null && <span className="text-xs font-bold text-white">{Math.round(m.audit.score)}/100 {m.audit.grade && `· ${m.audit.grade}`}</span>}>
                {m.audit.score == null ? (
                    <p className="text-sm text-slate-400">Site non audité.</p>
                ) : (
                    <>
                        {Object.entries(m.audit.sections).map(([k, v]) => (
                            <div key={k}>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-slate-300">{{ technical: 'Technique', seo_local: 'SEO local', conversion: 'Conversion', trust: 'Confiance' }[k] || k}</span>
                                    <span className="text-slate-400">{v.score}/{v.max}</span>
                                </div>
                                <Bar value={v.score} max={v.max} />
                            </div>
                        ))}
                        <Row label="Temps de réponse" value={m.audit.response_time_ms != null ? `${m.audit.response_time_ms} ms` : '—'}
                            tone={m.audit.response_time_ms > 2500 ? 'text-amber-300' : 'text-slate-100'} />
                        <Row label="Code HTTP" value={m.audit.http_status} />
                        <Row label="Audité le" value={fmtDate(m.audit.audited_at)} />
                        {m.audit.issues.length > 0 && (
                            <ul className="space-y-1 pt-1">
                                {m.audit.issues.map((i, k) => (
                                    <li key={k} className="text-xs text-slate-300">
                                        <span className={i.severity === 'high' ? 'text-red-400' : i.severity === 'medium' ? 'text-amber-400' : 'text-slate-400'}>●</span>{' '}
                                        <b>{i.title}</b> — {i.recommendation}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </>
                )}
            </Section>

            <Section title="Santé digitale" right={<span className="text-xs font-bold text-white">{Math.round(m.digital_health.score)}/100</span>}>
                {m.digital_health.criteria.map((c) => (
                    <div key={c.label}>
                        <div className="flex justify-between text-xs mb-1">
                            <span className="text-slate-200">{c.label}</span>
                            <span className="text-slate-400">{c.pts}/{c.max}</span>
                        </div>
                        <Bar value={c.pts} max={c.max} />
                        <p className="text-[11px] text-slate-400 mt-0.5">{c.detail}</p>
                    </div>
                ))}
            </Section>

            <Section title="Statistiques du site (30 j vs 30 j précédents)">
                {statRows.map(([label, k]) => {
                    const d = pct(s.last30[k], s.prev30[k]);
                    return (
                        <Row key={k} label={label}
                            value={<>{s.last30[k]} {d != null && <span className={d >= 0 ? 'text-emerald-400' : 'text-red-400'}>({d >= 0 ? '+' : ''}{d} %)</span>}</>} />
                    );
                })}
            </Section>

            <Section title="Demandes de modification">
                <Row label="En attente" value={m.requests.open} tone={m.requests.open ? 'text-amber-300' : 'text-slate-100'} />
                <Row label="Plus ancienne en attente" value={m.requests.oldest_open_days != null ? `${m.requests.oldest_open_days} j` : '—'} />
                <Row label="Ce mois-ci" value={`${m.requests.this_month}${m.requests.quota != null ? ` / ${m.requests.quota}` : ' (illimité)'}`} />
                <Row label="Total" value={m.requests.total} />
            </Section>

            <Section title="Onboarding & contenus">
                <div>
                    <div className="flex justify-between text-xs mb-1"><span className="text-slate-300">Complétude</span><span className="text-slate-400">{Math.round(m.onboarding.percent)} %</span></div>
                    <Bar value={m.onboarding.percent} />
                </div>
                {m.onboarding.missing.length > 0 && (
                    <p className="text-xs text-amber-300">Manque : {m.onboarding.missing.map((x) => x.label || x.path).join(', ')}</p>
                )}
                <Row label="Médias" value={Object.entries(m.onboarding.media).map(([k, v]) => `${k} ${v}`).join(' · ')} />
            </Section>

            <Section title="Accès du client">
                <Row label="Email" value={m.client_access.email || '—'} />
                <Row label="Dernière connexion" value={m.client_access.last_login ? `${fmtDate(m.client_access.last_login)} (il y a ${m.client_access.last_login_days} j)` : 'Jamais'} />
                <Row label="Connexions (30 j)" value={m.client_access.logins_30d} />
            </Section>

            <Section title="Réceptionniste IA">
                <Row label="Statut" value={r.status || '—'} />
                {r.days_left != null && <Row label="Jours restants" value={r.days_left} />}
                {r.stats && (
                    <>
                        <Row label="Appels reçus" value={r.stats.received} />
                        <Row label="Appels récupérés" value={r.stats.recovered} />
                        <Row label="Urgences" value={r.stats.urgent} />
                    </>
                )}
            </Section>

            <p className="text-[11px] text-slate-500 text-center">Mis à jour le {fmtDate(m.generated_at)}</p>
        </div>
    );
}

export default function ClientViewModal({ businessId, onClose }) {
    const [url, setUrl] = useState('');
    const [maint, setMaint] = useState(null);
    const [error, setError] = useState('');
    const [supervising, setSupervising] = useState(false);
    const [frameKey, setFrameKey] = useState(0);

    const loadView = async () => {
        setUrl('');
        try {
            const r = await axios.post(`/businesses/${businessId}/client-view`);
            // Même origine que le cockpit : chemin relatif, pour rester sur le même domaine.
            const u = new URL(r.data.url);
            setUrl(u.pathname + u.search);
            setFrameKey((k) => k + 1);
        } catch (e) {
            setError(e.response?.data?.detail || "Impossible d'ouvrir l'espace du client.");
        }
    };
    const loadMaint = async () => {
        try {
            const r = await axios.get(`/businesses/${businessId}/maintenance`);
            setMaint(r.data);
        } catch (e) {
            setError(e.response?.data?.detail || 'Impossible de charger la maintenance.');
        }
    };
    const supervise = async () => {
        setSupervising(true);
        try {
            await axios.post(`/monitor/${businessId}`, null, { timeout: 60000 });
            await loadMaint();
        } catch (e) {
            setError(e.response?.data?.detail || 'Supervision impossible.');
        } finally {
            setSupervising(false);
        }
    };

    useEffect(() => {
        loadView();
        loadMaint();
        const onKey = (e) => e.key === 'Escape' && onClose();
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [businessId]);

    return (
        <div className="fixed inset-0 z-[5000] bg-slate-950/85 backdrop-blur-sm flex flex-col" role="dialog" aria-modal="true" aria-label="Tableau de bord du client">
            <div className="flex items-center justify-between gap-3 px-4 py-3 bg-slate-900 border-b border-white/10">
                <div className="min-w-0">
                    <h3 className="font-bold text-white truncate">Tableau de bord client{maint?.name ? ` · ${maint.name}` : ''}</h3>
                    <p className="text-xs text-slate-400">À gauche, la vue exacte du client. À droite, les informations de maintenance.</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                    <button onClick={() => { loadView(); loadMaint(); }} title="Actualiser"
                        className="p-2 rounded-lg border border-white/10 text-slate-300 hover:bg-white/5"><RefreshCw className="w-4 h-4" /></button>
                    <button onClick={onClose} title="Fermer (Échap)"
                        className="p-2 rounded-lg border border-white/10 text-slate-300 hover:bg-white/5"><X className="w-4 h-4" /></button>
                </div>
            </div>
            {error && (
                <div className="mx-4 mt-3 flex items-center gap-2 text-sm text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                    <AlertTriangle className="w-4 h-4" /> {error}
                </div>
            )}
            <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-3 p-3">
                <div className="flex-1 min-h-[60vh] lg:min-h-0 bg-white rounded-xl overflow-hidden">
                    {url ? (
                        <iframe key={frameKey} src={url} title="Espace du client" className="w-full h-full border-0" />
                    ) : (
                        <div className="h-full flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-brand" /></div>
                    )}
                </div>
                <aside className="lg:w-[400px] shrink-0 lg:overflow-y-auto">
                    {maint ? <MaintenancePanel m={maint} onSupervise={supervise} supervising={supervising} />
                        : <div className="h-40 flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-brand" /></div>}
                </aside>
            </div>
        </div>
    );
}
