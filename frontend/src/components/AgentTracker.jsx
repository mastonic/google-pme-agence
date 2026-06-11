import React, { useState, useEffect, useRef } from 'react';
import { Bot, CheckCircle2, CircleDashed, Loader2, Code2 } from 'lucide-react';
import axios from 'axios';

const AGENTS = [
    { id: 'designer',  name: "Le Designer",    role: 'Directeur Artistique' },
    { id: 'eclaireur', name: "L'Éclaireur",     role: 'Extracteur de Données' },
    { id: 'stratege',  name: "Le Stratège",     role: 'Rédacteur de Conversion' },
    { id: 'artist',    name: "Visions Artist",  role: 'Photographe IA' },
    { id: 'ingenieur', name: "L'Ingénieur",     role: 'Développeur Fullstack' },
    { id: 'closer',    name: "Le Closer",       role: 'Prospection Automatisée' },
];

const AGENT_NAME_TO_INDEX = Object.fromEntries(AGENTS.map((a, i) => [a.name, i]));

function AgentTracker({ isProcessing, businessId }) {
    const [currentStep, setCurrentStep] = useState(0);
    const [logs, setLogs]               = useState([]);
    const [isFinished, setIsFinished]   = useState(false);
    const sinceRef    = useRef(0);
    const logsEndRef  = useRef(null);
    const intervalRef = useRef(null);

    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    useEffect(() => {
        if (!isProcessing || !businessId) {
            setCurrentStep(0);
            setLogs([]);
            setIsFinished(false);
            sinceRef.current = 0;
            if (intervalRef.current) clearInterval(intervalRef.current);
            return;
        }

        sinceRef.current = 0;
        setLogs([{ agent: 'Système', message: 'Connexion aux agents IA...', type: 'system' }]);
        setIsFinished(false);

        const poll = async () => {
            try {
                const r = await axios.get(`/businesses/${businessId}/logs?since=${sinceRef.current}`);
                const { logs: newLogs, total, finished } = r.data;

                if (newLogs.length > 0) {
                    sinceRef.current = total;
                    setLogs(prev => {
                        // Replace the initial "Connexion..." message once real logs arrive
                        const base = prev.length === 1 && prev[0].message === 'Connexion aux agents IA...' ? [] : prev;
                        return [...base, ...newLogs.filter(l => l.type !== 'stream_token')];
                    });

                    // Update current agent step
                    const lastChatLog = [...newLogs].reverse().find(l => l.type === 'chat');
                    if (lastChatLog) {
                        const idx = AGENT_NAME_TO_INDEX[lastChatLog.agent];
                        if (idx !== undefined) setCurrentStep(idx);
                    }
                }

                if (finished) {
                    setIsFinished(true);
                    setCurrentStep(AGENTS.length);
                    clearInterval(intervalRef.current);
                }
            } catch {
                // Network blip — keep polling
            }
        };

        poll(); // immediate first poll
        intervalRef.current = setInterval(poll, 2500);

        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [isProcessing, businessId]);

    if (!isProcessing) return null;

    return (
        <div className="mt-4 border-t border-white/10 pt-4 flex flex-col" style={{ maxHeight: '520px' }}>
            <h4 className="flex items-center text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                <Bot className="w-4 h-4 mr-2 text-brand" />
                Orchestration Claude — Live
            </h4>

            {/* Agent progress pills */}
            <div className="flex space-x-2 mb-4 overflow-x-auto pb-2 flex-shrink-0"
                 style={{ scrollbarWidth: 'thin' }}>
                {AGENTS.map((agent, index) => {
                    const status = index < currentStep ? 'completed' : index === currentStep ? 'processing' : 'pending';
                    return (
                        <div key={agent.id} className={`flex-shrink-0 flex items-center space-x-2 text-xs px-3 py-1.5 rounded-full border transition-all ${
                            status === 'completed' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                            status === 'processing' ? 'bg-brand/15 border-brand/40 text-white' :
                            'bg-white/5 border-white/5 text-slate-500 opacity-40'
                        }`}>
                            {status === 'completed' && <CheckCircle2 className="w-3 h-3" />}
                            {status === 'processing' && <Loader2 className="w-3 h-3 animate-spin text-brand" />}
                            {status === 'pending'    && <CircleDashed className="w-3 h-3" />}
                            <span className="font-bold">{agent.name}</span>
                        </div>
                    );
                })}
            </div>

            {/* Chat log */}
            <div className="flex-1 bg-slate-950/50 rounded-xl border border-white/10 p-3 overflow-y-auto text-sm font-mono flex flex-col space-y-2.5 min-h-0"
                 style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,.1) transparent' }}>
                {logs.map((log, index) => (
                    <div key={index} className={`flex flex-col ${
                        log.type === 'system' || log.type === 'error'
                            ? 'items-center text-xs italic'
                            : 'items-start'
                    }`}>
                        {log.type === 'chat' && (
                            <span className="text-brand font-bold text-[10px] mb-1">{log.agent} :</span>
                        )}
                        <span className={`break-words whitespace-pre-wrap max-w-full text-xs leading-relaxed ${
                            log.type === 'system'  ? 'text-slate-500' :
                            log.type === 'error'   ? 'text-rose-400' :
                            log.type === 'end'     ? 'text-emerald-400 font-bold' :
                            'text-slate-300 bg-slate-900 border border-white/5 p-2.5 rounded-xl rounded-tl-none'
                        }`}>
                            {log.message}
                        </span>
                    </div>
                ))}

                {!isFinished && (
                    <div className="flex items-center space-x-2 text-slate-500 text-xs italic p-2">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>Agent en cours... (mise à jour toutes les 2.5s)</span>
                    </div>
                )}
                <div ref={logsEndRef} />
            </div>
        </div>
    );
}

export default AgentTracker;
