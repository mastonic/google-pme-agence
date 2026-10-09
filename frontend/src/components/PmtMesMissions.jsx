import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { ChevronLeft, ChevronRight, Check, Navigation, MapPin, Home, Camera, Loader2, AlertTriangle } from 'lucide-react';

// Mes missions (équipier, sur téléphone) : valider l'acceptation, le départ,
// l'arrivée et le retour ; puis photographier le bon de la course.

const STEPS = [
    ['accepter', 'Accepter', Check, ['planifiee'], 'bg-sky-600'],
    ['depart', 'Départ', Navigation, ['planifiee', 'acceptee'], 'bg-amber-600'],
    ['arrivee', 'Patient déposé', MapPin, ['en_cours'], 'bg-violet-600'],
    ['retour', 'Retour', Home, ['en_cours', 'arrivee'], 'bg-emerald-600'],
];
// Date locale du téléphone / du poste (toISOString donnerait la date UTC, fausse après minuit en été).
const isoLocal = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const todayIso = () => isoLocal(new Date());
const shift = (iso, days) => { const d = new Date(`${iso}T12:00:00`); d.setDate(d.getDate() + days); return isoLocal(d); };
const frLong = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });

function PmtMesMissions() {
    const [date, setDate] = useState(todayIso);
    const [data, setData] = useState({ missions: [] });
    const [busy, setBusy] = useState('');
    const [message, setMessage] = useState('');
    const [askKm, setAskKm] = useState(() => {
        try { return localStorage.getItem('lp_pmt_ask_km') === '1'; } catch { return false; }
    });
    const photoFor = useRef(null);
    const input = useRef(null);

    const refresh = async () => setData((await axios.get('/pmt/planning/mes-missions', { params: { date } })).data);
    useEffect(() => { refresh().catch(e => setMessage(e?.response?.data?.detail || e.message)); }, [date]);
    useEffect(() => { try { localStorage.setItem('lp_pmt_ask_km', askKm ? '1' : '0'); } catch { /* indisponible */ } }, [askKm]);

    const act = async (m, action) => {
        let km;
        if (askKm && (action === 'depart' || action === 'retour')) {
            km = window.prompt('Compteur kilométrique du véhicule (facultatif)');
            if (km === null) return;
        }
        setBusy(m.id + action); setMessage('');
        try {
            const r = await axios.post(`/pmt/planning/missions/${m.id}/action`, { action, km_compteur: km || undefined });
            if (r.data.avertissements?.length) setMessage(`Attention : ${r.data.avertissements.join(' · ')}`);
            if (action === 'retour') setMessage('Retour validé. Photographie maintenant le bon de transport.');
            await refresh();
        } catch (e) {
            setMessage(e?.response?.data?.detail || e.message);
        } finally { setBusy(''); }
    };

    const takePhoto = (m) => { photoFor.current = m; input.current?.click(); };
    const upload = async (file) => {
        const m = photoFor.current;
        if (!file || !m) return;
        setBusy(m.id + 'photo'); setMessage('');
        const form = new FormData();
        form.append('file', file);
        form.append('mission_id', m.id);
        try {
            const r = await axios.post('/pmt/extract', form, { timeout: 120000 });
            setMessage(`Bon lu : dossier ${r.data.readiness_label.toLowerCase()}. Merci !`);
            await refresh();
        } catch (e) {
            setMessage(e?.response?.data?.detail || e.message);
        } finally {
            setBusy('');
            if (input.current) input.current.value = '';
        }
    };

    return (
        <div className="w-full h-full overflow-y-auto p-4">
            <div className="max-w-md mx-auto">
                <div className="flex items-center justify-between mb-4">
                    <button onClick={() => setDate(shift(date, -1))} className="p-3 rounded-xl hover:bg-white/10"><ChevronLeft className="w-5 h-5" /></button>
                    <div className="text-center">
                        <p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Mes missions</p>
                        <p className="font-semibold capitalize">{frLong(date)}</p>
                    </div>
                    <button onClick={() => setDate(shift(date, 1))} className="p-3 rounded-xl hover:bg-white/10"><ChevronRight className="w-5 h-5" /></button>
                </div>
                {message && <div className="mb-4 rounded-xl bg-slate-800 border border-white/10 text-sm px-4 py-3">{message}</div>}
                {data.missions.length === 0 && (
                    <div className="glass rounded-2xl border border-white/10 p-8 text-center text-sm text-slate-500">
                        {data.info || 'Aucune mission ce jour.'}
                    </div>
                )}
                <div className="space-y-4">
                    {data.missions.map(m => {
                        const at = (a) => (m.events || []).filter(e => e.action === a).pop()?.at?.slice(11, 16);
                        return (
                            <div key={m.id} className={`glass rounded-2xl border p-4 ${m.status === 'annulee' ? 'border-rose-500/20 opacity-60' : 'border-white/10'}`}>
                                <div className="flex items-start justify-between gap-2">
                                    <div>
                                        <p className="text-2xl font-extrabold">{m.heure_prevue}</p>
                                        <p className="font-semibold">{m.patient_nom || 'Patient ?'}</p>
                                    </div>
                                    <span className="text-xs px-2 py-1 rounded-full bg-slate-800 border border-white/10">{m.status_label}</span>
                                </div>
                                <p className="text-sm text-slate-300 mt-2">{m.adresse_depart || '?'} → {m.adresse_arrivee || '?'}</p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {m.mode === 'tap' ? 'VSL' : 'Ambulance'} {m.vehicule} · {m.equipage_noms.join(' + ')}
                                </p>
                                {m.notes && <p className="text-xs text-amber-200 mt-2"><AlertTriangle className="w-3 h-3 inline mr-1" />{m.notes}</p>}
                                <p className="text-xs text-slate-500 mt-2">
                                    {[['depart', 'Départ'], ['arrivee', 'Déposé'], ['retour', 'Retour']].filter(([a]) => at(a)).map(([a, l]) => `${l} ${at(a)}`).join(' · ')}
                                </p>
                                <div className="grid grid-cols-2 gap-2 mt-3">
                                    {STEPS.filter(([, , , from]) => from.includes(m.status)).map(([action, label, Icon, , color]) => (
                                        <button key={action} onClick={() => act(m, action)} disabled={!!busy}
                                            className={`${color} text-white rounded-xl py-3 text-sm font-bold flex items-center justify-center gap-2 disabled:opacity-50`}>
                                            {busy === m.id + action ? <Loader2 className="w-4 h-4 animate-spin" /> : <Icon className="w-4 h-4" />} {label}
                                        </button>
                                    ))}
                                    {m.status === 'terminee' && (
                                        <button onClick={() => takePhoto(m)} disabled={!!busy}
                                            className="col-span-2 bg-brand text-white rounded-xl py-3 text-sm font-bold flex items-center justify-center gap-2">
                                            {busy === m.id + 'photo' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Camera className="w-4 h-4" />}
                                            Photographier le bon
                                        </button>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
                <label className="flex items-center gap-2 text-xs text-slate-500 mt-6">
                    <input type="checkbox" checked={askKm} onChange={e => setAskKm(e.target.checked)} className="accent-sky-500" />
                    Demander le compteur kilométrique au départ et au retour
                </label>
                <input ref={input} type="file" accept="image/*,application/pdf" capture="environment" className="hidden"
                    onChange={e => upload(e.target.files?.[0])} />
            </div>
        </div>
    );
}

export default PmtMesMissions;
