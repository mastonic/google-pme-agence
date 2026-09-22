import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Loader2, ShieldCheck, ShieldX } from 'lucide-react';

const TOKEN_KEY = 'lp_admin_token';

function applyToken(token) {
    if (token) {
        axios.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
        delete axios.defaults.headers.common.Authorization;
    }
}

export default function EmailGate({ onGranted }) {
    const buttonRef = useRef(null);
    const [status, setStatus] = useState('loading'); // loading | ready | denied | config
    const [message, setMessage] = useState('');
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    const verify = async (token) => {
        applyToken(token);
        try {
            const r = await axios.get('/auth/me');
            if (r.data?.email) {
                localStorage.setItem(TOKEN_KEY, token);
                onGranted(r.data);
                return true;
            }
        } catch (e) {
            applyToken(null);
            localStorage.removeItem(TOKEN_KEY);
            if (e?.response?.status === 403) {
                setStatus('denied');
                setMessage("Ce compte Google n'est pas autorisé.");
            }
        }
        return false;
    };

    useEffect(() => {
        let cancelled = false;

        const bootstrap = async () => {
            const existing = localStorage.getItem(TOKEN_KEY);
            if (existing && await verify(existing)) return;
            if (!clientId) {
                setStatus('config');
                setMessage('VITE_GOOGLE_CLIENT_ID doit être configuré pour accéder à Local Pulse.');
                return;
            }

            const initGoogle = () => {
                if (cancelled || !window.google?.accounts?.id || !buttonRef.current) return;
                window.google.accounts.id.initialize({
                    client_id: clientId,
                    callback: async ({ credential }) => {
                        if (!credential) return;
                        setStatus('loading');
                        const ok = await verify(credential);
                        if (!ok && !cancelled) {
                            setStatus('denied');
                            setMessage("Connexion refusée ou jeton invalide.");
                        }
                    },
                });
                window.google.accounts.id.renderButton(buttonRef.current, {
                    theme: 'filled_black',
                    size: 'large',
                    shape: 'pill',
                    text: 'signin_with',
                    width: 300,
                });
                setStatus('ready');
            };

            if (window.google?.accounts?.id) {
                initGoogle();
                return;
            }

            let script = document.querySelector('script[data-localpulse-google-auth]');
            if (!script) {
                script = document.createElement('script');
                script.src = 'https://accounts.google.com/gsi/client';
                script.async = true;
                script.defer = true;
                script.dataset.localpulseGoogleAuth = '1';
                document.head.appendChild(script);
            }
            script.addEventListener('load', initGoogle, { once: true });
            script.addEventListener('error', () => {
                if (!cancelled) {
                    setStatus('denied');
                    setMessage('Impossible de charger la connexion Google.');
                }
            }, { once: true });
        };

        bootstrap();
        return () => { cancelled = true; };
    }, [clientId]);

    return (
        <div className="flex min-h-screen w-full items-center justify-center bg-slate-950 p-6 text-white">
            <div className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
                <div className="mb-6 flex justify-center">
                    <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand/15 border border-brand/25">
                        {status === 'denied' || status === 'config'
                            ? <ShieldX className="h-8 w-8 text-rose-400" />
                            : <ShieldCheck className="h-8 w-8 text-brand" />
                        }
                    </div>
                </div>

                <h1 className="text-center text-2xl font-bold">Local Pulse</h1>
                <p className="mt-2 text-center text-sm text-slate-400">
                    Cockpit privé de prospection et de croissance locale.
                </p>

                <div className="mt-8 flex min-h-[52px] items-center justify-center">
                    {status === 'loading' && (
                        <div className="flex items-center gap-2 text-sm text-slate-400">
                            <Loader2 className="h-4 w-4 animate-spin text-brand" />
                            Vérification de l'accès…
                        </div>
                    )}
                    <div ref={buttonRef} className={status === 'ready' ? 'block' : 'hidden'} />
                </div>

                {(status === 'denied' || status === 'config') && (
                    <div className="mt-5 rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
                        {message}
                    </div>
                )}

                <p className="mt-6 text-center text-[10px] leading-relaxed text-slate-600">
                    L'autorisation est vérifiée côté serveur. Aucune liste d'adresses admin n'est embarquée dans le navigateur.
                </p>
            </div>
        </div>
    );
}
