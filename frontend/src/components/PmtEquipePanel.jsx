import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import { Users, UserPlus, X, Save, KeyRound, AlertTriangle, CheckCircle2, Clock3, Trash2 } from 'lucide-react';

// Équipe : registre des salariés, échéances des documents (attestation
// préfectorale, AFGSU 2…), accès « employé » pour saisir les bons sur le terrain.

const QUALIFS = [
    ['DEA', 'DEA — diplôme d’État'], ['CCA', 'CCA'], ['DA', 'DA'], ['auxiliaire', 'Auxiliaire ambulancier'],
    ['conducteur', 'Conducteur d’ambulance'], ['stagiaire', 'Stagiaire'], ['autre', 'Autre'],
];
const CONTRATS = [['CDI', 'CDI'], ['CDD', 'CDD'], ['interim', 'Intérim'], ['vacataire', 'Vacataire'], ['mise_a_disposition', 'Mise à disposition']];
const STATUS = {
    ok: { label: 'En règle', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30', icon: CheckCircle2 },
    bientot: { label: 'À renouveler', cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30', icon: Clock3 },
    non_conforme: { label: 'Non conforme', cls: 'bg-rose-500/15 text-rose-300 border-rose-500/30', icon: AlertTriangle },
};
const EMPTY = {
    nom: '', prenom: '', qualification: 'DEA', numero_rpps: '', attestation_prefectorale_fin: '', afgsu2_fin: '',
    permis_fin: '', aptitude_medicale_fin: '', contrat: 'CDI', contrat_debut: '', contrat_fin: '', declare_ars_le: '', actif: true,
};
const frDate = (iso) => (iso ? iso.split('-').reverse().join('/') : '—');

function EmployeeDrawer({ employee, businessId, onClose, onSaved }) {
    const [form, setForm] = useState(() => ({ ...EMPTY, ...(employee || {}) }));
    const [access, setAccess] = useState({ email: '', password: '' });
    const [error, setError] = useState('');
    const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
    const field = 'mt-1 w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white';

    const save = async () => {
        setError('');
        try {
            const body = { ...form, business_id: businessId || form.business_id };
            const r = employee?.id ? await axios.put(`/pmt/equipe/${employee.id}`, body) : await axios.post('/pmt/equipe', body);
            onSaved(r.data);
        } catch (e) { setError(e?.response?.data?.detail || e.message); }
    };
    const createAccess = async () => {
        setError('');
        try {
            const r = await axios.post(`/pmt/equipe/${employee.id}/acces`, access);
            onSaved(r.data, 'Accès créé : transmets le mot de passe au salarié de vive voix.');
        } catch (e) { setError(e?.response?.data?.detail || e.message); }
    };
    const remove = async () => {
        if (!window.confirm('Supprimer ce salarié et son accès ?')) return;
        await axios.delete(`/pmt/equipe/${employee.id}`);
        onSaved(null);
    };

    const input = (k, label, type = 'text') => (
        <label className="block text-xs text-slate-400">{label}
            <input type={type} value={form[k] || ''} onChange={e => set(k, e.target.value)} className={field} />
        </label>
    );
    const select = (k, label, options) => (
        <label className="block text-xs text-slate-400">{label}
            <select value={form[k]} onChange={e => set(k, e.target.value)} className={field}>
                {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
        </label>
    );

    return createPortal(
        <div className="fixed inset-0 z-[5000] flex">
            <div className="flex-1 bg-black/60 backdrop-blur-sm" onClick={onClose} />
            <div className="w-full md:w-[560px] h-full bg-slate-950 border-l border-white/10 overflow-y-auto">
                <div className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur border-b border-white/10 p-5 flex items-center justify-between">
                    <h3 className="font-bold text-lg">{employee?.id ? `${form.prenom} ${form.nom}` : 'Nouveau salarié'}</h3>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-white/10"><X className="w-5 h-5" /></button>
                </div>
                <div className="p-5 space-y-5">
                    {error && <div className="rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-200 text-sm px-4 py-3">{error}</div>}
                    <div className="grid grid-cols-2 gap-3">
                        {input('nom', 'Nom')}
                        {input('prenom', 'Prénom')}
                        {select('qualification', 'Qualification', QUALIFS)}
                        {input('numero_rpps', 'N° RPPS / ADELI')}
                    </div>
                    <div>
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Documents — date de fin de validité</p>
                        <div className="grid grid-cols-2 gap-3">
                            {input('attestation_prefectorale_fin', 'Attestation préfectorale de conduite', 'date')}
                            {input('afgsu2_fin', 'AFGSU niveau 2 (4 ans)', 'date')}
                            {input('permis_fin', 'Permis de conduire', 'date')}
                            {input('aptitude_medicale_fin', 'Aptitude médicale', 'date')}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-2">Aucune donnée médicale n’est enregistrée : seulement les dates de validité.</p>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        {select('contrat', 'Contrat', CONTRATS)}
                        {input('declare_ars_le', 'Déclaré à l’ARS le', 'date')}
                        {input('contrat_debut', 'Début du contrat', 'date')}
                        {input('contrat_fin', 'Fin du contrat (CDD)', 'date')}
                    </div>
                    <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={!!form.actif} onChange={e => set('actif', e.target.checked)} className="accent-sky-500" />
                        Salarié actif <span className="text-xs text-slate-500">(décocher coupe aussi son accès)</span>
                    </label>
                    <div className="flex justify-between gap-2">
                        {employee?.id ? (
                            <button onClick={remove} className="px-3 py-2 rounded-xl border border-rose-500/30 text-rose-300 text-sm flex items-center gap-1">
                                <Trash2 className="w-4 h-4" /> Supprimer
                            </button>
                        ) : <span />}
                        <button onClick={save} className="px-4 py-2 rounded-xl bg-brand text-white text-sm font-semibold flex items-center gap-1">
                            <Save className="w-4 h-4" /> Enregistrer
                        </button>
                    </div>

                    {employee?.id && !employee.a_un_acces && (
                        <div className="glass rounded-2xl border border-white/10 p-4 space-y-3">
                            <p className="font-semibold text-sm flex items-center gap-2"><KeyRound className="w-4 h-4" /> Créer un accès employé</p>
                            <p className="text-xs text-slate-500">Il pourra photographier les bons et compléter ses courses depuis son téléphone. Pas d’export, pas de rejets, pas de suppression.</p>
                            <input type="email" placeholder="E-mail" value={access.email} onChange={e => setAccess(a => ({ ...a, email: e.target.value }))} className={field} />
                            <input type="text" placeholder="Mot de passe (10+ caractères)" value={access.password} onChange={e => setAccess(a => ({ ...a, password: e.target.value }))} className={field} />
                            <button onClick={createAccess} className="px-4 py-2 rounded-xl bg-slate-800 border border-white/10 text-sm">Créer l’accès</button>
                        </div>
                    )}
                    {employee?.a_un_acces && <p className="text-xs text-emerald-300">Ce salarié a un accès employé.</p>}
                </div>
            </div>
        </div>,
        document.body,
    );
}

function PmtEquipePanel({ businesses = [], user }) {
    const isAdmin = user?.role === 'admin';
    const [businessId, setBusinessId] = useState('');
    const [employees, setEmployees] = useState([]);
    const [alerts, setAlerts] = useState(null);
    const [editing, setEditing] = useState(null);
    const [message, setMessage] = useState('');

    const params = () => (businessId ? { business_id: businessId } : {});
    const refresh = async () => {
        const [e, a] = await Promise.all([
            axios.get('/pmt/equipe', { params: params() }),
            axios.get('/pmt/equipe/alertes', { params: params() }),
        ]);
        setEmployees(e.data);
        setAlerts(a.data);
    };
    useEffect(() => { refresh().catch(e => setMessage(e?.response?.data?.detail || e.message)); }, [businessId]);

    const openNew = () => {
        if (isAdmin && !businessId) { setMessage('Choisis d’abord le client ambulancier.'); return; }
        setEditing({});
    };

    return (
        <div className="w-full h-full overflow-y-auto p-4 md:p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-11 h-11 rounded-2xl bg-brand/15 border border-brand/30 flex items-center justify-center">
                            <Users className="w-6 h-6 text-brand" />
                        </div>
                        <div>
                            <h2 className="text-3xl font-extrabold">Équipe</h2>
                            <p className="text-slate-400 text-sm">Qualifications et échéances : un équipage non en règle expose à un indu.</p>
                        </div>
                    </div>
                    <div className="flex items-end gap-3">
                        {isAdmin && (
                            <select value={businessId} onChange={e => setBusinessId(e.target.value)}
                                className="bg-slate-800 border border-white/10 rounded-xl px-3 py-3 text-sm min-w-[220px]">
                                <option value="">Tous les clients</option>
                                {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                            </select>
                        )}
                        <button onClick={openNew} className="px-4 py-3 rounded-xl bg-brand text-white text-sm font-semibold flex items-center gap-2">
                            <UserPlus className="w-4 h-4" /> Ajouter un salarié
                        </button>
                    </div>
                </div>

                {alerts && (
                    <div className="grid grid-cols-3 gap-3 mb-6">
                        {[['Salariés actifs', alerts.salaries_actifs, 'text-white'],
                          ['Non conformes', alerts.non_conformes, 'text-rose-300'],
                          ['À renouveler sous 60 jours', alerts.a_renouveler, 'text-amber-300']].map(([l, v, tone]) => (
                            <div key={l} className="glass rounded-2xl border border-white/10 p-4">
                                <p className={`text-2xl font-extrabold ${tone}`}>{v}</p>
                                <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mt-1">{l}</p>
                            </div>
                        ))}
                    </div>
                )}
                {message && <div className="mb-4 rounded-xl bg-slate-800 border border-white/10 text-sm px-4 py-3">{message}</div>}

                <div className="glass rounded-2xl border border-white/10 divide-y divide-white/5">
                    {employees.length === 0 && <p className="p-6 text-sm text-slate-500 text-center">Aucun salarié enregistré.</p>}
                    {employees.map(e => {
                        const st = STATUS[e.conformite?.status] || STATUS.ok;
                        return (
                            <button key={e.id} onClick={() => setEditing(e)} className="w-full text-left p-4 hover:bg-white/[0.03] grid grid-cols-1 md:grid-cols-[1fr_auto] gap-2">
                                <div className="min-w-0">
                                    <p className={`font-semibold ${e.actif ? '' : 'line-through text-slate-500'}`}>
                                        {e.prenom} {e.nom} <span className="text-slate-400 font-normal text-sm">· {e.qualification}</span>
                                        {e.a_un_acces && <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-sky-500/15 text-sky-300">accès</span>}
                                    </p>
                                    <p className="text-xs text-slate-500 mt-1">
                                        Attestation préf. {frDate(e.attestation_prefectorale_fin)} · AFGSU 2 {frDate(e.afgsu2_fin)} · {e.contrat}
                                        {e.contrat_fin && ` jusqu’au ${frDate(e.contrat_fin)}`}
                                    </p>
                                    {[...(e.conformite?.problemes || []), ...(e.conformite?.alertes || [])].length > 0 && (
                                        <p className={`text-xs mt-1 ${e.conformite.problemes.length ? 'text-rose-300' : 'text-amber-300'}`}>
                                            {[...e.conformite.problemes, ...e.conformite.alertes].join(' · ')}
                                        </p>
                                    )}
                                </div>
                                <span className={`self-start text-xs px-2 py-1 rounded-full border flex items-center gap-1 ${st.cls}`}>
                                    <st.icon className="w-3 h-3" /> {st.label}
                                </span>
                            </button>
                        );
                    })}
                </div>
            </div>
            {editing && (
                <EmployeeDrawer employee={editing.id ? editing : null} businessId={businessId}
                    onClose={() => setEditing(null)}
                    onSaved={async (saved, note) => {
                        setEditing(note ? saved : null);
                        setMessage(note || (saved?.dossiers_recontroles ? `${saved.dossiers_recontroles} dossier(s) recontrôlé(s) avec les nouvelles dates.` : ''));
                        await refresh();
                    }} />
            )}
        </div>
    );
}

export default PmtEquipePanel;
