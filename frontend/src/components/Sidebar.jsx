import React from 'react';
import { LayoutDashboard, Target, Activity, Send, CheckCircle2, Clock, AlertCircle, Search } from 'lucide-react';

function Sidebar({ businesses, onSelect, selectedId, onOrchestrate, activeView, setActiveView }) {
    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed': return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
            case 'processing': return <Clock className="w-4 h-4 text-amber-400 animate-pulse" />;
            case 'error': return <AlertCircle className="w-4 h-4 text-rose-400" />;
            default: return <Clock className="w-4 h-4 text-slate-500" />;
        }
    };

    return (
        <div className="w-96 border-r border-white/5 bg-slate-950 flex flex-col z-[2000]">
            <div className="p-8 border-b border-white/5">
                <div className="flex items-center justify-between mb-8 opacity-0">
                    {/* Spacer for header overlay */}
                    <div className="h-10"></div>
                </div>

                <nav className="flex flex-col space-y-2 mt-8">
                    <button
                        onClick={() => setActiveView('market')}
                        className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all font-medium ${activeView === 'market' ? 'bg-white/5 text-white border border-white/10' : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                            }`}
                    >
                        <LayoutDashboard className={`w-5 h-5 ${activeView === 'market' ? 'text-brand' : ''}`} />
                        <span>Intelligence de Marché</span>
                    </button>
                    <button
                        onClick={() => setActiveView('campaigns')}
                        className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all font-medium ${activeView === 'campaigns' ? 'bg-white/5 text-white border border-white/10' : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                            }`}
                    >
                        <Target className={`w-5 h-5 ${activeView === 'campaigns' ? 'text-brand' : ''}`} />
                        <span>Campagnes</span>
                    </button>
                    <button
                        onClick={() => window.open('http://localhost:8501', '_blank')}
                        className="flex items-center space-x-3 px-4 py-3 rounded-xl transition-all font-medium text-brand bg-brand/10 border border-brand/20 hover:bg-brand/20"
                    >
                        <Activity className="w-5 h-5" />
                        <span>Live AI Cockpit</span>
                    </button>
                </nav>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                <div className="flex items-center justify-between px-2 mb-4">
                    <h2 className="text-xs font-bold uppercase tracking-widest text-slate-500">Opportunités Locales</h2>
                    <span className="bg-brand/10 text-brand text-[10px] px-2 py-0.5 rounded-full font-bold">{businesses.length} Trouvés</span>
                </div>

                {businesses.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 text-center px-6">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mb-4">
                            <Search className="w-8 h-8 text-slate-600" />
                        </div>
                        <p className="text-slate-400 text-sm">Déplacez-vous sur la carte et scannez une zone pour trouver des commerces locaux.</p>
                    </div>
                ) : (
                    businesses.map((biz) => (
                        <div
                            key={biz.id}
                            onClick={() => onSelect(biz)}
                            className={`group p-4 rounded-2xl cursor-pointer transition-all border ${selectedId === biz.id
                                ? 'bg-brand/10 border-brand/30 shadow-lg shadow-brand/5'
                                : 'bg-white/5 border-transparent hover:border-white/10 hover:bg-white/10'
                                }`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="font-bold text-sm truncate pr-2 group-hover:text-brand transition-colors">{biz.name}</h3>
                                <div className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${biz.potential_score >= 8 ? 'bg-emerald-500/20 text-emerald-400' :
                                    biz.potential_score >= 6 ? 'bg-amber-500/20 text-amber-400' :
                                        'bg-slate-500/20 text-slate-400'
                                    }`}>
                                    {biz.potential_score}
                                </div>
                            </div>

                            <div className="flex items-center justify-between text-[10px] text-slate-500 mt-3">
                                <div className="flex items-center space-x-2">
                                    {getStatusIcon(biz.status)}
                                    <span className="capitalize">{
                                        biz.status === 'processing' ? 'en cours' :
                                            biz.status === 'completed' ? 'terminé' : 'scanné'}</span>
                                </div>
                                {biz.status === 'completed' && (
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            // View URL logic here
                                        }}
                                        className="text-brand hover:underline font-bold"
                                    >
                                        Voir le Résultat
                                    </button>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            <div className="p-6 border-t border-white/5 bg-slate-950/80 backdrop-blur">
                <div className="glass rounded-xl p-4 flex items-center space-x-4">
                    <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center text-white font-bold">L</div>
                    <div>
                        <p className="text-sm font-bold">Ludovic</p>
                        <p className="text-[10px] text-emerald-400 font-medium">Plan Croissance Actif</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Sidebar;
