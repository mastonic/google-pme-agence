import React, { useState, useEffect } from 'react';
import { Bot, CheckCircle2, CircleDashed, Loader2 } from 'lucide-react';

const AGENTS = [
    { id: 'eclaireur', name: "L'Éclaireur", role: 'Extracteur de Données', duration: 4000 },
    { id: 'stratege', name: "Le Stratège", role: 'Rédacteur de Conversion', duration: 5000 },
    { id: 'designer', name: "Le Designer", role: 'Styliste UI/UX', duration: 4000 },
    { id: 'ingenieur', name: "L'Ingénieur", role: 'Développeur Fullstack', duration: 8000 },
    { id: 'closer', name: "Le Closer", role: 'Prospection Automatisée', duration: 3000 },
];

function AgentTracker({ isProcessing, businessId }) {
    const [currentStep, setCurrentStep] = useState(0);
    const [logs, setLogs] = useState([]);
    const [streaming, setStreaming] = useState(false);
    const logsEndRef = React.useRef(null);

    // Auto-scroll chat
    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    useEffect(() => {
        if (!isProcessing || !businessId) {
            setCurrentStep(0);
            setLogs([]);
            setStreaming(false);
            return;
        }

        setStreaming(true);
        setLogs([{ agent: "Système", message: "Initialisation du CrewAI et connexion au flux en direct...", type: "system" }]);

        const evtSource = new EventSource(`http://127.0.0.1:8000/stream/${businessId}`);

        evtSource.onmessage = function (event) {
            const data = JSON.parse(event.data);

            if (data.type === 'end') {
                setStreaming(false);
                setCurrentStep(AGENTS.length); // All done
                evtSource.close();
                return;
            }

            if (data.type === 'chat') {
                setLogs(prev => [...prev, data]);

                // Update current step based on the agent speaking
                const agentIndex = AGENTS.findIndex(a => a.name === data.agent);
                if (agentIndex !== -1 && agentIndex >= currentStep) {
                    setCurrentStep(agentIndex);
                }
            }
        };

        evtSource.onerror = function () {
            setStreaming(false);
            evtSource.close();
        };

        return () => {
            evtSource.close();
            setStreaming(false);
        };
    }, [isProcessing, businessId]);

    if (!isProcessing) return null;

    return (
        <div className="mt-4 border-t border-white/10 pt-4 flex flex-col h-[400px]">
            <h4 className="flex items-center text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                <Bot className="w-4 h-4 mr-2 text-brand" />
                Orchestration CrewAI - Live
            </h4>

            {/* Agent Progress Status */}
            <div className="flex space-x-2 mb-4 overflow-x-auto custom-scrollbar pb-2">
                {AGENTS.map((agent, index) => {
                    const status = index < currentStep ? 'completed' : index === currentStep ? 'processing' : 'pending';

                    return (
                        <div key={agent.id} className={`flex-shrink-0 flex items-center space-x-2 text-xs transition-opacity duration-500 bg-white/5 px-3 py-1.5 rounded-full border border-white/5 ${status === 'pending' ? 'opacity-40' : 'opacity-100'}`}>
                            <div>
                                {status === 'completed' && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                                {status === 'processing' && <Loader2 className="w-3 h-3 text-brand animate-spin" />}
                                {status === 'pending' && <CircleDashed className="w-3 h-3 text-slate-500" />}
                            </div>
                            <span className={`font-bold ${status === 'processing' ? 'text-white' : 'text-slate-300'}`}>
                                {agent.name}
                            </span>
                        </div>
                    );
                })}
            </div>

            {/* Live Chat Feed */}
            <div className="flex-1 bg-slate-950/50 rounded-xl border border-white/10 p-4 overflow-y-auto custom-scrollbar text-sm font-mono flex flex-col space-y-3">
                {logs.map((log, index) => (
                    <div key={index} className={`flex flex-col ${log.type === 'system' ? 'items-center text-slate-500 text-xs italic' : 'items-start'}`}>
                        {log.type === 'chat' && (
                            <span className="text-brand font-bold text-xs mb-1">{log.agent} :</span>
                        )}
                        <span className={`break-words whitespace-pre-wrap max-w-full ${log.type === 'system' ? '' : 'text-slate-300 bg-slate-900 border border-white/5 p-3 rounded-xl rounded-tl-none leading-relaxed'}`}>
                            {log.message}
                        </span>
                    </div>
                ))}

                {streaming && (
                    <div className="flex items-center space-x-2 text-slate-500 text-xs italic p-2">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>L'agent réfléchit...</span>
                    </div>
                )}
                <div ref={logsEndRef} />
            </div>
        </div>
    );
}

export default AgentTracker;
