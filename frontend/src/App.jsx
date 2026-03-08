import React, { useState, useEffect } from 'react';
import MapComponent from './components/MapComponent';
import Sidebar from './components/Sidebar';
import AgentTracker from './components/AgentTracker';
import CampaignsView from './components/CampaignsView';
import axios from 'axios';
import { Loader2 } from 'lucide-react';

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8000'
    : `http://${window.location.hostname}:8000`;


function App() {
    const [businesses, setBusinesses] = useState([]);
    const [selectedId, setSelectedId] = useState(() => localStorage.getItem('lp_selected_id'));
    const [selectedBusiness, setSelectedBusiness] = useState(null);
    const [isScanning, setIsScanning] = useState(false);
    const [activeView, setActiveView] = useState(() => localStorage.getItem('lp_active_view') || 'market');
    const [newlyOrchestratedId, setNewlyOrchestratedId] = useState(null);

    useEffect(() => {
        fetchBusinesses();
    }, []);

    const fetchBusinesses = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/businesses`);
            console.log('Fetched businesses:', response.data.length, 'entries');
            if (response.data.length > 0) {
                console.log('Sample business:', response.data[0]);
            }
            setBusinesses(response.data);
        } catch (error) {
            console.error('Error fetching businesses:', error);
        }
    };

    // Restore selected business object when businesses list or selectedId changes
    useEffect(() => {
        if (selectedId && !selectedBusiness && businesses.length > 0) {
            const business = businesses.find(b => b.id === selectedId);
            if (business) setSelectedBusiness(business);
        }
    }, [businesses, selectedId]);

    // Save view to localStorage
    useEffect(() => {
        localStorage.setItem('lp_active_view', activeView);
    }, [activeView]);

    const [isLoadingDetail, setIsLoadingDetail] = useState(false);

    // Handle selection changes
    const handleSelectBusiness = async (business) => {
        if (business) {
            setSelectedId(business.id);
            localStorage.setItem('lp_selected_id', business.id);

            // Set basic info immediately
            setSelectedBusiness(business);
            setIsLoadingDetail(true);

            // Fetch full details (including generated_copy) in background to speed up UI
            try {
                const response = await axios.get(`${API_BASE_URL}/businesses/${business.id}`);
                // Update selected business with full details
                setSelectedBusiness(response.data);

                // Also update this entry in the main list (so we don't re-fetch if selected again)
                setBusinesses(prev => prev.map(b => b.id === business.id ? response.data : b));
            } catch (error) {
                console.error('Error loading business details:', error);
            } finally {
                setIsLoadingDetail(false);
            }
        } else {
            setSelectedBusiness(null);
            setSelectedId(null);
            localStorage.removeItem('lp_selected_id');
        }
    };

    const handleScan = async (lat, lng) => {
        setIsScanning(true);
        try {
            await axios.post(`${API_BASE_URL}/scan?lat=${lat}&lng=${lng}&radius=1000`);
            fetchBusinesses();
        } catch (error) {
        } finally {
            setIsScanning(false);
        }
    };

    const handleOrchestrate = async (businessId) => {
        try {
            // Optimistic update
            setBusinesses(prev => prev.map(b => b.id === businessId ? { ...b, status: 'processing' } : b));
            if (selectedBusiness && selectedBusiness.id === businessId) {
                setSelectedBusiness(prev => ({ ...prev, status: 'processing' }));
            }

            // Trigger backend orchestration
            axios.post(`${API_BASE_URL}/orchestrate/${businessId}`);

            // Redirect to Campaigns view and select this business
            setNewlyOrchestratedId(businessId);
            setActiveView('campaigns');

            // Fetch updates (optional but good for consistency)
            setTimeout(fetchBusinesses, 500);
        } catch (error) {
            console.error('Error orchestrating business:', error);
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
            />

            <main className="flex-1 relative">
                {activeView === 'market' ? (
                    <>
                        <MapComponent
                            businesses={businesses}
                            onScan={handleScan}
                            isScanning={isScanning}
                            onSelectBusiness={handleSelectBusiness}
                        />

                        {/* Header Overlay & KPIs */}
                        <div className="absolute top-6 left-6 z-[1000] flex flex-col space-y-4">
                            <div className="glass p-4 rounded-xl flex items-center space-x-3 w-fit">
                                <div className="w-10 h-10 bg-brand rounded-lg flex items-center justify-center shadow-lg shadow-brand/20">
                                    <span className="text-xl font-bold italic">LP</span>
                                </div>
                                <div>
                                    <h1 className="text-xl font-bold tracking-tight">Local-Pulse</h1>
                                    <p className="text-xs text-slate-400">Intelligence Commerciale & Auto-Ops</p>
                                </div>
                            </div>

                            <div className="glass p-4 rounded-xl flex space-x-6 w-fit">
                                <div>
                                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Total Scanné</p>
                                    <p className="text-2xl font-bold">{businesses.length}</p>
                                </div>
                                <div className="w-px bg-white/10"></div>
                                <div>
                                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Haut Potentiel</p>
                                    <p className="text-2xl font-bold text-emerald-400">
                                        {businesses.filter(b => b.potential_score >= 8).length}
                                    </p>
                                </div>
                                <div className="w-px bg-white/10"></div>
                                <div>
                                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">En Pipeline</p>
                                    <p className="text-2xl font-bold text-amber-400">
                                        {businesses.filter(b => b.status === 'processing' || b.status === 'completed').length}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Score Legend Overlay */}
                        <div className="absolute bottom-6 left-6 z-[1000] glass p-4 rounded-xl">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Légende du Score</h4>
                            <div className="space-y-2 text-sm">
                                <div className="flex items-center space-x-3">
                                    <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
                                    <span className="font-medium">8-10 : Lead Chaud</span>
                                    <span className="text-xs text-slate-500">(Pas de site, mauvais avis)</span>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <div className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]"></div>
                                    <span className="font-medium">6-7 : Lead Tiède</span>
                                    <span className="text-xs text-slate-500">(Besoin d'optimisation)</span>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <div className="w-3 h-3 rounded-full bg-slate-500"></div>
                                    <span className="font-medium">0-5 : Froid</span>
                                    <span className="text-xs text-slate-500">(Forte présence numérique)</span>
                                </div>
                            </div>
                        </div>

                        {/* Selected Business Info Overlay */}
                        {selectedBusiness && (
                            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[1000] w-full max-w-md">
                                <div className="glass p-6 rounded-2xl mx-4 shadow-2xl">
                                    <div className="flex justify-between items-start mb-4 relative min-h-[100px]">
                                        {isLoadingDetail && (
                                            <div className="absolute inset-0 z-10 bg-slate-900/40 backdrop-blur-[2px] flex items-center justify-center rounded-xl">
                                                <Loader2 className="w-8 h-8 animate-spin text-brand" />
                                            </div>
                                        )}
                                        <div className="pr-4">
                                            <h3 className="text-xl font-bold">{selectedBusiness.name}</h3>
                                            <p className="text-sm text-slate-400 mt-1">{selectedBusiness.address}</p>
                                            <div className="flex items-center space-x-4 mt-2">
                                                {selectedBusiness.rating > 0 && (
                                                    <div className="flex items-center text-amber-400 text-sm font-medium">
                                                        <span className="mr-1">★</span>
                                                        {selectedBusiness.rating} ({selectedBusiness.user_ratings_total || 0} reviews)
                                                    </div>
                                                )}
                                                <div className="text-sm text-slate-400">
                                                    Statut: <span className="capitalize text-white font-medium">{
                                                        selectedBusiness.status === 'processing' ? 'En cours' :
                                                            selectedBusiness.status === 'completed' ? 'Terminé' : 'Scanné'}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className={`px-3 py-1 rounded-full border text-xs font-bold whitespace-nowrap shadow-sm ${selectedBusiness.potential_score >= 8 ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                                            selectedBusiness.potential_score >= 6 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                                                'bg-slate-500/20 text-slate-400 border-slate-500/30'
                                            }`}>
                                            Score: {selectedBusiness.potential_score}/10
                                        </div>
                                    </div>
                                    <div className="flex space-x-3">
                                        <button
                                            onClick={() => handleOrchestrate(selectedBusiness.id)}
                                            disabled={selectedBusiness.status === 'processing'}
                                            className="flex-1 bg-brand hover:bg-brand-dark transition-colors text-white font-bold py-3 rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-brand/30 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {selectedBusiness.status === 'processing' ? (
                                                <>
                                                    <Loader2 className="w-5 h-5 animate-spin" />
                                                    <span>Création en cours...</span>
                                                </>
                                            ) : (
                                                <span>Créer les Actifs Numériques</span>
                                            )}
                                        </button>
                                        <button
                                            onClick={() => handleSelectBusiness(null)}
                                            className="px-4 py-3 rounded-xl border border-white/10 hover:bg-white/5 transition-colors"
                                        >
                                            Fermer
                                        </button>
                                    </div>

                                    {selectedBusiness.status === 'processing' && (
                                        <div className="mt-4"><AgentTracker isProcessing={true} businessId={selectedBusiness.id} /></div>
                                    )}
                                </div>
                            </div>
                        )}
                    </>
                ) : (
                    <CampaignsView
                        businesses={businesses}
                        initialSelectedId={newlyOrchestratedId}
                        onDeploy={async (id) => {
                            try {
                                setBusinesses(prev => prev.map(b => b.id === id ? { ...b, status: 'processing' } : b));
                                await axios.post(`${API_BASE_URL}/deploy/${id}`);
                                fetchBusinesses();
                            } catch (error) {
                                console.error('Error deploying business:', error);
                                fetchBusinesses();
                            }
                        }}
                    />
                )}
            </main>
        </div>
    );
}

export default App;
