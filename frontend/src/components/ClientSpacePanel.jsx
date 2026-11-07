import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReceptionistPanel from './ReceptionistPanel';
import ClientViewModal from './ClientViewModal';
import { Loader2, Copy, Check, Send, ExternalLink, Inbox, AlertTriangle, ImagePlus, MonitorSmartphone } from 'lucide-react';

// Onglet « Espace client » : lien de connexion PulsePro et demandes de modification.
const CATS = {
    horaires: "Changement d'horaires",
    actualite: 'Ajouter une actualité',
    photos: 'Remplacer des photos',
    textes: 'Modifier un texte',
    autre: 'Autre demande',
};
const STATUSES = [
    { id: 'nouvelle', label: 'Reçue', cls: 'text-sky-300 bg-sky-500/10 border-sky-500/20' },
    { id: 'en_cours', label: 'En cours', cls: 'text-amber-300 bg-amber-500/10 border-amber-500/20' },
    { id: 'terminee', label: 'Terminée', cls: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20' },
];

function ClientSpacePanel({ businessId }) {
    const [data, setData]       = useState(null);
    const [error, setError]     = useState('');
    const [copied, setCopied]   = useState(false);
    const [sending, setSending] = useState(false);
    const [notice, setNotice]   = useState('');
    const [applying, setApplying] = useState(false);
    const [applied, setApplied]   = useState('');
    const [showView, setShowView] = useState(false);

    const load = async () => {
        try {
            const r = await axios.get(`/businesses/${businessId}/client-space`);
            setData(r.data);
            setError('');
        } catch (e) {
            setError(e.response?.data?.detail || "Impossible de charger l'espace client.");
        }
    };

    useEffect(() => { setData(null); load(); }, [businessId]);

    const copy = () => {
        navigator.clipboard.writeText(data.login_url);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    // Photos et logo du client appliqués au site actuel, sans repasser par l'IA.
    const applyClientContent = async () => {
        setApplying(true);
        setApplied('');
        try {
            const r = await axios.post(`/businesses/${businessId}/apply-client-content`);
            const d = r.data;
            if (!d.client_photos && !d.logo_added && !d.changed) {
                setApplied("Le client n'a encore déposé ni photo ni logo dans son espace.");
            } else if (!d.changed) {
                setApplied('Le site contient déjà les photos et le logo du client.');
            } else {
                setApplied(`✅ ${d.photos_placed} photo(s)${d.logo_added ? ' et le logo' : ''} du client appliqué(s) au site. Ouvrez l'onglet « Aperçu du Site » pour vérifier.`);
            }
        } catch (e) {
            setApplied(e.response?.data?.detail || "Impossible d'appliquer les photos.");
        } finally {
            setApplying(false);
        }
    };

    const sendLink = async () => {
        setSending(true);
        setNotice('');
        try {
            const r = await axios.post(`/businesses/${businessId}/client-space/send-link`);
            setNotice(`Lien envoyé à ${r.data.to}.`);
        } catch (e) {
            setNotice(e.response?.data?.detail || 'Envoi impossible.');
        } finally {
            setSending(false);
        }
    };

    const setStatus = async (id, status) => {
        const r = await axios.patch(`/client-requests/${id}`, { status });
        setData(prev => ({ ...prev, requests: prev.requests.map(q => (q.id === id ? r.data : q)) }));
    };

    if (error) {
        return (
            <div className="glass p-6 rounded-2xl flex items-center gap-3 text-amber-300">
                <AlertTriangle className="w-5 h-5" /> {error}
            </div>
        );
    }
    if (!data) {
        return <div className="glass p-10 rounded-2xl flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-brand" /></div>;
    }

    const open = data.requests.filter(r => r.status !== 'terminee').length;

    return (
        <div className="space-y-4">
            {showView && <ClientViewModal businessId={businessId} onClose={() => setShowView(false)} />}
            <div className="bg-slate-800 border border-brand/30 p-5 rounded-2xl flex items-center justify-between gap-4 flex-wrap">
                <div>
                    <h3 className="font-bold text-white">Tableau de bord du client</h3>
                    <p className="text-sm text-slate-400 mt-1">
                        Ouvre son espace exactement comme il le voit, avec à côté les infos de maintenance :
                        alertes, abonnement, site, SSL, audit, statistiques, demandes, connexions.
                    </p>
                </div>
                <button onClick={() => setShowView(true)}
                    className="flex items-center gap-2 text-sm bg-brand text-white px-4 py-2.5 rounded-xl font-bold hover:bg-blue-600">
                    <MonitorSmartphone className="w-4 h-4" /> Voir le tableau de bord du client
                </button>
            </div>
            <ReceptionistPanel businessId={businessId} />
            <div className="glass p-6 rounded-2xl space-y-4">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                        <h3 className="font-bold text-white">Accès du client à son espace PulsePro</h3>
                        <p className="text-sm text-slate-400 mt-1">
                            Le client y complète ses informations et ses photos, valide son site, paie, puis suit ses
                            statistiques et demande ses modifications.
                        </p>
                    </div>
                    <span className={`text-xs font-bold px-3 py-1.5 rounded-xl border ${data.status === 'live'
                        ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20'
                        : 'text-sky-300 bg-sky-500/10 border-sky-500/20'}`}>
                        {data.status === 'live' ? 'Site en ligne' : 'Onboarding'} · {data.media_count} média(s)
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    <input readOnly value={data.login_url}
                        className="flex-1 min-w-0 bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-slate-300" />
                    <button onClick={copy} className="flex items-center gap-2 text-xs border border-white/10 px-3 py-2 rounded-xl hover:bg-white/5">
                        {copied ? <><Check className="w-3.5 h-3.5 text-emerald-400" /> Copié</> : <><Copy className="w-3.5 h-3.5" /> Copier</>}
                    </button>
                    <a href={data.login_url} target="_blank" rel="noopener noreferrer"
                        className="p-2 rounded-xl border border-white/10 text-slate-400 hover:text-brand hover:bg-white/5" title="Ouvrir l'espace du client">
                        <ExternalLink className="w-4 h-4" />
                    </a>
                </div>
                <p className="text-xs text-slate-500">
                    Lien personnel et permanent : ne l'envoie qu'au client. Il peut aussi se connecter seul depuis la page
                    /espace avec son email ({data.owner_email || 'à renseigner dans le CRM'}).
                </p>

                <div className="flex items-center gap-3 flex-wrap">
                    <button onClick={sendLink} disabled={sending || !data.owner_email || !data.smtp_ready}
                        className="flex items-center gap-2 text-sm bg-brand text-white px-4 py-2 rounded-xl font-bold hover:bg-blue-600 disabled:opacity-40">
                        {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        Envoyer un lien de connexion par email
                    </button>
                    {!data.smtp_ready && <span className="text-xs text-amber-300">Envoi d'emails non configuré (SMTP) : copie le lien.</span>}
                    {notice && <span className="text-xs text-slate-300">{notice}</span>}
                </div>
            </div>

            <div className="glass p-6 rounded-2xl space-y-3">
                <h3 className="font-bold text-white">Photos et logo du client dans le site</h3>
                <p className="text-sm text-slate-400">
                    Remplace les images du site actuel par les photos déposées par le client (façade en premier) et
                    ajoute son logo, sans relancer l'IA. C'est aussi fait automatiquement à chaque déploiement.
                </p>
                <div className="flex items-center gap-3 flex-wrap">
                    <button onClick={applyClientContent} disabled={applying}
                        className="flex items-center gap-2 text-sm bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl font-bold disabled:opacity-40">
                        {applying ? <Loader2 className="w-4 h-4 animate-spin" /> : <ImagePlus className="w-4 h-4" />}
                        Appliquer ses photos et son logo au site
                    </button>
                    {applied && <span className="text-xs text-slate-300">{applied}</span>}
                </div>
            </div>

            <div className="glass p-6 rounded-2xl">
                <h3 className="font-bold text-white mb-4">
                    Demandes de modification {open > 0 && <span className="ml-2 text-xs text-amber-300">{open} à traiter</span>}
                </h3>
                {data.requests.length === 0 ? (
                    <p className="text-sm text-slate-500 flex items-center gap-2"><Inbox className="w-4 h-4" /> Aucune demande pour l'instant.</p>
                ) : (
                    <ul className="space-y-3">
                        {data.requests.map(r => (
                            <li key={r.id} className="border border-white/10 rounded-xl p-4">
                                <div className="flex items-center justify-between gap-3 flex-wrap">
                                    <span className="text-sm font-bold text-white">{CATS[r.cat] || r.cat}</span>
                                    <div className="flex gap-1">
                                        {STATUSES.map(s => (
                                            <button key={s.id} onClick={() => setStatus(r.id, s.id)}
                                                className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${r.status === s.id ? s.cls : 'border-white/10 text-slate-500 hover:text-white'}`}>
                                                {s.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <p className="text-sm text-slate-300 mt-2 whitespace-pre-wrap">{r.msg}</p>
                                <p className="text-xs text-slate-500 mt-1">{r.date && new Date(r.date).toLocaleString('fr-FR')}</p>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

export default ClientSpacePanel;
