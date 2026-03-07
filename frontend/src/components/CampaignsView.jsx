import { ExternalLink, CheckCircle2, Copy, ChevronLeft, Layout, Mail, FileText, Smartphone, Image as ImageIcon, Check, Loader2, PlayCircle } from 'lucide-react';
import AgentTracker from './AgentTracker';
import axios from 'axios';

function CampaignsView({ businesses, onDeploy, initialSelectedId }) {
    const campaigns = businesses.filter(b => b.status === 'processing' || b.status === 'pending_validation' || b.status === 'completed' || b.status === 'error');

    const [selectedCampaign, setSelectedCampaign] = useState(null);
    const [activeTab, setActiveTab] = useState('report');

    const fetchDetail = async (id) => {
        try {
            const response = await axios.get(`http://127.0.0.1:8000/businesses/${id}`);
            setSelectedCampaign(response.data);
        } catch (error) {
            console.error('Error fetching campaign detail:', error);
        }
    };

    const handleSelect = (camp) => {
        setSelectedCampaign(camp);
        fetchDetail(camp.id);
    };

    // Auto-select on mount or when initialSelectedId changes
    React.useEffect(() => {
        if (initialSelectedId) {
            const camp = campaigns.find(c => c.id === initialSelectedId);
            if (camp) {
                handleSelect(camp);
                if (camp.status === 'pending_validation') setActiveTab('validation');
            }
        }
    }, [initialSelectedId]);

    // Update selected campaign if the business object in the list updates (for live status/copy updates)
    React.useEffect(() => {
        if (selectedCampaign) {
            const updated = campaigns.find(c => c.id === selectedCampaign.id);
            if (updated && JSON.stringify(updated) !== JSON.stringify(selectedCampaign)) {
                setSelectedCampaign(updated);
            }
        }
    }, [businesses, selectedCampaign]);

    const tryParseJSON = (jsonString) => {
        try {
            const o = JSON.parse(jsonString);
            if (o && typeof o === "object") return o;
        } catch (e) { }
        return null;
    };

    if (selectedCampaign) {
        const data = tryParseJSON(selectedCampaign.generated_copy) || { email: selectedCampaign.generated_copy };

        // Clean up email content if it contains the orchestration summary line
        if (data.email && typeof data.email === 'string') {
            // New strategy: Extract between markers
            const markerRegex = /--- EMAIL CONTENT START ---([\s\S]*?)--- EMAIL CONTENT END ---/;
            const markerMatch = data.email.match(markerRegex);

            if (markerMatch && markerMatch[1]) {
                data.email = markerMatch[1].trim();
            } else {
                // Fallback: remove technical line
                const summaryRegex = /\[.*\] \| \[.*\] \| \[.*\] \| \[.*\] \| \[.*\]/g;
                data.email = data.email.replace(summaryRegex, '').trim();
            }
        }

        let vercelUrl = data.vercel_url || '';
        const vercelRegex = /https:\/\/[a-zA-Z0-9-]+\.vercel\.app/g;
        const matches = (selectedCampaign.generated_copy || '').match(vercelRegex);
        if (matches) vercelUrl = matches[matches.length - 1];
        if (!vercelUrl) vercelUrl = `https://${selectedCampaign.name.replace(/\s+/g, '-').toLowerCase()}-demo.vercel.app`;

        const isPending = selectedCampaign.status === 'pending_validation';

        // Extract and combine photos (AI generated + Google Maps)
        const allPhotos = [];

        // 1. Extract from ai_photos (using regex to find https:// links since agents might output text)
        if (data.ai_photos) {
            const urlRegex = /(https?:\/\/[^\s"',]+)/g;
            const matches = data.ai_photos.match(urlRegex);
            if (matches) {
                // Filter out non-image domains if necessary, but Fal.ai usually returns v3.fal.media or similar
                matches.forEach(url => {
                    const cleanUrl = url.replace(/\]|\)$/, ''); // remove trailing brackets if any
                    if (!allPhotos.includes(cleanUrl)) allPhotos.push(cleanUrl);
                });
            }
        }

        // 2. Add Google Maps photos
        if (data.photos && Array.isArray(data.photos)) {
            data.photos.forEach(photo => {
                if (typeof photo === 'string' && !allPhotos.includes(photo)) {
                    allPhotos.push(photo);
                }
            });
        }

        return (
            <div className="flex-1 h-full bg-slate-900 border-l border-white/5 overflow-y-auto custom-scrollbar p-8">
                <div className="max-w-6xl mx-auto h-full flex flex-col">
                    <div className="flex items-center space-x-4 mb-6">
                        <button onClick={() => setSelectedCampaign(null)} className="p-2 hover:bg-white/10 rounded-xl transition-colors">
                            <ChevronLeft className="w-6 h-6" />
                        </button>
                        <div>
                            <h2 className="text-2xl font-bold">{selectedCampaign.name}</h2>
                            <p className="text-sm text-slate-400">Score de Potentiel: <span className="text-emerald-400 font-bold">{selectedCampaign.potential_score}/10</span></p>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex items-center space-x-2 border-b border-white/10 mb-6 pb-2">
                        <button
                            onClick={() => setActiveTab('report')}
                            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'report' ? 'bg-brand text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                        >
                            <FileText className="w-4 h-4" />
                            <span>Analyse & Copywriting</span>
                        </button>
                        {isPending && (
                            <button
                                onClick={() => setActiveTab('validation')}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'validation' ? 'bg-brand text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                            >
                                <ImageIcon className="w-4 h-4" />
                                <span>Validation Photos</span>
                            </button>
                        )}
                        <button
                            onClick={() => setActiveTab('email')}
                            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'email' ? 'bg-brand text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                            disabled={isPending || selectedCampaign.status === 'processing'}
                        >
                            <Mail className="w-4 h-4" />
                            <span>Email de Prospection</span>
                        </button>
                        <button
                            onClick={() => setActiveTab('preview')}
                            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'preview' ? 'bg-brand text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                            disabled={isPending || selectedCampaign.status === 'processing'}
                        >
                            <Smartphone className="w-4 h-4" />
                            <span>Aperçu du Site</span>
                        </button>
                        {selectedCampaign.status === 'processing' && (
                            <button
                                onClick={() => setActiveTab('tracker')}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'tracker' ? 'bg-brand text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                            >
                                <PlayCircle className="w-4 h-4 animate-pulse text-amber-400" />
                                <span>Agent Cockpit</span>
                            </button>
                        )}
                    </div>

                    {/* Tab Content */}
                    <div className="flex-1 overflow-y-auto min-h-[500px]">
                        {activeTab === 'report' && (
                            <div className="glass p-6 rounded-2xl h-full overflow-y-auto custom-scrollbar">
                                <h3 className="text-lg font-bold mb-4">Rapport d'Investigation</h3>
                                <div className="space-y-6">
                                    <div>
                                        <h4 className="text-brand font-bold uppercase tracking-wider text-xs mb-2">Analyse Concurrentielle</h4>
                                        <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans bg-slate-900/50 p-4 rounded-xl border border-white/5">
                                            {data.report || 'Rapport non disponible en mode simulation.'}
                                        </pre>
                                    </div>
                                    <div>
                                        <h4 className="text-brand font-bold uppercase tracking-wider text-xs mb-2">Copywriting & Arguments</h4>
                                        <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans bg-slate-900/50 p-4 rounded-xl border border-white/5">
                                            {data.copywriting || 'Copywriting non disponible.'}
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        )}
                        {activeTab === 'validation' && (
                            <div className="glass p-6 rounded-2xl h-full flex flex-col items-center justify-center text-center">
                                <ImageIcon className="w-16 h-16 text-brand mb-4 opacity-50" />
                                <h3 className="text-xl font-bold mb-2">Validation des Photos</h3>
                                <p className="text-slate-400 mb-8 max-w-md">Sélectionnez la meilleure photo pour générer le site web. Cette photo sera utilisée en fond de la bannière principale.</p>

                                {/* Actual extracted photos from backend */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 w-full max-w-4xl max-h-[300px] overflow-y-auto custom-scrollbar p-2">
                                    {(allPhotos && allPhotos.length > 0) ? (
                                        allPhotos.map((photoUrl, i) => (
                                            <div
                                                key={i}
                                                onClick={() => {
                                                    document.querySelectorAll('.photo-choice').forEach(el => el.classList.remove('border-brand', 'ring-2', 'ring-brand'));
                                                    document.getElementById(`photo-${i}`).classList.add('border-brand', 'ring-2', 'ring-brand');
                                                }}
                                                id={`photo-${i}`}
                                                className="photo-choice h-32 bg-slate-800 rounded-xl border-2 border-transparent hover:border-brand/50 cursor-pointer overflow-hidden relative group transition-all"
                                            >
                                                <img src={photoUrl} alt={`Option ${i}`} className="w-full h-full object-cover" />
                                                <div className="absolute inset-0 bg-brand/30 opacity-0 group-focus-within:opacity-100 group-hover:opacity-50 flex items-center justify-center transition-opacity">
                                                    <Check className="text-white w-8 h-8 drop-shadow-lg" />
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="col-span-3 text-slate-500 italic p-6 bg-white/5 rounded-xl border border-white/10">
                                            Aucune photo disponible pour ce commerce.
                                        </div>
                                    )}
                                </div>

                                <button
                                    onClick={() => onDeploy && onDeploy(selectedCampaign.id)}
                                    disabled={selectedCampaign.status === 'processing' || selectedCampaign.status === 'completed'}
                                    className="bg-brand text-white px-8 py-3 rounded-xl font-bold hover:bg-brand-dark transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {selectedCampaign.status === 'processing' ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            <span>Déploiement en cours...</span>
                                        </>
                                    ) : selectedCampaign.status === 'completed' ? (
                                        <>
                                            <CheckCircle2 className="w-5 h-5" />
                                            <span>Déployé avec succès</span>
                                        </>
                                    ) : (
                                        <span>Valider & Déployer sur Vercel</span>
                                    )}
                                </button>
                            </div>
                        )}
                        {activeTab === 'email' && (
                            <div className="glass p-6 rounded-2xl h-full flex flex-col">
                                <h3 className="text-lg font-bold mb-4">Préparation de l'Email</h3>
                                <textarea
                                    className="flex-1 w-full bg-slate-900/50 text-white p-4 rounded-xl border border-white/10 custom-scrollbar resize-none focus:outline-none focus:border-brand"
                                    defaultValue={data.email || 'Texte de l\'email en cours de génération...'}
                                />
                                <div className="mt-4 flex justify-end">
                                    <button className="bg-brand text-white px-6 py-2 rounded-xl font-bold hover:bg-brand-dark transition-colors">
                                        Envoyer au Prospect via Gmail
                                    </button>
                                </div>
                            </div>
                        )}
                        {activeTab === 'preview' && (
                            <div className="glass p-2 rounded-2xl h-full flex flex-col relative w-full items-center justify-center bg-slate-900">
                                <div className="flex items-center justify-between w-full px-4 py-2 mb-2 bg-slate-800 rounded-t-xl">
                                    <span className="text-sm text-slate-400 truncate">{vercelUrl}</span>
                                    <button
                                        onClick={() => window.open(vercelUrl, '_blank')}
                                        className="text-brand hover:text-brand-dark flex flex-row items-center space-x-1 text-sm font-bold"
                                    >
                                        <span>Ouvrir dans un nouvel onglet</span>
                                        <ExternalLink className="w-4 h-4" />
                                    </button>
                                </div>
                                <iframe
                                    src={vercelUrl}
                                    className="w-full h-full rounded-b-xl border-none bg-white"
                                    title="Site Preview"
                                />
                            </div>
                        )}
                        {activeTab === 'tracker' && (
                            <div className="glass p-6 rounded-2xl h-full overflow-hidden">
                                <AgentTracker isProcessing={true} businessId={selectedCampaign.id} />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 h-full bg-slate-900 border-l border-white/5 overflow-y-auto custom-scrollbar p-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Vue d'ensemble des Campagnes</h2>
                        <p className="text-slate-400 mt-2">Suivez les sites OnePage générés et les performances d'orchestration.</p>
                    </div>
                    <div className="glass px-6 py-3 rounded-xl flex items-center space-x-4">
                        <div className="text-center">
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Actives</p>
                            <p className="text-xl font-bold text-amber-400">{campaigns.filter(c => c.status === 'processing').length}</p>
                        </div>
                        <div className="w-px h-8 bg-white/10"></div>
                        <div className="text-center">
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Déployées</p>
                            <p className="text-xl font-bold text-emerald-400">{campaigns.filter(c => c.status === 'completed').length}</p>
                        </div>
                    </div>
                </div>

                {campaigns.length === 0 ? (
                    <div className="glass p-12 rounded-2xl text-center flex flex-col items-center">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mb-4">
                            <ExternalLink className="w-8 h-8 text-slate-600" />
                        </div>
                        <h3 className="text-lg font-bold mb-2">Aucune campagne pour l'instant</h3>
                        <p className="text-slate-400 max-w-sm">Scannez une zone sur la carte et cliquez sur "Créer les Actifs Numériques" sur un commerce pour lancer une nouvelle campagne.</p>
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {campaigns.map((camp) => (
                            <div key={camp.id} onClick={() => handleSelect(camp)} className="glass p-6 rounded-2xl flex items-center justify-between group hover:bg-white/5 transition-colors border border-transparent hover:border-white/10 cursor-pointer">
                                <div className="flex items-center space-x-6">
                                    <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${camp.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : camp.status === 'pending_validation' ? 'bg-blue-500/20 text-blue-400' : 'bg-amber-500/20 text-amber-400'}`}>
                                        {camp.name.charAt(0)}
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-lg group-hover:text-brand transition-colors">{camp.name}</h3>
                                        <div className="flex items-center space-x-3 mt-1 text-sm text-slate-400">
                                            <span>Score : {camp.potential_score}/10</span>
                                            <span>•</span>
                                            <span className="capitalize text-white">
                                                Statut : {camp.status === 'processing' ? 'En cours' : camp.status === 'pending_validation' ? 'En attente de Validation' : camp.status === 'completed' ? 'Terminé' : camp.status}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center space-x-3">
                                    {camp.status === 'completed' || camp.status === 'pending_validation' ? (
                                        <button className="px-4 py-2 rounded-xl border border-white/10 bg-brand hover:bg-brand-dark transition-colors flex items-center space-x-2 text-sm font-bold text-white shadow-lg shadow-brand/20">
                                            <span>{camp.status === 'pending_validation' ? 'Continuer' : 'Gérer'}</span>
                                        </button>
                                    ) : null}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default CampaignsView;
