import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Film, Loader2, RefreshCw, Download, AlertTriangle, Clapperboard } from 'lucide-react';

// Onglet « Vidéo » : présentation motion design (voix off Google + musique).
// La vidéo est chargée en blob via axios, pour que le jeton admin soit envoyé
// (une balise <video src> ne peut pas transmettre l'en-tête Authorization).
function VideoPanel({ businessId, businessName }) {
    const [info, setInfo]           = useState(null);   // { status, seconds, size_kb, error, updated_at }
    const [videoUrl, setVideoUrl]   = useState('');
    const [starting, setStarting]   = useState(false);
    const [loadError, setLoadError] = useState('');
    const urlRef = useRef('');

    const setBlobUrl = (url) => {
        if (urlRef.current) URL.revokeObjectURL(urlRef.current);
        urlRef.current = url;
        setVideoUrl(url);
    };

    const loadVideo = async () => {
        try {
            const r = await axios.get(`/businesses/${businessId}/video`, { responseType: 'blob' });
            setBlobUrl(URL.createObjectURL(r.data));
            setLoadError('');
        } catch {
            setLoadError('Impossible de charger la vidéo.');
        }
    };

    const fetchStatus = async () => {
        try {
            const r = await axios.get(`/businesses/${businessId}/video/status`);
            setInfo(r.data);
            return r.data;
        } catch {
            setInfo({ status: 'none' });
            return null;
        }
    };

    useEffect(() => {
        setInfo(null);
        setBlobUrl('');
        fetchStatus().then(s => { if (s?.status === 'ready') loadVideo(); });
        return () => setBlobUrl('');
    }, [businessId]);

    // Suivi de la génération en cours.
    useEffect(() => {
        if (info?.status !== 'running') return;
        const id = setInterval(async () => {
            const s = await fetchStatus();
            if (s?.status === 'ready') loadVideo();
        }, 4000);
        return () => clearInterval(id);
    }, [info?.status, businessId]);

    const generate = async () => {
        setStarting(true);
        try {
            await axios.post(`/businesses/${businessId}/video`);
            setInfo(prev => ({ ...(prev || {}), status: 'running', error: null }));
        } catch (e) {
            setInfo({ status: 'error', error: e.response?.data?.detail || 'Lancement impossible.' });
        } finally {
            setStarting(false);
        }
    };

    const status = info?.status;
    const fileName = `presentation-${(businessName || 'prospect').toLowerCase().replace(/[^a-z0-9]+/g, '-')}.mp4`;

    if (!info) {
        return (
            <div className="glass p-10 rounded-2xl flex items-center justify-center text-slate-400">
                <Loader2 className="w-6 h-6 animate-spin text-brand" />
            </div>
        );
    }

    if (status === 'running') {
        return (
            <div className="glass p-10 rounded-2xl flex flex-col items-center justify-center text-center gap-3 min-h-[400px]">
                <Loader2 className="w-10 h-10 animate-spin text-brand" />
                <p className="font-bold text-white">Création de la vidéo en cours...</p>
                <p className="text-sm text-slate-400 max-w-md">
                    Voix off, animations et musique : comptez 1 à 3 minutes.
                    Vous pouvez changer d'onglet, la vidéo apparaîtra ici une fois prête.
                </p>
            </div>
        );
    }

    if (status === 'ready') {
        return (
            <div className="flex flex-col gap-3">
                <div className="bg-slate-950 rounded-xl overflow-hidden border border-white/10 flex items-center justify-center" style={{ minHeight: '400px' }}>
                    {videoUrl ? (
                        <video key={videoUrl} src={videoUrl} controls playsInline className="w-full max-h-[70vh] bg-black" />
                    ) : loadError ? (
                        <p className="text-sm text-rose-400">{loadError}</p>
                    ) : (
                        <Loader2 className="w-8 h-8 animate-spin text-brand" />
                    )}
                </div>
                <div className="flex items-center justify-between gap-3 flex-wrap px-4 py-3 bg-slate-800 rounded-xl border border-white/10">
                    <span className="text-xs text-slate-400">
                        <Film className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
                        {Math.round(info.seconds || 0)} s · {Math.round((info.size_kb || 0) / 102.4) / 10} Mo
                        {info.updated_at && <> · créée le {new Date(info.updated_at).toLocaleString('fr-FR')}</>}
                        <span className="block sm:inline sm:ml-2 text-slate-500">Elle sera publiée avec le site au déploiement.</span>
                    </span>
                    <div className="flex items-center gap-2">
                        <button onClick={generate} disabled={starting}
                            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-white/10 px-4 py-2 rounded-xl hover:bg-white/5 transition-colors disabled:opacity-40">
                            <RefreshCw className="w-4 h-4" /> Régénérer
                        </button>
                        {videoUrl && (
                            <a href={videoUrl} download={fileName}
                               className="flex items-center gap-2 text-sm bg-brand text-white px-4 py-2 rounded-xl font-bold hover:bg-brand-dark transition-colors">
                                <Download className="w-4 h-4" /> Télécharger
                            </a>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    // Aucune vidéo, ou échec de la dernière génération.
    return (
        <div className="glass p-10 rounded-2xl flex flex-col items-center justify-center text-center gap-4 min-h-[400px]">
            {status === 'error' ? (
                <>
                    <AlertTriangle className="w-10 h-10 text-amber-400" />
                    <p className="font-bold text-white">La dernière génération a échoué</p>
                    {info.error && <p className="text-xs text-slate-400 max-w-md break-words">{info.error}</p>}
                </>
            ) : (
                <>
                    <Clapperboard className="w-10 h-10 text-brand" />
                    <p className="font-bold text-white">Pas encore de vidéo de présentation</p>
                    <p className="text-sm text-slate-400 max-w-md">
                        Une vidéo animée avec voix off et musique, construite à partir de la fiche Google
                        du prospect. Elle sera aussi publiée avec le site au déploiement.
                    </p>
                </>
            )}
            <button onClick={generate} disabled={starting}
                className="flex items-center gap-2 bg-brand text-white px-6 py-2.5 rounded-xl font-bold hover:bg-brand-dark transition-colors disabled:opacity-40 shadow-lg shadow-brand/25">
                {starting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Film className="w-4 h-4" />}
                {status === 'error' ? 'Réessayer' : 'Générer la vidéo'}
            </button>
        </div>
    );
}

export default VideoPanel;
