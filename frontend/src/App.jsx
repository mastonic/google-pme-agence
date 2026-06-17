import React, { useState, useEffect } from 'react';
import MapComponent from './components/MapComponent';
import Sidebar from './components/Sidebar';
import AgentTracker from './components/AgentTracker';
import CampaignsView from './components/CampaignsView';
import AdminView from './components/AdminView';
import LiveCockpit from './components/LiveCockpit';
import PricingView from './components/PricingView';
import CrmView from './components/CrmView';
import ScoreBreakdownPanel from './components/ScoreBreakdownPanel';
import axios from 'axios';
import { Loader2, Menu } from 'lucide-react';

function App() {
    const [businesses, setBusinesses] = useState([]);
    const [selectedId, setSelectedId] = useState(() => localStorage.getItem('lp_selected_id'));
    const [selectedBusiness, setSelectedBusiness] = useState(null);
    const [isScanning, setIsScanning] = useState(false);
    const [scanError, setScanError] = useState('');
    const [activeView, setActiveView] = useState(() => localStorage.getItem('lp_active_view') || 'market');
    const [newlyOrchestratedId, setNewlyOrchestratedId] = useState(null);
    const [mapCenter, setMapCenter] = useState(null);

    useEffect(() => { fetchBusinesses(); }, []);

    const fetchBusinesses = async () => {
        try {
            const r = await axios.get('/businesses');
            if (Array.isArray(r.data)) {
                setBusinesses(prev => {
                    // Merge remote + local: remote wins for shared IDs (has fresh status),
                    // but we keep locally-scanned businesses that may not exist in this
                    // Cloud Run instance's DB yet (multi-instance SQLite problem).
                    const remoteMap = new Map(r.data.map(b => [b.id, b]));
                    const merged = new Map(prev.map(b => [b.id, b]));
                    for (const [id, b] of remoteMap) merged.set(id, b);
                    return Array.from(merged.values())
                        // Score Digital croissant : cibles prioritaires (faible présence) en tête
                        .sort((a, b) => (a.potential_score || 0) - (b.potential_score || 0));
                });
            }
        } catch (e) {
            console.error('Error fetching businesses:', e);
        }
    };

    useEffect(() => {
        if (selectedId && !selectedBusiness && businesses.length > 0) {
            const b = businesses.find(b => b.id === selectedId);
            if (b) setSelectedBusiness(b);
        }
    }, [businesses, selectedId]);

    useEffect(() => {
        localStorage.setItem('lp_active_view', activeView);
    }, [activeView]);

    const [isLoadingDetail, setIsLoadingDetail] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const handleSelectBusiness = async (business) => {
        if (business) {
            setSelectedId(business.id);
            localStorage.setItem('lp_selected_id', business.id);
            setSelectedBusiness(business);
            setIsLoadingDetail(true);
            try {
                const r = await axios.get(`/businesses/${business.id}`);
                setSelectedBusiness(r.data);
                setBusinesses(prev => prev.map(b => b.id === business.id ? r.data : b));
            } catch (e) {
                console.error('Error loading business details:', e);
            } finally {
                setIsLoadingDetail(false);
            }
        } else {
            setSelectedBusiness(null);
            setSelectedId(null);
            localStorage.removeItem('lp_selected_id');
        }
    };

    // Called from MapComponent scan button (uses current map center)
    const handleScanAtPosition = async (lat, lng) => {
        setIsScanning(true);
        setScanError('');
        try {
            const r = await axios.post(`/scan?lat=${lat}&lng=${lng}&radius=1000`);
            if (r.data?.businesses) setBusinesses(r.data.businesses);
            else fetchBusinesses();
        } catch (e) {
            console.error('Scan error:', e);
            const msg = e?.response?.data?.detail || e?.message || 'Erreur de scan';
            setScanError(msg);
        } finally {
            setIsScanning(false);
        }
    };

    // Called from Sidebar city search
    const handleScanResult = (bizList, lat, lng) => {
        setBusinesses(bizList);
        setMapCenter({ lat, lng });
        setActiveView('market');
    };

    const handleOrchestrate = async (businessId) => {
        try {
            setBusinesses(prev => prev.map(b => b.id === businessId ? { ...b, status: 'processing' } : b));
            if (selectedBusiness?.id === businessId)
                setSelectedBusiness(prev => ({ ...prev, status: 'processing' }));

            axios.post(`/orchestrate/${businessId}`);
            setNewlyOrchestratedId(businessId);
            setActiveView('campaigns');
            // Don't call fetchBusinesses here — it can overwrite the local 'processing'
            // status with stale data from another Cloud Run instance.
        } catch (e) {
            console.error('Error orchestrating:', e);
        }
    };

    return (
        <div className="flex h-screen w-screen overflow-hidden bg-slate-900 text-white font-sans">
            <Sidebar
                businesses={businesses}
                onSelect={handleSelectBusiness}
                selectedId={selectedId}
                onOrchestrate={handleOrchestrate}
                activeView={activeView}
                setActiveView={setActiveView}
                onScanResult={handleScanResult}
                isScanning={isScanning}
                setIsScanning={setIsScanning}
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
            />

            <main className="flex-1 relative h-full overflow-hidden">
                {/* Hamburger — mobile only, visible sur toutes les vues */}
                <button
                    onClick={() => setSidebarOpen(true)}
                    className="md:hidden absolute top-4 left-4 z-[2500] glass p-2.5 rounded-xl shadow-xl"
                    aria-label="Menu"
                >
                    <Menu className="w-5 h-5" />
                </button>

                {activeView === 'market' ? (
                    <>
                        <MapComponent
                            businesses={businesses}
                            onScan={handleScanAtPosition}
                            isScanning={isScanning}
                            onSelectBusiness={handleSelectBusiness}
                            centerTarget={mapCenter}
                        />
                        {scanError && (
                            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[2000] bg-rose-500/90 backdrop-blur text-white px-5 py-3 rounded-2xl text-sm font-medium shadow-xl flex items-center gap-2 max-w-md">
                                ❌ {scanError}
                            </div>
                        )}

                        {/* Score Legend — caché sur mobile pour libérer de l'espace */}
                        <div className="hidden sm:block absolute bottom-6 left-6 z-[1000] glass p-4 rounded-xl">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Cibles Prosp.</h4>
                            <div className="space-y-2 text-sm">
                                {[
                                    { color: 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]',     label: '0-2 Faible · prioritaire' },
                                    { color: 'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]', label: '3-6 Présence moyenne' },
                                ].map(({ color, label }) => (
                                    <div key={label} className="flex items-center space-x-2">
                                        <div className={`w-3 h-3 rounded-full ${color}`} />
                                        <span className="font-medium text-xs">{label}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Selected Business popup */}
                        {selectedBusiness && (
                            <div className="absolute bottom-0 sm:bottom-6 left-0 sm:left-1/2 sm:-translate-x-1/2 z-[1000] w-full sm:max-w-md max-h-[80vh] overflow-y-auto">
                                <div className="glass p-4 sm:p-6 rounded-t-2xl sm:rounded-2xl mx-0 sm:mx-4 shadow-2xl">
                                    <div className="flex justify-between items-start mb-3 relative min-h-[80px]">
                                        {isLoadingDetail && (
                                            <div className="absolute inset-0 z-10 bg-slate-900/40 backdrop-blur-[2px] flex items-center justify-center rounded-xl">
                                                <Loader2 className="w-8 h-8 animate-spin text-brand" />
                                            </div>
                                        )}
                                        <div className="pr-4">
                                            <h3 className="text-xl font-bold">{selectedBusiness.name}</h3>
                                            <p className="text-sm text-slate-400 mt-1">{selectedBusiness.address}</p>
                                            {selectedBusiness.rating > 0 && (
                                                <div className="flex items-center text-amber-400 text-sm font-medium mt-1">
                                                    <span className="mr-1">★</span>
                                                    {selectedBusiness.rating} ({selectedBusiness.user_ratings_total || 0})
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex flex-col items-end gap-1 shrink-0">
                                            <div className={`px-3 py-1 rounded-full border text-xs font-bold whitespace-nowrap ${
                                                selectedBusiness.potential_score >= 7 ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                                                selectedBusiness.potential_score >= 2.5 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                                                'bg-red-500/20 text-red-400 border-red-500/30'
                                            }`}>
                                                {selectedBusiness.potential_score}/10
                                            </div>
                                            <button onClick={() => handleSelectBusiness(null)}
                                                className="text-slate-400 hover:text-white transition-colors text-lg leading-none mt-1">
                                                ✕
                                            </button>
                                        </div>
                                    </div>

                                    {/* Score breakdown — toujours visible */}
                                    {selectedBusiness.score_breakdown && (
                                        <ScoreBreakdownPanel breakdown={selectedBusiness.score_breakdown} />
                                    )}

                                    <button
                                        onClick={() => handleOrchestrate(selectedBusiness.id)}
                                        disabled={selectedBusiness.status === 'processing'}
                                        className="w-full bg-brand hover:bg-brand-dark transition-colors text-white font-bold py-3 rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-brand/30 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {selectedBusiness.status === 'processing' ? (
                                            <><Loader2 className="w-5 h-5 animate-spin" /><span>Création en cours...</span></>
                                        ) : (
                                            <span>✨ Créer les Actifs Numériques</span>
                                        )}
                                    </button>
                                    {selectedBusiness.status === 'processing' && (
                                        <div className="mt-4">
                                            <AgentTracker isProcessing={true} businessId={selectedBusiness.id} />
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </>
                ) : activeView === 'admin' ? (
                    <AdminView onBack={() => setActiveView('market')} />
                ) : activeView === 'crm' ? (
                    <CrmView />
                ) : activeView === 'cockpit' ? (
                    <LiveCockpit businesses={businesses} onRefresh={fetchBusinesses} />
                ) : activeView === 'pricing' ? (
                    <PricingView />
                ) : (
                    <CampaignsView
                        businesses={businesses}
                        initialSelectedId={newlyOrchestratedId}
                        onGoToCrm={() => setActiveView('crm')}
                        onDeploy={async (id) => {
                            try {
                                setBusinesses(prev => prev.map(b => b.id === id ? { ...b, status: 'processing' } : b));
                                await axios.post(`/deploy/${id}`);
                                fetchBusinesses();
                            } catch (e) {
                                console.error('Deploy error:', e);
                                fetchBusinesses();
                            }
                        }}
                        onRegenerate={(id) => handleOrchestrate(id)}
                    />
                )}
            </main>
        </div>
    );
}

export default App;
