import React, { useState, useEffect } from 'react';
import { Bot, CheckCircle2, CircleDashed, Loader2, Code2 } from 'lucide-react';

const AGENTS = [
    { id: 'eclaireur',      name: "L'Éclaireur",    role: 'Extracteur de Données' },
    { id: 'stratege',       name: "Le Stratège",     role: 'Rédacteur de Conversion' },
    { id: 'designer',       name: "Le Designer",     role: 'Directeur Artistique' },
    { id: 'ingenieur',      name: "L'Ingénieur",     role: 'Développeur Fullstack' },
    { id: 'closer',         name: "Le Closer",       role: 'Prospection Automatisée' },
];

function AgentTracker({ isProcessing, businessId }) {
    const [currentStep, setCurrentStep] = useState(0);
    const [logs, setLogs]               = useState([]);
    const [streaming, setStreaming]     = useState(false);
    const [htmlBuffer, setHtmlBuffer]   = useState('');
    const [isStreamingHtml, setIsStreamingHtml] = useState(false);
    const logsEndRef = React.useRef(null);

    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, htmlBuffer]);

    useEffect(() => {
        if (!isProcessing || !businessId) {
            setCurrentStep(0);
            setLogs([]);
            setStreaming(false);
            setHtmlBuffer('');
            setIsStreamingHtml(false);
            return;
        }

        setStreaming(true);
        setLogs([{ agent: "Système", message: "Connexion au flux CrewAI + Claude...", type: "system" }]);

        const evtSource = new EventSource(`/stream/${businessId}`);

        evtSource.onmessage = function (event) {
            const data = JSON.parse(event.data);

            if (data.type === 'end') {
                setStreaming(false);
                setIsStreamingHtml(false);
                setCurrentStep(AGENTS.length);
                evtSource.close();
                return;
            }

            if (data.type === 'stream_token' && data.agent === "L'Ingénieur") {
                setIsStreamingHtml(true);
                setHtmlBuffer(prev => prev + data.message);
                setCurrentStep(AGENTS.findIndex(a => a.id === 'ingenieur'));
                return;
            }

            if (data.type === 'chat') {
                // When Engineer sends a non-token chat message, HTML streaming is done
                if (data.agent === "L'Ingénieur") {
                    setIsStreamingHtml(false);
                }
                setLogs(prev => [...prev, data]);

                const agentIndex = AGENTS.findIndex(a => a.name === data.agent);
                if (agentIndex !== -1) setCurrentStep(agentIndex);
            }

            if (data.type === 'error') {
                setLogs(prev => [...prev, { agent: "Système", message: `❌ Erreur : ${data.message}`, type: "error" }]);
                setStreaming(false);
                evtSource.close();
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
        <div className="mt-4 border-t border-white/10 pt-4 flex flex-col" style={{ maxHeight: '520px' }}>
            <h4 className="flex items-center text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                <Bot className="w-4 h-4 mr-2 text-brand" />
                Orchestration Claude — Live
            </h4>

            {/* Agent progress pills */}
            <div className="flex space-x-2 mb-4 overflow-x-auto pb-2 custom-scrollbar flex-shrink-0">
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

            {/* HTML streaming panel — shows while Engineer generates */}
            {isStreamingHtml && (
                <div className="flex-shrink-0 mb-3 rounded-xl border border-green-500/30 bg-slate-950 overflow-hidden">
                    <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border-b border-green-500/20">
                        <Code2 className="w-3.5 h-3.5 text-green-400" />
                        <span className="text-xs font-bold text-green-400">L'Ingénieur génère le HTML en temps réel</span>
                        <Loader2 className="w-3 h-3 text-green-400 animate-spin ml-auto" />
                    </div>
                    <pre className="p-3 text-[10px] text-green-300 font-mono overflow-y-auto leading-relaxed"
                         style={{ maxHeight: '180px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                        {htmlBuffer.slice(-3000)}
                    </pre>
                </div>
            )}

            {/* Chat log */}
            <div className="flex-1 bg-slate-950/50 rounded-xl border border-white/10 p-3 overflow-y-auto custom-scrollbar text-sm font-mono flex flex-col space-y-2.5 min-h-0">
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
                            'text-slate-300 bg-slate-900 border border-white/5 p-2.5 rounded-xl rounded-tl-none'
                        }`}>
                            {log.message}
                        </span>
                    </div>
                ))}

                {streaming && !isStreamingHtml && (
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
