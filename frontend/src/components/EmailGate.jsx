import React, { useState } from 'react';
import { Mail, ShieldCheck, ShieldX, ArrowRight } from 'lucide-react';

const WHITELIST = [
    'tontonmasto1@protonmail.com',
    'tontonmasto2@protonmail.com',
    'rigahludovic@gmail.com',
];

export default function EmailGate({ onGranted }) {
    const [email, setEmail] = useState('');
    const [status, setStatus] = useState('idle'); // 'idle' | 'denied'

    const handleSubmit = (e) => {
        e.preventDefault();
        const normalized = email.trim().toLowerCase();
        if (WHITELIST.includes(normalized)) {
            onGranted();
        } else {
            setStatus('denied');
        }
    };

    return (
        <div className="flex h-full w-full items-center justify-center bg-slate-900 p-6">
            <div className="w-full max-w-sm glass rounded-2xl border border-white/10 p-8 shadow-2xl">
                {/* Icon */}
                <div className="mb-6 flex justify-center">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand/15 border border-brand/25">
                        {status === 'denied'
                            ? <ShieldX className="h-7 w-7 text-rose-400" />
                            : <ShieldCheck className="h-7 w-7 text-brand" />
                        }
                    </div>
                </div>

                <h2 className="mb-1 text-center text-lg font-bold text-white">
                    Accès Administration
                </h2>
                <p className="mb-7 text-center text-sm text-slate-400">
                    Entrez votre adresse e-mail pour accéder à l&apos;outil.
                </p>

                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <div className="relative">
                        <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => { setEmail(e.target.value); setStatus('idle'); }}
                            placeholder="votre@email.com"
                            required
                            autoFocus
                            className="w-full rounded-xl border border-white/10 bg-slate-800 py-3 pl-10 pr-4 text-sm text-white placeholder-slate-500 outline-none transition-colors focus:border-brand"
                        />
                    </div>

                    {status === 'denied' && (
                        <p className="flex items-center gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-2.5 text-sm text-rose-400">
                            <ShieldX className="h-4 w-4 flex-shrink-0" />
                            Accès refusé. Cet e-mail n&apos;est pas autorisé.
                        </p>
                    )}

                    <button
                        type="submit"
                        className="flex items-center justify-center gap-2 rounded-xl bg-brand py-3 text-sm font-semibold text-white transition-opacity hover:opacity-88 active:opacity-75"
                    >
                        Accéder
                        <ArrowRight className="h-4 w-4" />
                    </button>
                </form>
            </div>
        </div>
    );
}
