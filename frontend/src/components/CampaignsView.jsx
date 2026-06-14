import React, { useState, useEffect } from 'react';
import {
    ExternalLink, CheckCircle2, ChevronLeft, Monitor, Smartphone,
    Mail, FileText, Image as ImageIcon, Check, Loader2, PlayCircle,
    RefreshCw, Rocket, Share2, CreditCard, Users, Download, Search,
    Copy, AtSign
} from 'lucide-react';
import AgentTracker from './AgentTracker';
import PricingModal from './PricingModal';
import axios from 'axios';

const API_BASE_URL = '';

function CampaignsView({ businesses, onDeploy, initialSelectedId, onRegenerate, onGoToCrm }) {
    const campaigns = businesses.filter(b =>
        ['processing', 'pending_validation', 'completed', 'error'].includes(b.status)
    );

    const [selectedCampaign, setSelectedCampaign] = useState(null);
    const [activeTab, setActiveTab]               = useState('report');
    const [previewMode, setPreviewMode]           = useState('desktop');
    const [previewViewed, setPreviewViewed]       = useState(false);
    const [showPricing, setShowPricing]           = useState(false);
    const [copied, setCopied]                     = useState(false);
    const [emailBody, setEmailBody]               = useState('');
    const [findingEmail, setFindingEmail]         = useState(false);
    const [foundEmails, setFoundEmails]           = useState(null);
    const [recipientEmail, setRecipientEmail]     = useState('');

    const fetchDetail = async (id) => {
        try {
            const response = await axios.get(`${API_BASE_URL}/businesses/${id}`);
            setSelectedCampaign(response.data);
        } catch (error) {
            console.error('Error fetching campaign detail:', error);
        }
    };

    const handleSelect = (camp) => {
        setSelectedCampaign(camp);
        setPreviewViewed(false);
        setActiveTab(camp.status === 'pending_validation' ? 'preview' : 'report');
        setFoundEmails(null);
        setRecipientEmail('');
        setEmailBody('');
        fetchDetail(camp.id);
    };

    useEffect(() => {
        if (initialSelectedId) {
            const camp = campaigns.find(c => c.id === initialSelectedId);
            if (camp) handleSelect(camp);
        }
    }, [initialSelectedId]);

    useEffect(() => {
        if (selectedCampaign) {
            const updated = campaigns.find(c => c.id === selectedCampaign.id);
            if (updated && JSON.stringify(updated) !== JSON.stringify(selectedCampaign)) {
                setSelectedCampaign(updated);
            }
        }
    }, [businesses]);

    // Auto-refresh while processing so tabs appear when done
    useEffect(() => {
        if (!selectedCampaign || selectedCampaign.status !== 'processing') return;
        const id = setInterval(async () => {
            try {
                const r = await axios.get(`${API_BASE_URL}/businesses/${selectedCampaign.id}`);
                if (r.data.status !== 'processing') {
                    setSelectedCampaign(r.data);
                    // On error → report tab (shows error banner), on success → preview
                    setActiveTab(r.data.status === 'error' ? 'report' : 'preview');
                }
            } catch {}
        }, 4000);
        return () => clearInterval(id);
    }, [selectedCampaign?.id, selectedCampaign?.status]);

    const tryParseJSON = (v) => {
        try { const o = JSON.parse(v); if (o && typeof o === 'object') return o; } catch { }
        return null;
    };

    if (selectedCampaign) {
        const data = tryParseJSON(selectedCampaign.generated_copy)
            || (typeof selectedCampaign.generated_copy === 'object' ? selectedCampaign.generated_copy : {})
            || {};

        // Extract & clean email
        let emailText = data.email || '';
        const markerMatch = emailText.match(/--- EMAIL CONTENT START ---([\s\S]*?)--- EMAIL CONTENT END ---/);
        if (markerMatch) emailText = markerMatch[1].trim();

        // Deployment URL (completed) or fallback
        const deployedUrl = selectedCampaign.deployment_url || '';
        const hasHtml      = !!(selectedCampaign.generated_html || data.html);
        const isPending    = selectedCampaign.status === 'pending_validation';
        const isCompleted  = selectedCampaign.status === 'completed';
        const isProcessing = selectedCampaign.status === 'processing';
        const isError      = selectedCampaign.status === 'error';

        // Photo list
        const allPhotos = [];
        if (data.ai_photos) {
            const matches = data.ai_photos.match(/(https?:\/\/[^\s"',]+)/g);
            if (matches) matches.forEach(u => { const c = u.replace(/[\])]$/, ''); if (!allPhotos.includes(c)) allPhotos.push(c); });
        }

        const previewSrc = `${API_BASE_URL}/preview/${selectedCampaign.id}`;

        return (
            <>
            <div className="w-full h-full bg-slate-900 overflow-y-auto p-8" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,.1) transparent' }}>
                <div className="max-w-6xl mx-auto flex flex-col">

                    {/* Header */}
                    <div className="flex items-center space-x-4 mb-6">
                        <button onClick={() => setSelectedCampaign(null)} className="p-2 hover:bg-white/10 rounded-xl transition-colors">
                            <ChevronLeft className="w-6 h-6" />
                        </button>
                        <div>
                            <h2 className="text-2xl font-bold">{selectedCampaign.name}</h2>
                            <p className="text-sm text-slate-400">
                                Score Digital : <span className={`font-bold ${selectedCampaign.potential_score >= 7 ? 'text-emerald-400' : selectedCampaign.potential_score >= 2.5 ? 'text-amber-400' : 'text-red-400'}`}>{selectedCampaign.potential_score}/10</span>
                                {isCompleted && deployedUrl && (
                                    <> · <a href={deployedUrl} target="_blank" rel="noopener noreferrer"
                                           className="text-brand hover:underline ml-1">
                                        Site live ↗
                                    </a></>
                                )}
                            </p>
                        </div>
                        {(isPending || isCompleted) && (
                            <div className="ml-auto flex items-center gap-2 flex-wrap justify-end">
                                {/* Share demo */}
                                <button
                                    onClick={() => {
                                        navigator.clipboard.writeText(`${window.location.origin}/demo/${selectedCampaign.id}`);
                                        setCopied(true);
                                        setTimeout(() => setCopied(false), 2000);
                                    }}
                                    className="flex items-center gap-2 text-xs border border-white/10 px-3 py-1.5 rounded-xl hover:bg-white/5 transition-colors"
                                >
                                    {copied ? (
                                        <><Check className="w-3 h-3 text-emerald-400" /> Copié !</>
                                    ) : (
                                        <><Share2 className="w-3 h-3" /> Partager démo</>
                                    )}
                                </button>

                                {/* ── Go to CRM ── */}
                                <button
                                    onClick={onGoToCrm}
                                    className="flex items-center gap-2 text-xs bg-violet-600 hover:bg-violet-500 text-white px-3 py-1.5 rounded-xl font-bold transition-colors"
                                >
                                    <Users className="w-3 h-3" />
                                    Gérer dans le CRM →
                                </button>

                                {/* Subscribe */}
                                {selectedCampaign.subscription_status !== 'active' && (
                                    <button
                                        onClick={() => setShowPricing(true)}
                                        className="flex items-center gap-2 text-xs bg-brand text-white px-3 py-1.5 rounded-xl font-bold hover:bg-blue-600 transition-colors"
                                    >
                                        <CreditCard className="w-3 h-3" />
                                        Créer abonnement
                                    </button>
                                )}

                                {selectedCampaign.subscription_status === 'active' && (
                                    <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl font-bold">
                                        <CheckCircle2 className="w-3 h-3" /> Client actif · {selectedCampaign.plan_tier}
                                    </span>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Tabs */}
                    <div className="flex items-center space-x-2 border-b border-white/10 mb-6 pb-2 overflow-x-auto custom-scrollbar flex-shrink-0">
                        {[
                            { id: 'report',  label: 'Analyse & Copy',     icon: FileText,    show: true },
                            { id: 'photos',  label: 'Photos',              icon: ImageIcon,   show: allPhotos.length > 0 },
                            { id: 'email',   label: 'Email Prospect',      icon: Mail,        show: !isProcessing },
                            { id: 'preview', label: 'Aperçu du Site',      icon: Monitor,     show: hasHtml || isPending || isCompleted || (isError && hasHtml) },
                            { id: 'tracker', label: 'Agent Cockpit',       icon: PlayCircle,  show: isProcessing },
                        ].filter(t => t.show).map(tab => (
                            <button key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                                    activeTab === tab.id
                                        ? 'bg-brand text-white'
                                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                                }`}
                            >
                                <tab.icon className={`w-4 h-4 ${tab.id === 'tracker' ? 'animate-pulse text-amber-400' : ''}`} />
                                <span>{tab.label}</span>
                                {tab.id === 'preview' && isPending && !previewViewed && (
                                    <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Tab content */}
                    <div className="flex-1 min-h-[500px] overflow-y-auto">

                        {/* ── REPORT ── */}
                        {activeTab === 'report' && (
                            <div className="glass p-6 rounded-2xl space-y-6">

                                {/* PDF export button */}
                                {(data.report || data.copywriting) && (
                                    <div className="flex justify-end">
                                        <button
                                            onClick={() => {
                                                const w = window.open('', '_blank', 'width=900,height=750');
                                                w.document.write(`<!DOCTYPE html><html lang="fr"><head>
                                                    <meta charset="UTF-8">
                                                    <title>Rapport — ${selectedCampaign.name}</title>
                                                    <style>
                                                        body{font-family:Georgia,serif;max-width:780px;margin:40px auto;padding:0 24px;color:#1a1a1a;line-height:1.7}
                                                        h1{font-size:26px;border-bottom:3px solid #0071E3;padding-bottom:12px;margin-bottom:6px}
                                                        .meta{color:#666;font-size:13px;margin-bottom:28px}
                                                        h2{font-size:15px;color:#0071E3;text-transform:uppercase;letter-spacing:.05em;margin-top:36px;margin-bottom:8px}
                                                        pre{white-space:pre-wrap;font-family:Georgia,serif;font-size:14px;margin:0}
                                                        hr{border:none;border-top:1px solid #e5e7eb;margin:28px 0}
                                                        @media print{body{margin:0}button{display:none}}
                                                    </style>
                                                </head><body>
                                                    <h1>${selectedCampaign.name}</h1>
                                                    <div class="meta">${selectedCampaign.address || ''} · Score ${selectedCampaign.potential_score}/10 · ${new Date().toLocaleDateString('fr-FR')}</div>
                                                    <h2>Rapport d'Investigation</h2>
                                                    <pre>${(data.report || '').replace(/</g,'&lt;')}</pre>
                                                    <hr/>
                                                    <h2>Copywriting & Arguments</h2>
                                                    <pre>${(data.copywriting || '').replace(/</g,'&lt;')}</pre>
                                                    <script>window.onload=()=>window.print()</script>
                                                </body></html>`);
                                                w.document.close();
                                            }}
                                            className="flex items-center gap-2 text-xs border border-white/10 px-3 py-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                                        >
                                            <Download className="w-3.5 h-3.5" />
                                            Télécharger PDF
                                        </button>
                                    </div>
                                )}

                                {/* Error state banner + regenerate */}
                                {isError && (
                                    <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                                        <div>
                                            <p className="text-rose-400 font-bold text-sm flex items-center gap-2">
                                                ❌ La génération a échoué
                                            </p>
                                            <p className="text-slate-400 text-xs mt-1">
                                                Une erreur s'est produite durant le processus. Relancez la génération pour réessayer.
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => onRegenerate && onRegenerate(selectedCampaign.id)}
                                            className="flex items-center gap-2 bg-brand text-white px-5 py-2.5 rounded-xl font-bold text-sm hover:bg-brand-dark transition-colors whitespace-nowrap shadow-lg shadow-brand/25"
                                        >
                                            <RefreshCw className="w-4 h-4" />
                                            Régénérer le site
                                        </button>
                                    </div>
                                )}

                                <div>
                                    <h4 className="text-brand font-bold uppercase tracking-wider text-xs mb-2">Rapport d'Investigation</h4>
                                    <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans bg-slate-900/50 p-4 rounded-xl border border-white/5 overflow-y-auto custom-scrollbar" style={{maxHeight:'none'}}>
                                        {data.report || 'Rapport en cours de génération...'}
                                    </pre>
                                </div>
                                <div>
                                    <h4 className="text-brand font-bold uppercase tracking-wider text-xs mb-2">Copywriting & Arguments</h4>
                                    <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans bg-slate-900/50 p-4 rounded-xl border border-white/5 overflow-y-auto custom-scrollbar" style={{maxHeight:'none'}}>
                                        {data.copywriting || 'Copywriting en cours...'}
                                    </pre>
                                </div>
                                <div>
                                    <h4 className="text-brand font-bold uppercase tracking-wider text-xs mb-2">Directives Design</h4>
                                    {(() => {
                                        let d = data.design;
                                        if (!d) return <p className="text-slate-500 text-sm italic">Design en cours...</p>;
                                        try { d = typeof d === 'string' ? JSON.parse(d) : d; } catch {}
                                        if (typeof d === 'object' && d !== null) {
                                            return (
                                                <div className="grid grid-cols-2 gap-3">
                                                    {d.template && <div className="bg-slate-900/50 p-3 rounded-xl border border-white/5"><p className="text-[10px] text-slate-500 uppercase mb-1">Template</p><p className="text-sm text-white font-medium">{d.template}</p></div>}
                                                    {d.mood && <div className="bg-slate-900/50 p-3 rounded-xl border border-white/5"><p className="text-[10px] text-slate-500 uppercase mb-1">Ambiance</p><p className="text-sm text-white font-medium">{d.mood}</p></div>}
                                                    {d.fonts && <div className="bg-slate-900/50 p-3 rounded-xl border border-white/5"><p className="text-[10px] text-slate-500 uppercase mb-1">Typographies</p><p className="text-sm text-white">{d.fonts.heading} / {d.fonts.body}</p></div>}
                                                    {d.colors && <div className="bg-slate-900/50 p-3 rounded-xl border border-white/5"><p className="text-[10px] text-slate-500 uppercase mb-1">Couleurs</p><div className="flex gap-1.5 mt-1">{Object.entries(d.colors).slice(0,5).map(([k,v]) => <div key={k} title={k} className="w-5 h-5 rounded-full border border-white/10" style={{background:v}}/>)}</div></div>}
                                                    {d.unique_angle && <div className="col-span-2 bg-slate-900/50 p-3 rounded-xl border border-white/5"><p className="text-[10px] text-slate-500 uppercase mb-1">Angle unique</p><p className="text-sm text-slate-300">{d.unique_angle}</p></div>}
                                                </div>
                                            );
                                        }
                                        return <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans bg-slate-900/50 p-4 rounded-xl border border-white/5">{String(d)}</pre>;
                                    })()}
                                </div>
                            </div>
                        )}

                        {/* ── PHOTOS ── */}
                        {activeTab === 'photos' && (
                            <div className="glass p-6 rounded-2xl">
                                <h3 className="text-lg font-bold mb-4">Photos disponibles</h3>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {allPhotos.map((url, i) => (
                                        <div key={i} className="aspect-square rounded-xl overflow-hidden border border-white/10">
                                            <img src={url} alt={`Photo ${i + 1}`} className="w-full h-full object-cover hover:scale-105 transition-transform" />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* ── EMAIL ── */}
                        {activeTab === 'email' && (
                            <div className="glass p-6 rounded-2xl flex flex-col gap-4">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-lg font-bold">Email de Prospection</h3>
                                </div>

                                {/* Destinataire */}
                                <div>
                                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Destinataire</p>
                                    <div className="flex gap-2">
                                        <div className="relative flex-1">
                                            <AtSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                            <input
                                                type="email"
                                                value={recipientEmail}
                                                onChange={e => setRecipientEmail(e.target.value)}
                                                placeholder="email@commerce.fr"
                                                className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand"
                                            />
                                        </div>
                                        <button
                                            onClick={async () => {
                                                setFindingEmail(true);
                                                setFoundEmails(null);
                                                try {
                                                    const r = await axios.get(`/businesses/${selectedCampaign.id}/find-email`);
                                                    setFoundEmails(r.data);
                                                    if (r.data.found?.[0]) setRecipientEmail(r.data.found[0]);
                                                    else if (r.data.guesses?.[0]) setRecipientEmail(r.data.guesses[0]);
                                                } catch {}
                                                finally { setFindingEmail(false); }
                                            }}
                                            disabled={findingEmail}
                                            className="flex items-center gap-2 px-3 py-2 bg-violet-600/20 border border-violet-500/30 text-violet-400 rounded-xl text-xs font-bold hover:bg-violet-600/30 transition-colors disabled:opacity-50 whitespace-nowrap"
                                        >
                                            {findingEmail ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                                            Trouver l'email
                                        </button>
                                    </div>

                                    {/* Found emails suggestions */}
                                    {foundEmails && (
                                        <div className="mt-2 space-y-1.5">
                                            {foundEmails.found?.length > 0 && (
                                                <div>
                                                    <p className="text-[10px] text-emerald-400 font-bold mb-1">✅ Trouvés sur le site :</p>
                                                    {foundEmails.found.map(e => (
                                                        <button key={e} onClick={() => setRecipientEmail(e)}
                                                            className={`block text-xs px-2 py-1 rounded-lg mr-1 mb-1 transition-colors ${recipientEmail === e ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-white/5 text-slate-300 hover:bg-white/10'}`}>
                                                            {e}
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                            {foundEmails.guesses?.length > 0 && (
                                                <div>
                                                    <p className="text-[10px] text-amber-400 font-bold mb-1">💡 Suggestions probables :</p>
                                                    {foundEmails.guesses.map(e => (
                                                        <button key={e} onClick={() => setRecipientEmail(e)}
                                                            className={`inline-block text-xs px-2 py-1 rounded-lg mr-1 mb-1 transition-colors ${recipientEmail === e ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-white/5 text-slate-300 hover:bg-white/10'}`}>
                                                            {e}
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                            {!foundEmails.found?.length && !foundEmails.guesses?.length && (
                                                <p className="text-xs text-slate-500 italic">Aucun email trouvé — entrez-le manuellement.</p>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Email body */}
                                <div>
                                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Corps de l'email</p>
                                    <textarea
                                        rows={12}
                                        className="w-full bg-slate-900/50 text-white p-4 rounded-xl border border-white/10 resize-none focus:outline-none focus:border-brand custom-scrollbar text-sm leading-relaxed"
                                        value={emailBody || emailText || ''}
                                        onChange={e => setEmailBody(e.target.value)}
                                        placeholder="Email en cours de génération..."
                                    />
                                </div>

                                {/* Actions */}
                                <div className="flex items-center justify-between gap-3">
                                    <button
                                        onClick={() => {
                                            const body = emailBody || emailText || '';
                                            navigator.clipboard.writeText(body);
                                        }}
                                        className="flex items-center gap-2 text-xs border border-white/10 px-3 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                                    >
                                        <Copy className="w-3.5 h-3.5" />
                                        Copier le texte
                                    </button>
                                    <a
                                        href={`mailto:${recipientEmail}?subject=Votre site web professionnel — ${selectedCampaign.name}&body=${encodeURIComponent(emailBody || emailText || '')}`}
                                        className="flex items-center gap-2 bg-brand text-white px-5 py-2 rounded-xl font-bold hover:bg-blue-600 transition-colors text-sm"
                                    >
                                        <Mail className="w-4 h-4" />
                                        Ouvrir dans Gmail / Mail
                                    </a>
                                </div>
                            </div>
                        )}

                        {/* ── PREVIEW ── */}
                        {activeTab === 'preview' && (
                            <div className="flex flex-col h-full gap-3" style={{ minHeight: '600px' }}>

                                {/* Browser chrome bar */}
                                <div className="flex items-center gap-3 px-4 py-2.5 bg-slate-800 rounded-xl border border-white/10">
                                    <div className="flex gap-1.5">
                                        <div className="w-3 h-3 rounded-full bg-rose-500" />
                                        <div className="w-3 h-3 rounded-full bg-amber-500" />
                                        <div className="w-3 h-3 rounded-full bg-emerald-500" />
                                    </div>
                                    <span className="flex-1 text-center text-xs text-slate-400 font-mono truncate">
                                        {API_BASE_URL}/preview/{selectedCampaign.id}
                                    </span>
                                    <div className="flex items-center gap-1">
                                        <button
                                            title="Vue bureau"
                                            onClick={() => setPreviewMode('desktop')}
                                            className={`p-1.5 rounded-lg transition-colors ${previewMode === 'desktop' ? 'bg-brand text-white' : 'text-slate-400 hover:bg-white/10'}`}
                                        >
                                            <Monitor className="w-4 h-4" />
                                        </button>
                                        <button
                                            title="Vue mobile"
                                            onClick={() => setPreviewMode('mobile')}
                                            className={`p-1.5 rounded-lg transition-colors ${previewMode === 'mobile' ? 'bg-brand text-white' : 'text-slate-400 hover:bg-white/10'}`}
                                        >
                                            <Smartphone className="w-4 h-4" />
                                        </button>
                                        <a href={previewSrc} target="_blank" rel="noopener noreferrer"
                                           className="p-1.5 rounded-lg text-slate-400 hover:text-brand hover:bg-white/10 transition-colors ml-1">
                                            <ExternalLink className="w-4 h-4" />
                                        </a>
                                    </div>
                                </div>

                                {/* Iframe container */}
                                <div className="flex-1 bg-slate-950 rounded-xl overflow-hidden border border-white/10 flex items-center justify-center" style={{ minHeight: '500px' }}>
                                    <div className={previewMode === 'mobile'
                                        ? 'w-[390px] h-[844px] border-4 border-slate-600 rounded-[2.5rem] overflow-hidden shadow-2xl'
                                        : 'w-full h-full'
                                    } style={previewMode !== 'mobile' ? { minHeight: '500px' } : {}}>
                                        {hasHtml || isPending ? (
                                            <iframe
                                                key={`${selectedCampaign.id}-${previewMode}`}
                                                src={previewSrc}
                                                className="w-full h-full border-none bg-white"
                                                title="Site Preview"
                                                onLoad={() => setPreviewViewed(true)}
                                                style={{ minHeight: previewMode === 'desktop' ? '500px' : undefined }}
                                            />
                                        ) : (
                                            <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-3">
                                                <Loader2 className="w-8 h-8 animate-spin text-brand" />
                                                <p className="text-sm">Génération du site en cours...</p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Action bar */}
                                <div className="flex items-center justify-between px-4 py-3 bg-slate-800 rounded-xl border border-white/10">
                                    <button
                                        onClick={() => onRegenerate && onRegenerate(selectedCampaign.id)}
                                        disabled={isProcessing}
                                        className="flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-white/10 px-4 py-2 rounded-xl hover:bg-white/5 transition-colors disabled:opacity-40"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        Régénérer
                                    </button>

                                    <div className="flex items-center gap-3">
                                        {!previewViewed && !isCompleted && (
                                            <span className="text-xs text-amber-400 animate-pulse">
                                                👁️ Visualisez le site pour débloquer le déploiement
                                            </span>
                                        )}
                                        <button
                                            onClick={() => onDeploy && onDeploy(selectedCampaign.id)}
                                            disabled={(!previewViewed && !isCompleted) || isProcessing}
                                            className="flex items-center gap-2 bg-brand text-white px-6 py-2.5 rounded-xl font-bold hover:bg-brand-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-brand/25"
                                        >
                                            {isCompleted ? (
                                                <><CheckCircle2 className="w-4 h-4" /> Déployé sur Vercel</>
                                            ) : isProcessing ? (
                                                <><Loader2 className="w-4 h-4 animate-spin" /> Déploiement...</>
                                            ) : (
                                                <><Rocket className="w-4 h-4" /> Déployer sur Vercel</>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ── TRACKER ── */}
                        {activeTab === 'tracker' && (
                            <div className="glass p-6 rounded-2xl h-full overflow-hidden">
                                <AgentTracker isProcessing={true} businessId={selectedCampaign.id} />
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Pricing Modal */}
            <PricingModal
                isOpen={showPricing}
                onClose={() => setShowPricing(false)}
                businessId={selectedCampaign.id}
                businessName={selectedCampaign.name}
            />
            </>
        );
    }

    // ── Campaign list ──
    return (
        <div className="w-full h-full bg-slate-900 overflow-y-auto p-8" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,.1) transparent' }}>
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Campagnes</h2>
                        <p className="text-slate-400 mt-1">Sites générés et en attente de déploiement.</p>
                    </div>
                    <div className="glass px-6 py-3 rounded-xl flex items-center gap-6">
                        <div className="text-center">
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Actives</p>
                            <p className="text-xl font-bold text-amber-400">{campaigns.filter(c => c.status === 'processing').length}</p>
                        </div>
                        <div className="w-px h-8 bg-white/10" />
                        <div className="text-center">
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">À valider</p>
                            <p className="text-xl font-bold text-blue-400">{campaigns.filter(c => c.status === 'pending_validation').length}</p>
                        </div>
                        <div className="w-px h-8 bg-white/10" />
                        <div className="text-center">
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Déployées</p>
                            <p className="text-xl font-bold text-emerald-400">{campaigns.filter(c => c.status === 'completed').length}</p>
                        </div>
                    </div>
                </div>

                {campaigns.length === 0 ? (
                    <div className="border border-white/10 bg-slate-800/50 p-12 rounded-2xl text-center">
                        <div className="text-5xl mb-4">🎯</div>
                        <h3 className="text-xl font-bold text-white mb-2">Aucune campagne active</h3>
                        <p className="text-slate-300 mb-1">Pour démarrer :</p>
                        <ol className="text-slate-400 text-sm space-y-1 mt-3 text-left inline-block">
                            <li className="flex items-start gap-2"><span className="text-brand font-bold">1.</span>Tapez une ville dans la barre de recherche à gauche</li>
                            <li className="flex items-start gap-2"><span className="text-brand font-bold">2.</span>Cliquez sur un commerce dans la liste ou sur la carte</li>
                            <li className="flex items-start gap-2"><span className="text-brand font-bold">3.</span>Cliquez sur <strong className="text-white">✨ Créer les Actifs Numériques</strong></li>
                        </ol>
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {campaigns.map((camp) => (
                            <div key={camp.id}
                                 onClick={() => handleSelect(camp)}
                                 className="glass p-6 rounded-2xl flex items-center justify-between group hover:bg-white/5 transition-colors border border-transparent hover:border-white/10 cursor-pointer"
                            >
                                <div className="flex items-center gap-5">
                                    <div className={`w-11 h-11 rounded-full flex items-center justify-center font-bold text-lg ${
                                        camp.status === 'completed'          ? 'bg-emerald-500/20 text-emerald-400' :
                                        camp.status === 'pending_validation' ? 'bg-blue-500/20 text-blue-400' :
                                        camp.status === 'processing'         ? 'bg-amber-500/20 text-amber-400' :
                                        'bg-rose-500/20 text-rose-400'
                                    }`}>
                                        {camp.name.charAt(0)}
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-lg group-hover:text-brand transition-colors">{camp.name}</h3>
                                        <div className="flex items-center gap-3 mt-0.5 text-sm text-slate-400">
                                            <span>Score : {camp.potential_score}/10</span>
                                            <span>·</span>
                                            <span className={
                                                camp.status === 'completed'          ? 'text-emerald-400' :
                                                camp.status === 'pending_validation' ? 'text-blue-400' :
                                                camp.status === 'processing'         ? 'text-amber-400' : 'text-rose-400'
                                            }>
                                                {camp.status === 'processing'         ? '⏳ En cours...' :
                                                 camp.status === 'pending_validation' ? '👁️ À valider' :
                                                 camp.status === 'completed'          ? '✅ Déployé' : '❌ Erreur'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <button className="px-4 py-2 rounded-xl border border-white/10 bg-brand/80 hover:bg-brand text-white text-sm font-bold transition-colors">
                                    {camp.status === 'pending_validation' ? 'Valider →' : 'Gérer →'}
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default CampaignsView;
