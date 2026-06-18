import React, { useState } from 'react';
import { LayoutDashboard, Target, CheckCircle2, Clock, AlertCircle, Search, Settings, MapPin, Loader2, X, Activity, CreditCard, Users } from 'lucide-react';
import axios from 'axios';

function Sidebar({ businesses, onSelect, selectedId, onOrchestrate, activeView, setActiveView, onScanResult, isScanning, setIsScanning, isOpen, onClose }) {
    const activeCount = businesses.filter(b => b.status === 'processing').length;
    const [searchQuery, setSearchQuery] = useState('');
    const [searchError, setSearchError] = useState(null);

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed': return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
            case 'processing': return <Clock className="w-4 h-4 text-amber-400 animate-pulse" />;
            case 'error': return <AlertCircle className="w-4 h-4 text-rose-400" />;
            default: return <Clock className="w-4 h-4 text-slate-500" />;
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;
        setSearchError(null);
        setIsScanning(true);
        try {
            const geo = await axios.get(`/geocode?address=${encodeURIComponent(searchQuery)}`);
            const { lat, lng } = geo.data;
            const scan = await axios.post(`/scan?lat=${lat}&lng=${lng}&radius=1000`);
            if (scan.data?.businesses) {
                onScanResult(scan.data.businesses, lat, lng);
                if (scan.data.businesses.length === 0) {
                    setSearchError('Aucun commerce trouvé. Essayez un autre lieu.');
                }
            }
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || 'Erreur de localisation';
            setSearchError(msg);
        } finally {
            setIsScanning(false);
        }
    };

    const handleNav = (id) => {
        setActiveView(id);
        if (onClose) onClose(); // ferme le drawer sur mobile
    };

    const navItems = [
        { id: 'market',    label: 'Carte & Prospection', icon: LayoutDashboard },
        { id: 'campaigns', label: 'Campagnes',            icon: Target },
        { id: 'crm',       label: 'CRM Pipeline',        icon: Users },
        { id: 'cockpit',   label: 'Live Cockpit',         icon: Activity },
        { id: 'pricing',   label: 'Offres & Prix',        icon: CreditCard },
        { id: 'admin',     label: 'Administration',       icon: Settings },
    ];

    return (
        <>
            {/* Backdrop mobile */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/60 z-[2999] md:hidden"
                    onClick={onClose}
                />
            )}

            <div className={`
                fixed md:relative inset-y-0 left-0
                w-full sm:w-80 md:w-60 lg:w-72
                z-[3000] md:z-[2000]
                transition-transform duration-300 ease-in-out
                ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
                border-r border-white/5 bg-slate-950 flex flex-col h-full
            `}>

                {/* Logo + close button mobile */}
                <div className="p-4 lg:p-6 border-b border-white/5">
                    <div className="flex items-center justify-between mb-4 lg:mb-6">
                        <div className="flex items-center space-x-3">
                            <div className="w-9 h-9 lg:w-10 lg:h-10 bg-brand rounded-lg flex items-center justify-center shadow-lg shadow-brand/20 flex-shrink-0">
                                <span className="text-lg lg:text-xl font-bold italic">LP</span>
                            </div>
                            <div>
                                <h1 className="text-base lg:text-lg font-bold tracking-tight">Local-Pulse</h1>
                                <p className="text-[10px] text-slate-400">Prospection & SaaS PME</p>
                            </div>
                        </div>
                        {/* Bouton fermer visible uniquement sur mobile */}
                        <button
                            onClick={onClose}
                            className="md:hidden p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Navigation */}
                    <nav className="flex flex-col space-y-1">
                        {navItems.map(({ id, label, icon: Icon }) => (
                            <button
                                key={id}
                                onClick={() => handleNav(id)}
                                className={`flex items-center space-x-3 px-3 lg:px-4 py-2 lg:py-2.5 rounded-xl transition-all font-medium text-sm ${
                                    activeView === id
                                        ? 'bg-brand/10 text-white border border-brand/20'
                                        : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                                }`}
                            >
                                <Icon className={`w-4 h-4 flex-shrink-0 ${activeView === id ? 'text-brand' : ''}`} />
                                <span className="flex-1 text-left">{label}</span>
                                {id === 'cockpit' && activeCount > 0 && (
                                    <span className="flex items-center gap-1 bg-amber-500/20 border border-amber-500/30 text-amber-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                                        {activeCount}
                                    </span>
                                )}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Search & Scan */}
                <div className="p-3 lg:p-4 border-b border-white/5">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2 lg:mb-3">Scanner une zone</p>
                    <form onSubmit={handleSearch} className="flex gap-2">
                        <div className="relative flex-1">
                            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={e => { setSearchQuery(e.target.value); setSearchError(null); }}
                                placeholder="Ville ou code postal..."
                                className="w-full pl-9 pr-3 py-2.5 bg-slate-800 border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand transition-colors"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={isScanning || !searchQuery.trim()}
                            className="px-3 py-2.5 bg-brand hover:bg-brand-dark rounded-xl transition-colors disabled:opacity-50 flex-shrink-0"
                            title="Scanner"
                        >
                            {isScanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                        </button>
                    </form>
                    {searchError && (
                        <div className="mt-2 flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-2 rounded-lg">
                            <span className="flex-1">{searchError}</span>
                            <button onClick={() => setSearchError(null)}><X className="w-3 h-3" /></button>
                        </div>
                    )}
                    <p className="text-[10px] text-slate-600 mt-2 hidden lg:block">Ou cliquez sur le bouton "Scanner" sur la carte</p>
                </div>

                {/* KPIs rapides */}
                <div className="px-3 lg:px-4 py-3 border-b border-white/5 grid grid-cols-3 gap-2">
                    {[
                        { label: 'Scannés',  value: businesses.length,                                                                    color: 'text-white' },
                        { label: 'Cibles',   value: businesses.filter(b => b.potential_score < 4).length,                                 color: 'text-red-400' },
                        { label: 'Pipeline', value: businesses.filter(b => ['processing','completed'].includes(b.status)).length,         color: 'text-amber-400' },
                    ].map(({ label, value, color }) => (
                        <div key={label} className="text-center">
                            <p className={`text-lg lg:text-xl font-bold ${color}`}>{value}</p>
                            <p className="text-[9px] text-slate-500 uppercase tracking-wider">{label}</p>
                        </div>
                    ))}
                </div>

                {/* Business list */}
                <div className="flex-1 overflow-y-auto p-3 space-y-2" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,.1) transparent' }}>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 px-1 mb-1">
                        Opportunités · {businesses.length}
                    </p>
                    {businesses.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-10 text-center px-4">
                            <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mb-3">
                                <Search className="w-6 h-6 text-slate-600" />
                            </div>
                            <p className="text-slate-400 text-sm">Recherchez une ville ou scannez la carte pour trouver des commerces locaux.</p>
                        </div>
                    ) : (
                        businesses.map((biz) => (
                            <div
                                key={biz.id}
                                onClick={() => { onSelect(biz); handleNav('market'); }}
                                className={`group p-3 rounded-xl cursor-pointer transition-all border ${
                                    selectedId === biz.id
                                        ? 'bg-brand/10 border-brand/30'
                                        : 'bg-white/[0.03] border-transparent hover:border-white/10 hover:bg-white/5'
                                }`}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <h3 className="font-semibold text-sm truncate pr-2 group-hover:text-brand transition-colors leading-tight">{biz.name}</h3>
                                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded flex-shrink-0 ${
                                        biz.potential_score >= 7 ? 'bg-emerald-500/20 text-emerald-400' :
                                        biz.potential_score >= 2.5 ? 'bg-amber-500/20 text-amber-400' :
                                        'bg-red-500/20 text-red-400'
                                    }`}>{biz.potential_score}</span>
                                </div>
                                <p className="text-[11px] text-slate-500 truncate mb-2">{biz.address}</p>
                                <div className="flex items-center justify-between text-[10px] text-slate-500">
                                    <div className="flex items-center space-x-1.5">
                                        {getStatusIcon(biz.status)}
                                        <span className="capitalize">{
                                            biz.status === 'processing' ? 'en cours' :
                                            biz.status === 'completed' ? 'terminé' :
                                            biz.status === 'pending_validation' ? 'à valider' :
                                            'scanné'
                                        }</span>
                                    </div>
                                    {biz.status === 'completed' && biz.deployment_url && (
                                        <a href={biz.deployment_url} target="_blank" rel="noopener noreferrer"
                                           onClick={e => e.stopPropagation()}
                                           className="text-brand hover:underline font-bold">Site ↗</a>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Footer user */}
                <div className="p-3 lg:p-4 border-t border-white/5 space-y-2">
                    <a
                        href="/"
                        className="flex items-center gap-2 px-3 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 border border-transparent transition-all text-sm font-medium"
                    >
                        <span className="text-base leading-none">←</span>
                        <span>Retour au site</span>
                    </a>
                    <div className="flex items-center space-x-3 px-3 py-2.5 rounded-xl bg-white/[0.03] border border-white/5">
                        <div className="w-8 h-8 rounded-full bg-brand flex items-center justify-center text-white font-bold text-sm flex-shrink-0">L</div>
                        <div className="min-w-0">
                            <p className="text-sm font-bold truncate">Ludovic</p>
                            <p className="text-[10px] text-brand font-medium">Admin</p>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

export default Sidebar;
