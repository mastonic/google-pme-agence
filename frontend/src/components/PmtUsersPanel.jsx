import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Users, UserPlus, KeyRound, Power, Trash2 } from 'lucide-react';

// Comptes du module transport (admin) : un compte client par ambulancier,
// rattaché à son entreprise ; il ne voit que ses dossiers.

function PmtUsersPanel({ businesses = [] }) {
    const [users, setUsers] = useState([]);
    const [form, setForm] = useState({ email: '', password: '', role: 'client', business_id: '' });
    const [message, setMessage] = useState('');

    const refresh = async () => setUsers((await axios.get('/pmt/auth/users')).data);
    useEffect(() => { refresh().catch(e => setMessage(e?.response?.data?.detail || e.message)); }, []);

    const businessName = (id) => businesses.find(b => b.id === id)?.name || id;

    const create = async (e) => {
        e.preventDefault();
        setMessage('');
        try {
            await axios.post('/pmt/auth/users', form);
            setForm({ email: '', password: '', role: 'client', business_id: '' });
            setMessage('Compte créé. Transmets le mot de passe au client par un autre canal que l’e-mail.');
            await refresh();
        } catch (err) {
            setMessage(err?.response?.data?.detail || err.message);
        }
    };

    const patch = async (u, body, done) => {
        try {
            await axios.patch(`/pmt/auth/users/${u.id}`, body);
            setMessage(done);
            await refresh();
        } catch (err) {
            setMessage(err?.response?.data?.detail || err.message);
        }
    };

    const resetPassword = (u) => {
        const pw = window.prompt(`Nouveau mot de passe pour ${u.email} (10 caractères minimum, lettres et chiffres)`);
        if (pw) patch(u, { password: pw }, 'Mot de passe changé : les sessions ouvertes de ce compte sont fermées.');
    };

    const remove = async (u) => {
        if (!window.confirm(`Supprimer le compte ${u.email} ?`)) return;
        try {
            await axios.delete(`/pmt/auth/users/${u.id}`);
            await refresh();
        } catch (err) {
            setMessage(err?.response?.data?.detail || err.message);
        }
    };

    const field = 'bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm';

    return (
        <div className="w-full h-full overflow-y-auto p-4 md:p-8">
            <div className="max-w-5xl mx-auto">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-11 h-11 rounded-2xl bg-brand/15 border border-brand/30 flex items-center justify-center">
                        <Users className="w-6 h-6 text-brand" />
                    </div>
                    <div>
                        <h2 className="text-3xl font-extrabold">Comptes</h2>
                        <p className="text-slate-400 text-sm">Un compte par ambulancier : il ne voit que les dossiers de son entreprise.</p>
                    </div>
                </div>

                <form onSubmit={create} className="glass rounded-2xl border border-white/10 p-4 mb-6 grid grid-cols-1 md:grid-cols-[1fr_1fr_140px_1fr_auto] gap-3">
                    <input required type="email" placeholder="E-mail" value={form.email}
                        onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className={field} />
                    <input required type="text" placeholder="Mot de passe (10+ car.)" value={form.password}
                        onChange={e => setForm(f => ({ ...f, password: e.target.value }))} className={field} />
                    <select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))} className={field}>
                        <option value="client">Client</option>
                        <option value="employe">Équipier</option>
                        <option value="admin">Admin agence</option>
                    </select>
                    <select value={form.business_id} disabled={form.role === 'admin'} required={form.role !== 'admin'}
                        onChange={e => setForm(f => ({ ...f, business_id: e.target.value }))} className={field}>
                        <option value="">Entreprise du client…</option>
                        {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                    </select>
                    <button className="px-4 py-2 rounded-xl bg-brand text-white text-sm font-semibold flex items-center justify-center gap-1">
                        <UserPlus className="w-4 h-4" /> Créer
                    </button>
                </form>
                {message && <div className="mb-4 rounded-xl bg-slate-800 border border-white/10 text-sm px-4 py-3">{message}</div>}

                <div className="glass rounded-2xl border border-white/10 divide-y divide-white/5">
                    {users.map(u => (
                        <div key={u.id} className="p-4 flex flex-wrap items-center justify-between gap-3">
                            <div className="min-w-0">
                                <p className={`font-semibold ${u.active ? '' : 'line-through text-slate-500'}`}>{u.email}</p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {u.role === 'admin' ? 'Admin agence' : `${u.role === 'employe' ? 'Équipier' : 'Gérant'} · ${businessName(u.business_id)}`}
                                    {' · '}dernière connexion : {u.last_login_at ? new Date(u.last_login_at + 'Z').toLocaleString('fr-FR') : 'jamais'}
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <button onClick={() => resetPassword(u)} className="px-3 py-1.5 rounded-lg bg-slate-800 border border-white/10 text-xs flex items-center gap-1">
                                    <KeyRound className="w-3 h-3" /> Mot de passe
                                </button>
                                <button onClick={() => patch(u, { active: !u.active }, u.active ? 'Compte désactivé.' : 'Compte réactivé.')}
                                    className="px-3 py-1.5 rounded-lg bg-slate-800 border border-white/10 text-xs flex items-center gap-1">
                                    <Power className="w-3 h-3" /> {u.active ? 'Désactiver' : 'Réactiver'}
                                </button>
                                <button onClick={() => remove(u)} className="px-3 py-1.5 rounded-lg border border-rose-500/30 text-rose-300 text-xs">
                                    <Trash2 className="w-3 h-3" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default PmtUsersPanel;
