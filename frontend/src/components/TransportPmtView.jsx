import React, { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import {
    Ambulance, Upload, FileDown, Printer, Trash2, CheckCircle2, AlertTriangle, XCircle,
    Info, Loader2, Plus, Save, ShieldAlert, Camera
} from 'lucide-react';

// Bons de transport (PMT Cerfa 11574*04) des clients ambulanciers :
// scan → lecture automatique → correction → contrôles → export facturation.

const READINESS = {
    pret:       { label: 'Prêt à facturer', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
    a_verifier: { label: 'À vérifier',      cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
    bloquant:   { label: 'Bloquant',        cls: 'bg-rose-500/15 text-rose-300 border-rose-500/30' },
};

const LEVELS = {
    error:   { icon: XCircle,       cls: 'text-rose-300',  ring: 'border-rose-500/60' },
    warning: { icon: AlertTriangle, cls: 'text-amber-300', ring: 'border-amber-500/60' },
    info:    { icon: Info,          cls: 'text-slate-400', ring: '' },
};

const LIEUX = [['', '—'], ['domicile', 'Domicile'], ['autre', 'Autre lieu'], ['structure', 'Structure de soins']];

const SECTIONS = [
    { title: 'Patient', fields: [
        ['data.beneficiaire.nom', 'Nom'],
        ['data.beneficiaire.prenom', 'Prénom'],
        ['data.beneficiaire.nir', 'NIR (13 caractères)'],
        ['data.beneficiaire.nir_cle', 'Clé'],
        ['data.beneficiaire.date_naissance', 'Date de naissance', 'date'],
        ['data.beneficiaire.adresse', 'Adresse', 'text', true],
        ['data.organisme.libelle', 'Caisse'],
        ['data.organisme.code', 'Code caisse'],
        ['data.accident_tiers', 'Accident causé par un tiers', 'tri'],
        ['data.date_accident', 'Date de l’accident', 'date'],
    ]},
    { title: 'Prise en charge', fields: [
        ['data.situation.hospitalisation', 'Entrée / sortie d’hospitalisation', 'bool'],
        ['data.situation.ald_exonerante', 'ALD exonérante', 'bool'],
        ['data.situation.ald_non_exonerante', 'ALD non exonérante', 'bool'],
        ['data.situation.at_mp', 'Accident du travail / maladie pro.', 'bool'],
        ['data.situation.date_at_mp', 'Date AT/MP', 'date'],
        ['data.exoneration_tm', 'Exonération du ticket modérateur', 'tri'],
        ['data.pension_militaire', 'Pension militaire (art. L. 115)', 'tri'],
    ]},
    { title: 'Transport prescrit', fields: [
        ['data.mode', 'Mode', 'select', false, [['', '—'], ['ambulance', 'Ambulance'], ['tap', 'VSL / taxi conventionné'], ['vehicule_personnel', 'Véhicule personnel'], ['transport_commun', 'Transport en commun']]],
        ['data.ambulance_justif.allonge_demi_assis', 'Allongé ou demi-assis', 'bool'],
        ['data.ambulance_justif.brancardage', 'Brancardage ou portage', 'bool'],
        ['data.ambulance_justif.surveillance', 'Surveillance qualifiée', 'bool'],
        ['data.ambulance_justif.oxygene', 'Oxygène', 'bool'],
        ['data.ambulance_justif.asepsie', 'Asepsie rigoureuse', 'bool'],
        ['data.transport_partage', 'Transport partagé possible', 'bool'],
    ]},
    { title: 'Trajet', fields: [
        ['data.trajet.depart_type', 'Départ', 'select', false, LIEUX],
        ['data.trajet.depart_libelle', 'Lieu de départ (si hors domicile)'],
        ['data.trajet.arrivee_type', 'Arrivée', 'select', false, LIEUX],
        ['data.trajet.arrivee_libelle', 'Lieu / structure d’arrivée'],
        ['data.trajet.aller_retour', 'Aller-retour', 'bool'],
        ['data.trajet.nb_iteratifs', 'Transports itératifs', 'number'],
        ['data.urgence.samu', 'Urgence — SAMU / centre 15', 'bool'],
        ['data.urgence.autre', 'Urgence — autre', 'bool'],
    ]},
    { title: 'Prescripteur', fields: [
        ['data.prescripteur.nom', 'Nom'],
        ['data.prescripteur.rpps', 'RPPS (11 chiffres)'],
        ['data.prescripteur.raison_sociale', 'Structure'],
        ['data.prescripteur.numero_structure', 'N° structure (AM / FINESS / SIRET)'],
        ['data.prescripteur.date_prescription', 'Date de prescription', 'date'],
        ['data.prescripteur.signature_presente', 'Signature présente', 'bool'],
    ]},
    { title: 'Course réalisée', fields: [
        ['transport.date_transport', 'Date du transport', 'date'],
        ['transport.heure_depart', 'Heure de départ', 'time'],
        ['transport.km_aller', 'Km aller', 'number'],
        ['transport.vehicule', 'Véhicule'],
        ['transport.equipage', 'Équipage'],
        ['transport.accord_prealable_ref', 'Réf. accord préalable'],
    ]},
];

const TRANSPORTEUR_FIELDS = [
    ['raison_sociale', 'Raison sociale'],
    ['adresse', 'Adresse'],
    ['numero_identification', 'N° d’identification'],
    ['fait_a', 'Fait à'],
];

const getPath = (obj, path) => path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);

const setPath = (obj, path, value) => {
    const copy = structuredClone(obj);
    const keys = path.split('.');
    let node = copy;
    keys.slice(0, -1).forEach(k => { node[k] = node[k] ?? {}; node = node[k]; });
    node[keys.at(-1)] = value;
    return copy;
};

// Le chemin d'un contrôle (« prescripteur.rpps ») vers celui du brouillon (« data.prescripteur.rpps »).
const checkPath = (field) => (field.startsWith('transport') ? field : `data.${field}`);

const loadTransporteur = () => {
    try { return JSON.parse(localStorage.getItem('lp_pmt_transporteur') || '{}'); } catch { return {}; }
};

function Field({ path, label, type = 'text', wide, options, draft, onChange, issue }) {
    const value = getPath(draft, path);
    const ring = issue ? LEVELS[issue].ring : 'border-white/10';
    if (type === 'bool') {
        return (
            <label className={`flex items-center gap-2 text-sm px-3 py-2 rounded-xl border ${ring} bg-slate-800/50 cursor-pointer`}>
                <input type="checkbox" checked={!!value} onChange={e => onChange(path, e.target.checked)} className="accent-sky-500" />
                {label}
            </label>
        );
    }
    const base = `mt-1 w-full bg-slate-800 border ${ring} rounded-xl px-3 py-2 text-sm`;
    let input;
    if (type === 'tri') {
        input = (
            <select className={base} value={value === true ? 'oui' : value === false ? 'non' : ''}
                onChange={e => onChange(path, e.target.value === '' ? null : e.target.value === 'oui')}>
                <option value="">Non renseigné</option><option value="oui">Oui</option><option value="non">Non</option>
            </select>
        );
    } else if (type === 'select') {
        input = (
            <select className={base} value={value ?? ''} onChange={e => onChange(path, e.target.value || null)}>
                {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
        );
    } else {
        input = (
            <input type={type} className={base} value={value ?? ''}
                onChange={e => onChange(path, type === 'number'
                    ? (e.target.value === '' ? null : Number(e.target.value))
                    : e.target.value)} />
        );
    }
    return (
        <label className={`block text-xs text-slate-400 ${wide ? 'sm:col-span-2' : ''}`}>
            {label}
            {input}
        </label>
    );
}

function TransportPmtView({ businesses = [] }) {
    const [vouchers, setVouchers] = useState([]);
    const [businessId, setBusinessId] = useState('');
    const [filter, setFilter] = useState('');
    const [selected, setSelected] = useState(null);   // bon enregistré
    const [draft, setDraft] = useState(null);         // { data, transport } en cours d'édition
    const [preview, setPreview] = useState(null);     // contrôles en direct
    const [transporteur, setTransporteur] = useState(loadTransporteur);
    const [busy, setBusy] = useState('');
    const [message, setMessage] = useState('');
    const fileInput = useRef(null);
    const cameraInput = useRef(null);
    const dirty = useRef(false);

    const refresh = async () => {
        const params = businessId ? { business_id: businessId } : {};
        const r = await axios.get('/pmt/vouchers', { params });
        setVouchers(Array.isArray(r.data) ? r.data : []);
    };

    useEffect(() => { refresh().catch(e => setMessage(e.message)); }, [businessId]);

    useEffect(() => {
        try { localStorage.setItem('lp_pmt_transporteur', JSON.stringify(transporteur)); } catch { /* stockage indisponible */ }
    }, [transporteur]);

    const open = (v) => {
        setSelected(v);
        setDraft({ data: v.data, transport: v.transport });
        setPreview(v);
        dirty.current = false;
        setMessage('');
    };

    // Contrôles en direct pendant la correction (sans enregistrer).
    useEffect(() => {
        if (!draft || !dirty.current) return;
        const t = setTimeout(() => {
            axios.post('/pmt/validate', draft).then(r => setPreview(r.data)).catch(() => {});
        }, 350);
        return () => clearTimeout(t);
    }, [draft]);

    const onChange = (path, value) => {
        dirty.current = true;
        setDraft(prev => {
            let next = setPath(prev, path, value);
            // Corriger un champ vaut vérification : il sort des lectures incertaines.
            const short = path.replace(/^data\./, '');
            const uncertain = next.data?.champs_incertains || [];
            if (uncertain.includes(short)) {
                next = setPath(next, 'data.champs_incertains', uncertain.filter(f => f !== short));
            }
            return next;
        });
    };

    const markVerified = (field) => {
        dirty.current = true;
        setDraft(prev => setPath(prev, 'data.champs_incertains',
            (prev.data?.champs_incertains || []).filter(f => f !== field)));
    };

    const upload = async (file) => {
        if (!file) return;
        setBusy('extract'); setMessage('');
        const form = new FormData();
        form.append('file', file);
        if (businessId) form.append('business_id', businessId);
        try {
            const r = await axios.post('/pmt/extract', form, { timeout: 120000 });
            const v = (await axios.patch(`/pmt/vouchers/${r.data.id}`, { transporteur })).data;
            await refresh();
            open(v);
            setMessage(`Bon lu automatiquement (${r.data.extraction_provider}). Vérifie les champs signalés.`);
        } catch (e) {
            setMessage(e?.response?.data?.detail || e.message || 'Lecture impossible');
        } finally {
            setBusy('');
            if (fileInput.current) fileInput.current.value = '';
            if (cameraInput.current) cameraInput.current.value = '';
        }
    };

    const createManual = async () => {
        setBusy('manual');
        try {
            const r = await axios.post('/pmt/vouchers', { business_id: businessId || null, data: {}, transport: {}, transporteur });
            await refresh();
            open(r.data);
        } finally { setBusy(''); }
    };

    const save = async (status) => {
        if (!selected) return;
        setBusy('save'); setMessage('');
        try {
            const payload = { ...draft, transporteur, ...(status ? { status } : {}) };
            const r = await axios.patch(`/pmt/vouchers/${selected.id}`, payload);
            open(r.data);
            await refresh();
            setMessage(status === 'validated' ? 'Bon validé : prêt pour la télétransmission.' : 'Enregistré.');
        } catch (e) {
            setMessage(e?.response?.data?.detail || e.message);
        } finally { setBusy(''); }
    };

    const remove = async () => {
        if (!selected || !window.confirm('Supprimer définitivement ce bon de transport ?')) return;
        await axios.delete(`/pmt/vouchers/${selected.id}`);
        setSelected(null); setDraft(null); setPreview(null);
        await refresh();
    };

    const issues = useMemo(() => {
        const map = {};
        const rank = { error: 3, warning: 2, info: 1 };
        (preview?.checks || []).forEach(c => {
            const p = checkPath(c.field);
            if (!map[p] || rank[c.level] > rank[map[p]]) map[p] = c.level;
        });
        return map;
    }, [preview]);

    const shown = vouchers.filter(v => !filter || v.readiness === filter);
    const counts = Object.fromEntries(Object.keys(READINESS).map(k => [k, vouchers.filter(v => v.readiness === k).length]));
    const exportUrl = `/pmt/vouchers/export.csv${businessId ? `?business_id=${encodeURIComponent(businessId)}` : ''}`;

    return (
        <div className="w-full h-full overflow-y-auto bg-slate-900 p-4 md:p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-11 h-11 rounded-2xl bg-brand/15 border border-brand/30 flex items-center justify-center">
                            <Ambulance className="w-6 h-6 text-brand" />
                        </div>
                        <div>
                            <h2 className="text-3xl font-extrabold">Bons de transport</h2>
                            <p className="text-slate-400 text-sm">Scan de la PMT → lecture automatique → contrôles CPAM → export facturation.</p>
                        </div>
                    </div>
                    <div className="min-w-[260px]">
                        <label className="text-xs text-slate-400 font-bold uppercase tracking-wider">Client ambulancier</label>
                        <select value={businessId} onChange={e => setBusinessId(e.target.value)}
                            className="mt-2 w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-3 text-sm">
                            <option value="">Tous les clients</option>
                            {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                        </select>
                    </div>
                </div>

                <div className="flex items-start gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-200 text-xs p-3 mb-6">
                    <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <p>Données de santé : le scan n’est pas conservé, seules les données extraites le sont.
                        Avant de traiter de vrais patients, il faut un hébergement certifié HDS et un fournisseur de lecture automatique couvert contractuellement.</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6">
                    {/* Colonne gauche : import + liste */}
                    <div className="space-y-4">
                        <div
                            className="glass rounded-2xl border-2 border-dashed border-white/15 p-5 text-center"
                            onDragOver={e => e.preventDefault()}
                            onDrop={e => { e.preventDefault(); upload(e.dataTransfer.files?.[0]); }}
                        >
                            {busy === 'extract' ? (
                                <div className="py-4 text-sm text-slate-300 flex flex-col items-center gap-2">
                                    <Loader2 className="w-6 h-6 animate-spin text-brand" />
                                    Lecture du bon en cours…
                                </div>
                            ) : (
                                <>
                                    <Upload className="w-7 h-7 mx-auto text-brand mb-2" />
                                    <p className="text-sm font-semibold">Déposer le scan du bon de transport</p>
                                    <p className="text-xs text-slate-500 mt-1">PDF ou photo · volets 1 et 2</p>
                                    <div className="flex flex-wrap justify-center gap-2 mt-4">
                                        <button onClick={() => fileInput.current?.click()}
                                            className="px-3 py-2 rounded-xl bg-brand text-white text-sm font-semibold">Choisir un fichier</button>
                                        <button onClick={() => cameraInput.current?.click()}
                                            className="px-3 py-2 rounded-xl bg-slate-800 border border-white/10 text-sm flex items-center gap-1">
                                            <Camera className="w-4 h-4" /> Photo
                                        </button>
                                        <button onClick={createManual} disabled={!!busy}
                                            className="px-3 py-2 rounded-xl bg-slate-800 border border-white/10 text-sm flex items-center gap-1">
                                            <Plus className="w-4 h-4" /> Saisie manuelle
                                        </button>
                                    </div>
                                </>
                            )}
                            <input ref={fileInput} type="file" accept="application/pdf,image/*" className="hidden"
                                onChange={e => upload(e.target.files?.[0])} />
                            <input ref={cameraInput} type="file" accept="image/*" capture="environment" className="hidden"
                                onChange={e => upload(e.target.files?.[0])} />
                        </div>

                        <div className="glass rounded-2xl border border-white/10 p-4">
                            <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Cadre transporteur (volet 2)</p>
                            <div className="space-y-2">
                                {TRANSPORTEUR_FIELDS.map(([k, label]) => (
                                    <input key={k} placeholder={label} value={transporteur[k] || ''}
                                        onChange={e => setTransporteur(t => ({ ...t, [k]: e.target.value }))}
                                        className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm" />
                                ))}
                            </div>
                            <p className="text-[11px] text-slate-500 mt-2">Repris automatiquement sur chaque fiche.</p>
                        </div>

                        <div className="glass rounded-2xl border border-white/10">
                            <div className="flex items-center justify-between p-4 border-b border-white/5">
                                <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{vouchers.length} bon(s)</p>
                                <a href={exportUrl} className="text-xs flex items-center gap-1 text-sky-300 hover:text-sky-200">
                                    <FileDown className="w-4 h-4" /> Export CSV
                                </a>
                            </div>
                            <div className="flex flex-wrap gap-2 p-3 border-b border-white/5">
                                <button onClick={() => setFilter('')}
                                    className={`text-[11px] px-2 py-1 rounded-full border ${!filter ? 'border-white/40 text-white' : 'border-white/10 text-slate-400'}`}>Tous</button>
                                {Object.entries(READINESS).map(([k, r]) => (
                                    <button key={k} onClick={() => setFilter(k)}
                                        className={`text-[11px] px-2 py-1 rounded-full border ${filter === k ? r.cls : 'border-white/10 text-slate-400'}`}>
                                        {r.label} · {counts[k]}
                                    </button>
                                ))}
                            </div>
                            <div className="max-h-[420px] overflow-y-auto divide-y divide-white/5">
                                {shown.length === 0 && <p className="p-4 text-sm text-slate-500">Aucun bon pour l’instant.</p>}
                                {shown.map(v => {
                                    const b = v.data?.beneficiaire || {};
                                    return (
                                        <button key={v.id} onClick={() => open(v)}
                                            className={`w-full text-left p-3 hover:bg-white/[0.04] ${selected?.id === v.id ? 'bg-white/[0.06]' : ''}`}>
                                            <div className="flex items-center justify-between gap-2">
                                                <p className="font-semibold text-sm truncate">{[b.nom, b.prenom].filter(Boolean).join(' ') || 'Patient à compléter'}</p>
                                                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${READINESS[v.readiness]?.cls}`}>{READINESS[v.readiness]?.label}</span>
                                            </div>
                                            <p className="text-[11px] text-slate-500 mt-1 truncate">
                                                {v.transport?.date_transport || v.data?.prescripteur?.date_prescription || '—'} · {v.data?.trajet?.arrivee_libelle || 'arrivée ?'}
                                                {v.status === 'validated' && ' · validé'}
                                            </p>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    {/* Colonne droite : correction + contrôles */}
                    <div>
                        {message && <div className="mb-4 rounded-xl bg-slate-800 border border-white/10 px-4 py-3 text-sm">{message}</div>}
                        {!draft ? (
                            <div className="glass rounded-2xl border border-white/10 p-10 text-center text-slate-500 text-sm">
                                Dépose un bon de transport ou sélectionne-le dans la liste.
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-6">
                                <div className="space-y-4">
                                    {SECTIONS.map(section => (
                                        <div key={section.title} className="glass rounded-2xl border border-white/10 p-4">
                                            <h3 className="font-bold text-sm mb-3">{section.title}</h3>
                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                {section.fields.map(([path, label, type, wide, options]) => (
                                                    <Field key={path} path={path} label={label} type={type} wide={wide} options={options}
                                                        draft={draft} onChange={onChange} issue={issues[path]} />
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                    {draft.data?.elements_medicaux && (
                                        <div className="glass rounded-2xl border border-white/10 p-4 text-sm">
                                            <h3 className="font-bold mb-1">Éléments médicaux (volet 1, médecin-conseil)</h3>
                                            <p className="text-slate-400">{draft.data.elements_medicaux}</p>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-4 xl:sticky xl:top-0 self-start">
                                    <div className="glass rounded-2xl border border-white/10 p-4">
                                        <span className={`inline-block text-xs px-3 py-1 rounded-full border font-bold ${READINESS[preview?.readiness]?.cls}`}>
                                            {READINESS[preview?.readiness]?.label}
                                        </span>
                                        {preview?.prise_en_charge && (
                                            <p className="text-xs text-slate-400 mt-3">
                                                Prise en charge : <b className="text-white">{preview.prise_en_charge.taux_amo} % AMO</b> — {preview.prise_en_charge.motif}
                                            </p>
                                        )}
                                        <div className="grid grid-cols-2 gap-2 mt-4">
                                            <button onClick={() => save()} disabled={!!busy}
                                                className="px-3 py-2 rounded-xl bg-slate-800 border border-white/10 text-sm flex items-center justify-center gap-1">
                                                {busy === 'save' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Enregistrer
                                            </button>
                                            <button onClick={() => save('validated')} disabled={!!busy || preview?.readiness === 'bloquant'}
                                                className="px-3 py-2 rounded-xl bg-emerald-600 disabled:opacity-40 text-white text-sm font-semibold flex items-center justify-center gap-1">
                                                <CheckCircle2 className="w-4 h-4" /> Valider
                                            </button>
                                            <button onClick={() => window.open(`/pmt/vouchers/${selected.id}/fiche`, '_blank')}
                                                className="px-3 py-2 rounded-xl bg-slate-800 border border-white/10 text-sm flex items-center justify-center gap-1">
                                                <Printer className="w-4 h-4" /> Fiche
                                            </button>
                                            <button onClick={remove}
                                                className="px-3 py-2 rounded-xl bg-slate-800 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-center gap-1">
                                                <Trash2 className="w-4 h-4" /> Supprimer
                                            </button>
                                        </div>
                                        {dirty.current && <p className="text-[11px] text-amber-300 mt-2">Modifications non enregistrées.</p>}
                                    </div>

                                    <div className="glass rounded-2xl border border-white/10 p-4">
                                        <h3 className="font-bold text-sm mb-3">Contrôles avant télétransmission</h3>
                                        <ul className="space-y-3">
                                            {(preview?.checks || []).length === 0 && <li className="text-sm text-emerald-300">Aucune anomalie.</li>}
                                            {(preview?.checks || []).map((c, i) => {
                                                const L = LEVELS[c.level];
                                                return (
                                                    <li key={`${c.code}-${i}`} className="flex gap-2 text-xs">
                                                        <L.icon className={`w-4 h-4 flex-shrink-0 ${L.cls}`} />
                                                        <div>
                                                            <p className={L.cls}>{c.message}</p>
                                                            {c.fix && <p className="text-slate-500 mt-0.5">{c.fix}</p>}
                                                            {c.code === 'LECTURE_INCERTAINE' && (
                                                                <button onClick={() => markVerified(c.field)} className="mt-1 text-sky-300 hover:text-sky-200">
                                                                    J’ai vérifié sur le scan
                                                                </button>
                                                            )}
                                                        </div>
                                                    </li>
                                                );
                                            })}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default TransportPmtView;
