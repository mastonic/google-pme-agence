import React, { useState, useEffect } from 'react';
import MapComponent from './components/MapComponent';
import Sidebar from './components/Sidebar';
import AgentTracker from './components/AgentTracker';
import CampaignsView from './components/CampaignsView';
import AdminView from './components/AdminView';
import LiveCockpit from './components/LiveCockpit';
import axios from 'axios';
import { Loader2 } from 'lucide-react';

function App() {
    const [businesses, setBusinesses] = useState([]);
    const [selectedId, setSelectedId] = useState(() => localStorage.getItem('lp_selected_id'));
    const [selectedBusiness, setSelectedBusiness] = useState(null);
    const [isScanning, setIsScanning] = useState(false);
    const [activeView, setActiveView] = useState(() => localStorage.getItem('lp_active_view') || 'market');
    const [newlyOrchestratedId, setNewlyOrchestratedId] = useState(null);
    const [mapCenter, setMapCenter] = useState(null);

    useEffect(() => { fetchBusinesses(); }, []);

    const fetchBusinesses = async () => {
        try {
            const r = await axios.get('/businesses');
            if (Array.isArray(r.data)) setBusinesses(r.data);
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
        try {
            const r = await axios.post(`/scan?lat=${lat}&lng=${lng}&radius=1000`);
            if (r.data?.businesses) setBusinesses(r.data.businesses);
            else fetchBusinesses();
        } catch (e) {
            console.error('Scan error:', e);
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
            setTimeout(fetchBusinesses, 500);
        } catch (e) {
            console.error('Error orchestrating:', e);
            fetchBusinesses();
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
            />

            <main className="flex-1 relative h-full overflow-hidden">
                {activeView === 'market' ? (
                    <>
                        <MapComponent
                            businesses={businesses}
                            onScan={handleScanAtPosition}
                            isScanning={isScanning}
                            onSelectBusiness={handleSelectBusiness}
                            centerTarget={mapCenter}
                        />

                        {/* Score Legend */}
                        <div className="absolute bottom-6 left-6 z-[1000] glass p-4 rounded-xl">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Score</h4>
                            <div className="space-y-2 text-sm">
                                {[
                                    { color: 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]', label: '8-10 Lead Chaud' },
                                    { color: 'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]',   label: '6-7 Lead Tiède' },
                                    { color: 'bg-slate-500',                                            label: '0-5 Froid' },
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
                            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[1000] w-full max-w-md">
                                <div className="glass p-6 rounded-2xl mx-4 shadow-2xl">
                                    <div className="flex justify-between items-start mb-4 relative min-h-[80px]">
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
                                        <div className={`px-3 py-1 rounded-full border text-xs font-bold whitespace-nowrap ${
                                            selectedBusiness.potential_score >= 8 ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                                            selectedBusiness.potential_score >= 6 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                                            'bg-slate-500/20 text-slate-400 border-slate-500/30'
                                        }`}>
                                            {selectedBusiness.potential_score}/10
                                        </div>
                                    </div>
                                    <div className="flex space-x-3">
                                        <button
                                            onClick={() => handleOrchestrate(selectedBusiness.id)}
                                            disabled={selectedBusiness.status === 'processing'}
                                            className="flex-1 bg-brand hover:bg-brand-dark transition-colors text-white font-bold py-3 rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-brand/30 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {selectedBusiness.status === 'processing' ? (
                                                <><Loader2 className="w-5 h-5 animate-spin" /><span>Création en cours...</span></>
                                            ) : (
                                                <span>✨ Créer les Actifs Numériques</span>
                                            )}
                                        </button>
                                        <button onClick={() => handleSelectBusiness(null)}
                                            className="px-4 py-3 rounded-xl border border-white/10 hover:bg-white/5 transition-colors">
                                            ✕
                                        </button>
                                    </div>
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
                ) : activeView === 'cockpit' ? (
                    <LiveCockpit businesses={businesses} onRefresh={fetchBusinesses} />
                ) : (
                    <CampaignsView
                        businesses={businesses}
                        initialSelectedId={newlyOrchestratedId}
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
