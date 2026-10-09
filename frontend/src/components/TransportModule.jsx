import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Ambulance, LogIn, LogOut, Loader2, ShieldCheck } from 'lucide-react';
import TransportPmtView from './TransportPmtView';
import PmtRejetsPanel from './PmtRejetsPanel';
import PmtTracesPanel from './PmtTracesPanel';
import PmtUsersPanel from './PmtUsersPanel';
import { installPmtInterceptors, loadSession, saveSession } from './pmtAuth';

// Module transport sanitaire : connexion, puis dossiers / rejets CPAM / comptes.

function LoginForm({ onLogged }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');

    const submit = async (e) => {
        e.preventDefault();
        setBusy(true); setError('');
        try {
            const r = await axios.post('/pmt/auth/login', { email, password });
            onLogged({ token: r.data.token, user: r.data.user });
        } catch (err) {
            setError(err?.response?.data?.detail || err.message);
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="flex h-full w-full items-center justify-center bg-slate-900 p-6">
            <form onSubmit={submit} className="w-full max-w-sm glass rounded-2xl border border-white/10 p-8 space-y-4">
                <div className="flex justify-center">
                    <div className="h-14 w-14 rounded-2xl bg-brand/15 border border-brand/25 flex items-center justify-center">
                        <Ambulance className="h-7 w-7 text-brand" />
                    </div>
                </div>
                <div className="text-center">
                    <h2 className="text-lg font-bold">Transport sanitaire</h2>
                    <p className="text-sm text-slate-400 mt-1">Données de santé : connexion obligatoire.</p>
                </div>
                <input type="email" required autoFocus value={email} onChange={e => setEmail(e.target.value)}
                    placeholder="E-mail" autoComplete="username"
                    className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-sm outline-none focus:border-brand" />
                <input type="password" required value={password} onChange={e => setPassword(e.target.value)}
                    placeholder="Mot de passe" autoComplete="current-password"
                    className="w-full rounded-xl border border-white/10 bg-slate-800 px-4 py-3 text-sm outline-none focus:border-brand" />
                {error && <p className="text-sm text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2">{error}</p>}
                <button type="submit" disabled={busy}
                    className="w-full rounded-xl bg-brand py-3 text-sm font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-50">
                    {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />} Se connecter
                </button>
            </form>
        </div>
    );
}

function TransportModule({ businesses = [] }) {
    const [session, setSession] = useState(loadSession);
    const [tab, setTab] = useState('dossiers');

    useEffect(() => { installPmtInterceptors(() => setSession(null)); }, []);

    const logged = (s) => { saveSession(s); setSession(s); };
    const logout = () => { saveSession(null); setSession(null); };

    if (!session?.token) return <LoginForm onLogged={logged} />;

    const user = session.user;
    const tabs = [
        ['dossiers', 'Dossiers'],
        ['traces', 'Traces GPS'],
        ['rejets', 'Rejets CPAM'],
        ...(user.role === 'admin' ? [['comptes', 'Comptes']] : []),
    ];
    // Un client ne voit que son entreprise : pas de sélecteur.
    const visibleBusinesses = user.role === 'admin' ? businesses : businesses.filter(b => b.id === user.business_id);

    return (
        <div className="w-full h-full flex flex-col bg-slate-900">
            <div className="flex items-center justify-between gap-3 px-4 md:px-8 pt-4 border-b border-white/5">
                <div className="flex gap-1 overflow-x-auto">
                    {tabs.map(([id, label]) => (
                        <button key={id} onClick={() => setTab(id)}
                            className={`px-4 py-2.5 text-sm font-semibold border-b-2 -mb-px whitespace-nowrap ${tab === id
                                ? 'border-brand text-white' : 'border-transparent text-slate-400 hover:text-white'}`}>
                            {label}
                        </button>
                    ))}
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400 pb-2">
                    <span className="hidden sm:flex items-center gap-1">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />{user.email}
                        {user.role === 'admin' && <span className="ml-1 px-1.5 py-0.5 rounded bg-brand/20 text-brand">admin</span>}
                    </span>
                    <button onClick={logout} className="flex items-center gap-1 hover:text-white"><LogOut className="w-4 h-4" /> Déconnexion</button>
                </div>
            </div>
            <div className="flex-1 min-h-0">
                {tab === 'dossiers' && <TransportPmtView businesses={visibleBusinesses} user={user} />}
                {tab === 'traces' && <PmtTracesPanel businesses={visibleBusinesses} user={user} />}
                {tab === 'rejets' && <PmtRejetsPanel businesses={visibleBusinesses} user={user} />}
                {tab === 'comptes' && user.role === 'admin' && <PmtUsersPanel businesses={businesses} />}
            </div>
        </div>
    );
}

export default TransportModule;
