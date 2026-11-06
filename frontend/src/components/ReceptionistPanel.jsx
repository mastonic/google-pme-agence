import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Loader2, PhoneCall, PhoneIncoming, PhoneForwarded, AlertTriangle, Sparkles, RefreshCw } from 'lucide-react';

// Carte « Réceptionniste IA » : essai 30 jours, statistiques d'appels et activation.
// API : GET /businesses/{id}/receptionist, POST /businesses/{id}/receptionist/activate
// Réponse : { status: 'inactive'|'trial'|'active'|'expired', days_left, stats: {received, recovered, urgent}, twilio_number }
const TRIAL_DAYS = 30;

const STATUS_UI = {
    inactive: { label: 'Non activée', cls: 'text-slate-300 bg-white/5 border-white/10' },
    trial:    { label: 'Essai gratuit', cls: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20' },
    active:   { label: 'Active', cls: 'text-sky-300 bg-sky-500/10 border-sky-500/20' },
    expired:  { label: 'Essai terminé', cls: 'text-amber-300 bg-amber-500/10 border-amber-500/20' },
};

function Stat({ icon: Icon, label, value, accent }) {
    return (
        <div className="border border-white/10 rounded-xl p-4 flex flex-col gap-1">
            <span className="text-xs text-slate-400 flex items-center gap-1.5"><Icon className="w-3.5 h-3.5" /> {label}</span>
            <span className={`text-2xl font-bold ${accent || 'text-white'}`}>{Number.isFinite(value) ? value : 0}</span>
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
            // 404 = service pas encore disponible pour ce compte : on affiche l'état « non activée ».
            if (e.response?.status === 404) {
                setData({ status: 'inactive' });
                setError('');
            } else {
                setError(e.response?.data?.detail || 'Impossible de charger la réceptionniste IA.');
            }
        } finally {
            setLoading(false);
        }
    }, [businessId]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => { setData(null); load(); }, [load]);

    const activate = async () => {
        setActivating(true);
        setError('');
        try {
            const r = await axios.post(`/businesses/${businessId}/receptionist/activate`, {});
            if (r.data && r.data.status) setData(r.data);
            else await load();
        } catch (e) {
            setError(e.response?.data?.detail || "L'activation a échoué. Réessayez dans un instant.");
        } finally {
            setActivating(false);
        }
    };

    if (loading && !data) {
        return <div className="glass p-8 rounded-2xl flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-brand" /></div>;
    }

    const status   = STATUS_UI[data?.status] ? data.status : 'inactive';
    const ui       = STATUS_UI[status];
    const stats    = data?.stats || {};
    const daysLeft = Math.max(0, Number(data?.days_left) || 0);
    const progress = status === 'trial' ? Math.min(100, Math.round(((TRIAL_DAYS - daysLeft) / TRIAL_DAYS) * 100)) : 0;
    const hasCalls = (Number(stats.received) || 0) > 0;

    return (
        <div className="glass p-6 rounded-2xl space-y-5">
            <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                    <h3 className="font-bold text-white flex items-center gap-2">
                        <PhoneCall className="w-4 h-4 text-brand" /> Réceptionniste IA
                    </h3>
                    <p className="text-sm text-slate-400 mt-1 max-w-xl">
                        Répond aux appels manqués, qualifie la demande, détecte les urgences et envoie un SMS résumé.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold px-3 py-1.5 rounded-xl border ${ui.cls}`}>
                        {ui.label}{status === 'trial' && ` · ${daysLeft} jour${daysLeft > 1 ? 's' : ''} restant${daysLeft > 1 ? 's' : ''}`}
                    </span>
                    <button onClick={load} disabled={loading} title="Actualiser"
                        className="p-2 rounded-xl border border-white/10 text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-40">
                        <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {error && (
                <div className="flex items-center gap-2 text-sm text-amber-300">
                    <AlertTriangle className="w-4 h-4" /> {error}
                </div>
            )}

            {status === 'trial' && (
                <div className="h-1.5 rounded-full bg-white/10 overflow-hidden" aria-label="Progression de l'essai">
                    <div className="h-full bg-emerald-400" style={{ width: `${progress}%` }} />
                </div>
            )}

            {(status === 'trial' || status === 'active' || status === 'expired') && (
                <>
                    <div className="grid grid-cols-3 gap-3">
                        <Stat icon={PhoneIncoming} label="Appels reçus" value={Number(stats.received)} />
                        <Stat icon={PhoneForwarded} label="Récupérés" value={Number(stats.recovered)} accent="text-emerald-300" />
                        <Stat icon={AlertTriangle} label="Urgents" value={Number(stats.urgent)} accent="text-amber-300" />
                    </div>
                    {!hasCalls && (
                        <p className="text-xs text-slate-500">
                            Aucun appel pour l'instant. Pensez à activer le renvoi d'appel « si occupé / sans réponse » vers le numéro ci-dessous.
                        </p>
                    )}
                    {data?.twilio_number && (
                        <p className="text-sm text-slate-300">
                            Numéro de renvoi : <span className="font-mono text-white">{data.twilio_number}</span>
                        </p>
                    )}
                </>
            )}

            {status === 'inactive' && (
                <div className="flex items-center justify-between gap-4 flex-wrap border border-brand/30 bg-brand/5 rounded-xl p-4">
                    <p className="text-sm text-slate-300">
                        <span className="font-bold text-white">Offerte 30 jours</span>, sans engagement, résiliable à tout moment.
                    </p>
                    <button onClick={activate} disabled={activating}
                        className="flex items-center gap-2 text-sm bg-brand text-white px-4 py-2 rounded-xl font-bold hover:bg-blue-600 disabled:opacity-40">
                        {activating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        Activer mes 30 jours gratuits
                    </button>
                </div>
            )}

            {status === 'expired' && (
                <p className="text-sm text-amber-200">
                    L'essai gratuit est terminé : les appels ne sont plus pris en charge. Ajoutez l'option Réceptionniste IA à l'abonnement pour la réactiver.
                </p>
            )}
        </div>
    );
}

export default ReceptionistPanel;
