import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Lock, LogIn, LogOut, AlertCircle } from 'lucide-react';
import AdminView from './AdminView';

const SESSION_KEY = 'lp_admin_token';

export default function AdminLoginGate({ onBack }) {
    const [token, setToken]   = useState(() => sessionStorage.getItem(SESSION_KEY));
    const [email, setEmail]   = useState('');
    const [error, setError]   = useState('');
    const [loading, setLoading] = useState(false);

    // Inject / remove admin token on every axios request
    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['X-Admin-Token'] = token;
        } else {
            delete axios.defaults.headers.common['X-Admin-Token'];
        }
    }, [token]);

    const handleLogin = useCallback(async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const { data } = await axios.post('/admin/login', { email: email.trim() });
            sessionStorage.setItem(SESSION_KEY, data.token);
            axios.defaults.headers.common['X-Admin-Token'] = data.token;
            setToken(data.token);
        } catch (err) {
            setError(err?.response?.data?.detail || 'Accès refusé');
        } finally {
            setLoading(false);
        }
    }, [email]);

    const handleLogout = useCallback(async () => {
        try { await axios.post('/admin/logout'); } catch { /* ignore */ }
        sessionStorage.removeItem(SESSION_KEY);
        delete axios.defaults.headers.common['X-Admin-Token'];
        setToken(null);
        setEmail('');
    }, []);

    if (token) {
        return <AdminView onBack={onBack} onLogout={handleLogout} />;
    }

    return (
        <div className="flex items-center justify-center h-full bg-slate-900">
            <div className="glass rounded-3xl p-10 w-full max-w-sm shadow-2xl">
                <div className="flex flex-col items-center gap-3 mb-8">
                    <div className="w-14 h-14 rounded-2xl bg-brand/20 flex items-center justify-center">
                        <Lock className="w-7 h-7 text-brand" />
                    </div>
                    <h2 className="text-xl font-bold text-white">Accès Administration</h2>
                    <p className="text-sm text-slate-400 text-center">
                        Réservé aux adresses email autorisées
                    </p>
                </div>

                <form onSubmit={handleLogin} className="flex flex-col gap-4">
                    <input
                        type="email"
                        required
                        placeholder="votre@email.com"
                        value={email}
                        onChange={e => { setEmail(e.target.value); setError(''); }}
                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3
                                   text-white placeholder-slate-500 focus:outline-none
                                   focus:border-brand transition-colors"
                    />

                    {error && (
                        <div className="flex items-center gap-2 text-rose-400 text-sm">
                            <AlertCircle className="w-4 h-4 shrink-0" />
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading || !email}
                        className="w-full bg-brand hover:bg-brand-dark transition-colors text-white
                                   font-bold py-3 rounded-xl flex items-center justify-center gap-2
                                   disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <LogIn className="w-4 h-4" />
                        {loading ? 'Vérification…' : 'Accéder'}
                    </button>

                    <button
                        type="button"
                        onClick={onBack}
                        className="text-slate-500 hover:text-slate-300 text-sm text-center transition-colors"
                    >
                        ← Retour
                    </button>
                </form>
            </div>
        </div>
    );
}
