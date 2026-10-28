import { useState, useEffect, useRef } from "react";
import {
  Wand2, Eye, Rocket, RefreshCw, CheckCircle2, Loader2,
  Globe, Palette, Code2, Mail, ChevronRight, Sparkles,
  Monitor, Smartphone, ExternalLink, Copy, Check, X,
  Building2, MapPin, Star, Clock, Phone, AlertCircle
} from "lucide-react";

// ─────────────────────────────────────────────
// DONNÉES MOCK (remplace par props réels)
// ─────────────────────────────────────────────
const MOCK_BUSINESS = {
  id: "biz_001",
  name: "Boulangerie Dupont",
  category: "Boulangerie / Pâtisserie",
  address: "12 Rue de la Paix, Fort-de-France, Martinique",
  phone: "+596 596 12 34 56",
  rating: 4.7,
  reviews_count: 134,
  hours: "Lun–Sam 6h–19h, Dim 6h–13h",
  photos: [
    "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800",
    "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=800",
  ],
  description: "Boulangerie artisanale depuis 1987, spécialiste du pain au levain et des pâtisseries créoles.",
  digital_gap_score: 87,
};

// ─────────────────────────────────────────────
// ÉTAPES DES AGENTS
// ─────────────────────────────────────────────
const AGENT_STEPS = [
  { id: "scout",    icon: MapPin,    label: "Éclaireur",   role: "Analyse Google Maps & données locales" },
  { id: "designer", icon: Palette,   label: "Designer",    role: "Identité visuelle & choix de template" },
  { id: "writer",   icon: Sparkles,  label: "Copywriter",  role: "Storytelling & contenu persuasif" },
  { id: "dev",      icon: Code2,     label: "Ingénieur",   role: "Génération HTML/Tailwind via Claude" },
  { id: "closer",   icon: Mail,      label: "Closer",      role: "Email de prospection personnalisé" },
];

// ─────────────────────────────────────────────
// PROMPT CLAUDE POUR GÉNÉRATION DE SITE
// ─────────────────────────────────────────────
function buildSitePrompt(business, designPlan) {
  return `Tu es un développeur web expert spécialisé dans les sites pour commerces locaux.

Génère un site OnePage HTML complet et moderne pour ce commerce :

NOM : ${business.name}
SECTEUR : ${business.category}
ADRESSE : ${business.address}
TÉLÉPHONE : ${business.phone}
AVIS : ${business.rating}/5 (${business.reviews_count} avis)
HORAIRES : ${business.hours}
DESCRIPTION : ${business.description}
PHOTOS : ${business.photos.join(", ")}

PLAN DESIGN CHOISI :
${designPlan}

RÈGLES ABSOLUES :
- HTML complet et autonome (<!DOCTYPE html> ... </html>)
- Tailwind CSS via CDN (https://cdn.tailwindcss.com)
- Google Fonts via CDN
- Design PREMIUM et UNIQUE, pas générique
- Sections obligatoires : Hero, Services/Produits, Avis clients, Horaires+Contact, Footer
- Bouton WhatsApp flottant (lien wa.me/${business.phone?.replace(/\D/g, "")})
- Google Maps embed pour l'adresse
- Responsive mobile-first
- Animations CSS subtiles (pas de lib externe)
- Palette et typo cohérentes avec le secteur

Réponds UNIQUEMENT avec le code HTML, sans balises markdown, sans explication.`;
}

// ─────────────────────────────────────────────
// PROMPT CLAUDE POUR LE PLAN DESIGN
// ─────────────────────────────────────────────
function buildDesignPrompt(business) {
  return `Tu es un designer UI/UX expert. Pour ce commerce :

NOM : ${business.name}
SECTEUR : ${business.category}
NOTE : ${business.rating}/5

Génère un plan design UNIQUE en JSON strict (pas de markdown) :
{
  "template": "bento|minimal|split|editorial",
  "palette": { "primary": "#hex", "secondary": "#hex", "accent": "#hex", "bg": "#hex", "text": "#hex" },
  "fonts": { "display": "Nom Google Font", "body": "Nom Google Font" },
  "hero_concept": "Description en 1 phrase du hero",
  "signature": "L'élément unique mémorable de ce site",
  "mood": "Mot qui résume l'ambiance"
}

Sois SPÉCIFIQUE au secteur. Pas de choix génériques.`;
}

// ─────────────────────────────────────────────
// COMPOSANT PRINCIPAL
// ─────────────────────────────────────────────
export default function SiteGeneratorV2({ business = MOCK_BUSINESS }) {
  const [phase, setPhase] = useState("idle"); // idle | planning | generating | preview | deploying | done
  const [currentStep, setCurrentStep] = useState(-1);
  const [agentLogs, setAgentLogs] = useState([]);
  const [designPlan, setDesignPlan] = useState(null);
  const [generatedHTML, setGeneratedHTML] = useState("");
  const [streamedHTML, setStreamedHTML] = useState("");
  const [previewMode, setPreviewMode] = useState("desktop");
  const [deployedUrl, setDeployedUrl] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const logsEndRef = useRef(null);
  const streamRef = useRef("");

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [agentLogs]);

  const addLog = (agent, message, type = "info") => {
    setAgentLogs(prev => [...prev, { agent, message, type, ts: Date.now() }]);
  };

  // ── APPEL CLAUDE API ──
  async function callClaude(prompt, systemPrompt = "", onStream = null) {
    const messages = [{ role: "user", content: prompt }];
    const body = {
      model: "claude-sonnet-4-20250514",
      max_tokens: 8000,
      system: systemPrompt || "Tu es un expert en création de sites web pour PME locales.",
      messages,
      stream: !!onStream,
    };

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) throw new Error(`API Error: ${response.status}`);

    if (onStream) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let full = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "content_block_delta" && data.delta?.text) {
                full += data.delta.text;
                onStream(full);
              }
            } catch {}
          }
        }
      }
      return full;
    } else {
      const data = await response.json();
      return data.content?.[0]?.text || "";
    }
  }

  // ── PIPELINE PRINCIPAL ──
  async function startGeneration() {
    setPhase("planning");
    setCurrentStep(0);
    setAgentLogs([]);
    setDesignPlan(null);
    setGeneratedHTML("");
    setStreamedHTML("");
    setError("");
    streamRef.current = "";

    try {
      // ── ÉTAPE 0 : Scout ──
      addLog("Éclaireur", `Analyse de "${business.name}" (${business.category})…`, "system");
      addLog("Éclaireur", `Score Digital Gap : ${business.digital_gap_score}/100 — opportunité forte`, "success");
      addLog("Éclaireur", `${business.reviews_count} avis Google (${business.rating}★) récupérés`, "info");
      await delay(1200);

      // ── ÉTAPE 1 : Designer ──
      setCurrentStep(1);
      addLog("Designer", "Analyse du secteur et définition de l'identité visuelle…", "system");

      const designRaw = await callClaude(buildDesignPrompt(business));
      let plan;
      try {
        const clean = designRaw.replace(/```json|```/g, "").trim();
        plan = JSON.parse(clean);
        setDesignPlan(plan);
        addLog("Designer", `Template choisi : ${plan.template?.toUpperCase()} — Mood : "${plan.mood}"`, "success");
        addLog("Designer", `Palette : ${plan.palette?.primary} / ${plan.palette?.accent}`, "info");
        addLog("Designer", `Typo : ${plan.fonts?.display} + ${plan.fonts?.body}`, "info");
        addLog("Designer", `Signature : ${plan.signature}`, "highlight");
      } catch {
        plan = { template: "minimal", mood: "élégant", signature: "Design épuré premium" };
        setDesignPlan(plan);
        addLog("Designer", "Plan design généré (mode simplifié)", "info");
      }
      await delay(800);

      // ── ÉTAPE 2 : Copywriter ──
      setCurrentStep(2);
      addLog("Copywriter", "Rédaction du storytelling et des accroches…", "system");
      addLog("Copywriter", `Hero concept : "${plan.hero_concept || "Authenticité locale mise en scène"}"`, "info");
      addLog("Copywriter", "Sections : Hero, Services, Avis clients, Contact — ✓", "success");
      await delay(1000);

      // ── ÉTAPE 3 : Ingénieur (génération HTML en streaming) ──
      setCurrentStep(3);
      setPhase("generating");
      addLog("Ingénieur", "Génération du site HTML/Tailwind via Claude Sonnet…", "system");

      const planText = plan
        ? `Template: ${plan.template}, Couleurs: primary=${plan.palette?.primary}, accent=${plan.palette?.accent}, Fonts: ${plan.fonts?.display}/${plan.fonts?.body}, Signature: ${plan.signature}`
        : "Template minimal premium";

      const html = await callClaude(
        buildSitePrompt(business, planText),
        "Tu génères uniquement du code HTML complet et autonome. Jamais de markdown. Jamais d'explication.",
        (streamed) => {
          streamRef.current = streamed;
          setStreamedHTML(streamed);
        }
      );

      const finalHTML = html.replace(/```html|```/g, "").trim();
      setGeneratedHTML(finalHTML);
      setStreamedHTML(finalHTML);
      addLog("Ingénieur", `Site généré — ${(finalHTML.length / 1024).toFixed(1)} KB de code propre`, "success");
      await delay(500);

      // ── ÉTAPE 4 : Closer ──
      setCurrentStep(4);
      addLog("Closer", `Email de prospection rédigé pour ${business.name}`, "system");
      addLog("Closer", "Brouillon Gmail créé — prêt à envoyer", "success");
      await delay(800);

      setPhase("preview");
      addLog("Système", "✓ Pipeline terminé — Vérifiez le preview avant déploiement", "system");

    } catch (err) {
      setError(err.message);
      setPhase("idle");
      addLog("Système", `Erreur : ${err.message}`, "error");
    }
  }

  // ── DÉPLOIEMENT VERCEL (simulé ici) ──
  async function deployToVercel() {
    setPhase("deploying");
    addLog("Système", "Déploiement sur Vercel en cours…", "system");
    await delay(2000);
    const slug = business.name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
    const url = `https://${slug}-${Math.random().toString(36).slice(2, 7)}.vercel.app`;
    setDeployedUrl(url);
    setPhase("done");
    addLog("Système", `✓ Site en ligne : ${url}`, "success");
  }

  const copyHTML = () => {
    navigator.clipboard.writeText(generatedHTML);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const progressPct = currentStep < 0 ? 0 : Math.round(((currentStep + 1) / AGENT_STEPS.length) * 100);

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans" style={{ fontFamily: "'Inter', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        .log-info    { color: #94a3b8; }
        .log-success { color: #34d399; }
        .log-error   { color: #f87171; }
        .log-system  { color: #a78bfa; }
        .log-highlight { color: #fbbf24; font-weight: 600; }
        .agent-active { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); }
        .agent-done   { background: #065f46; }
        .agent-idle   { background: #1e293b; }
        .glass { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); backdrop-filter: blur(12px); }
        .pulse-ring { animation: pulse-ring 2s ease-out infinite; }
        @keyframes pulse-ring { 0% { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); } 100% { box-shadow: 0 0 0 20px rgba(99,102,241,0); } }
        .stream-cursor::after { content: '▌'; animation: blink 0.8s step-end infinite; }
        @keyframes blink { 50% { opacity: 0; } }
        .preview-desktop { width: 100%; }
        .preview-mobile  { width: 375px; margin: 0 auto; }
        ::-webkit-scrollbar { width: 4px; } 
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
      `}</style>

      {/* ── HEADER ── */}
      <header className="border-b border-white/5 px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <Wand2 size={16} />
          </div>
          <div>
            <div className="font-semibold text-sm">Local Pulse — Générateur IA v2</div>
            <div className="text-xs text-slate-500">Propulsé par Claude Sonnet</div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Building2 size={14} />
          <span className="font-medium text-white">{business.name}</span>
          <span className="text-slate-600">·</span>
          <span>{business.category}</span>
          <span className="ml-2 px-2 py-0.5 rounded-full bg-emerald-900/40 text-emerald-400 border border-emerald-800/50">
            Gap {business.digital_gap_score}/100
          </span>
        </div>
      </header>

      <div className="flex h-[calc(100vh-65px)]">

        {/* ── PANNEAU GAUCHE : AGENTS + LOGS ── */}
        <div className="w-80 border-r border-white/5 flex flex-col">

          {/* Agents timeline */}
          <div className="p-5 border-b border-white/5">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">Pipeline d'agents</div>
            <div className="space-y-2">
              {AGENT_STEPS.map((step, i) => {
                const Icon = step.icon;
                const isDone = currentStep > i;
                const isActive = currentStep === i && (phase === "planning" || phase === "generating");
                return (
                  <div key={step.id}
                    className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-500 ${
                      isActive ? "agent-active" :
                      isDone   ? "agent-done" :
                                 "agent-idle"
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      isActive ? "bg-white/20" : isDone ? "bg-emerald-700/50" : "bg-slate-800"
                    }`}>
                      {isDone
                        ? <CheckCircle2 size={16} className="text-emerald-300" />
                        : isActive
                          ? <Loader2 size={16} className="animate-spin" />
                          : <Icon size={16} className="text-slate-500" />
                      }
                    </div>
                    <div className="min-w-0">
                      <div className={`text-xs font-semibold ${isActive || isDone ? "text-white" : "text-slate-500"}`}>
                        {step.label}
                      </div>
                      <div className={`text-xs truncate ${isActive ? "text-white/70" : isDone ? "text-emerald-400/70" : "text-slate-600"}`}>
                        {step.role}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Progress bar */}
            {phase !== "idle" && (
              <div className="mt-4">
                <div className="flex justify-between text-xs text-slate-500 mb-1">
                  <span>Progression</span><span>{progressPct}%</span>
                </div>
                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-700"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Logs */}
          <div className="flex-1 overflow-y-auto p-4 space-y-1.5">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">Journal en direct</div>
            {agentLogs.length === 0 && (
              <div className="text-xs text-slate-600 italic">En attente du lancement…</div>
            )}
            {agentLogs.map((log, i) => (
              <div key={i} className="text-xs font-mono">
                <span className="text-slate-600">[{log.agent}]</span>{" "}
                <span className={`log-${log.type}`}>{log.message}</span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>

          {/* Design plan badge */}
          {designPlan && (
            <div className="p-4 border-t border-white/5">
              <div className="glass rounded-xl p-3 space-y-1.5">
                <div className="text-xs font-semibold text-indigo-400">Plan design validé</div>
                <div className="flex gap-2">
                  {Object.entries(designPlan.palette || {}).slice(0, 5).map(([k, v]) => (
                    <div key={k} className="w-5 h-5 rounded-full border border-white/10 flex-shrink-0"
                      style={{ background: v }} title={`${k}: ${v}`} />
                  ))}
                </div>
                <div className="text-xs text-slate-400 truncate">{designPlan.signature}</div>
              </div>
            </div>
          )}
        </div>

        {/* ── ZONE CENTRALE ── */}
        <div className="flex-1 flex flex-col overflow-hidden">

          {/* ── IDLE : CTA de lancement ── */}
          {phase === "idle" && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-md">
                <div className="w-20 h-20 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center mx-auto mb-6 pulse-ring">
                  <Wand2 size={36} className="text-indigo-400" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Générer le site</h2>
                <p className="text-slate-400 text-sm mb-8 leading-relaxed">
                  Claude Sonnet va analyser <strong className="text-white">{business.name}</strong>, concevoir
                  une identité visuelle unique, générer un site HTML complet et le préparer
                  au déploiement Vercel — le tout en moins de 60 secondes.
                </p>

                {/* Business card */}
                <div className="glass rounded-2xl p-4 mb-8 text-left space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Star size={14} className="text-amber-400 fill-amber-400" />
                    <span className="text-white font-medium">{business.rating}</span>
                    <span className="text-slate-500">({business.reviews_count} avis)</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <MapPin size={12} /><span>{business.address}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <Clock size={12} /><span>{business.hours}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <Phone size={12} /><span>{business.phone}</span>
                  </div>
                </div>

                {error && (
                  <div className="flex items-center gap-2 text-sm text-rose-400 bg-rose-900/20 border border-rose-800/30 rounded-xl p-3 mb-4">
                    <AlertCircle size={16} />{error}
                  </div>
                )}

                <button onClick={startGeneration}
                  className="w-full py-4 px-8 bg-indigo-600 hover:bg-indigo-500 rounded-2xl font-semibold text-lg transition-all hover:scale-[1.02] active:scale-95 flex items-center justify-center gap-3">
                  <Sparkles size={20} />
                  Lancer le pipeline Claude
                  <ChevronRight size={20} />
                </button>
              </div>
            </div>
          )}

          {/* ── PLANNING / GENERATING : Streaming du code ── */}
          {(phase === "planning" || phase === "generating") && (
            <div className="flex-1 flex flex-col">
              <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
                <Loader2 size={16} className="animate-spin text-indigo-400" />
                <span className="text-sm font-medium">
                  {phase === "planning" ? "Analyse et conception…" : "Génération du site en streaming…"}
                </span>
                {phase === "generating" && streamedHTML && (
                  <span className="ml-auto text-xs text-slate-500">
                    {(streamedHTML.length / 1024).toFixed(1)} KB générés
                  </span>
                )}
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                {streamedHTML ? (
                  <pre className={`text-xs font-mono text-emerald-400/80 whitespace-pre-wrap leading-relaxed ${phase === "generating" ? "stream-cursor" : ""}`}>
                    {streamedHTML.slice(0, 4000)}{streamedHTML.length > 4000 ? "\n…(suite en cours)" : ""}
                  </pre>
                ) : (
                  <div className="flex flex-col gap-3 animate-pulse">
                    {[...Array(12)].map((_, i) => (
                      <div key={i} className="h-3 bg-slate-800 rounded" style={{ width: `${40 + Math.random() * 55}%` }} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── PREVIEW ── */}
          {(phase === "preview" || phase === "deploying" || phase === "done") && generatedHTML && (
            <div className="flex-1 flex flex-col overflow-hidden">

              {/* Toolbar preview */}
              <div className="flex items-center gap-3 px-6 py-3 border-b border-white/5 bg-slate-900/50">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-rose-500/70" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/70" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/70" />
                </div>

                {/* URL bar fake */}
                <div className="flex-1 mx-4 bg-slate-800 rounded-lg px-3 py-1.5 flex items-center gap-2">
                  <Globe size={12} className="text-slate-500" />
                  <span className="text-xs text-slate-400 font-mono">
                    {deployedUrl || `preview — ${business.name}`}
                  </span>
                  {deployedUrl && (
                    <a href={deployedUrl} target="_blank" rel="noreferrer"
                      className="ml-auto text-indigo-400 hover:text-indigo-300">
                      <ExternalLink size={12} />
                    </a>
                  )}
                </div>

                {/* Switcher desktop/mobile */}
                <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
                  <button onClick={() => setPreviewMode("desktop")}
                    className={`px-2 py-1 rounded-md transition-all ${previewMode === "desktop" ? "bg-slate-600 text-white" : "text-slate-500 hover:text-white"}`}>
                    <Monitor size={14} />
                  </button>
                  <button onClick={() => setPreviewMode("mobile")}
                    className={`px-2 py-1 rounded-md transition-all ${previewMode === "mobile" ? "bg-slate-600 text-white" : "text-slate-500 hover:text-white"}`}>
                    <Smartphone size={14} />
                  </button>
                </div>

                {/* Actions */}
                <button onClick={copyHTML}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg transition-all">
                  {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                  {copied ? "Copié !" : "HTML"}
                </button>

                <button onClick={startGeneration}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg transition-all">
                  <RefreshCw size={12} />
                  Regénérer
                </button>
              </div>

              {/* iFrame preview */}
              <div className="flex-1 overflow-auto bg-slate-900 p-4">
                <div className={`transition-all duration-500 ${previewMode === "mobile" ? "preview-mobile" : "preview-desktop"}`}>
                  {previewMode === "mobile" && (
                    <div className="border-4 border-slate-700 rounded-[2rem] overflow-hidden shadow-2xl">
                      <iframe
                        srcDoc={generatedHTML}
                        className="w-full h-[700px]"
                        title="preview-mobile"
                        sandbox="allow-scripts"
                      />
                    </div>
                  )}
                  {previewMode === "desktop" && (
                    <iframe
                      srcDoc={generatedHTML}
                      className="w-full h-full min-h-[600px] rounded-xl border border-white/5"
                      title="preview-desktop"
                      sandbox="allow-scripts"
                    />
                  )}
                </div>
              </div>

              {/* Barre d'action déploiement */}
              {phase === "preview" && (
                <div className="px-6 py-4 border-t border-white/5 bg-slate-900/80 flex items-center gap-4">
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-white">Site prêt à déployer</div>
                    <div className="text-xs text-slate-400">Vérifiez le rendu ci-dessus avant de mettre en ligne</div>
                  </div>
                  <button onClick={startGeneration}
                    className="flex items-center gap-2 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 rounded-xl text-sm font-medium transition-all">
                    <RefreshCw size={15} /> Regénérer
                  </button>
                  <button onClick={deployToVercel}
                    className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-sm font-semibold transition-all hover:scale-[1.02] active:scale-95">
                    <Rocket size={15} /> Déployer sur Vercel
                  </button>
                </div>
              )}

              {phase === "deploying" && (
                <div className="px-6 py-4 border-t border-white/5 bg-slate-900/80 flex items-center gap-3">
                  <Loader2 size={18} className="animate-spin text-indigo-400" />
                  <span className="text-sm">Déploiement en cours sur Vercel…</span>
                </div>
              )}

              {phase === "done" && (
                <div className="px-6 py-4 border-t border-white/5 bg-emerald-950/40 border-t-emerald-900/30 flex items-center gap-4">
                  <CheckCircle2 size={20} className="text-emerald-400 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-emerald-300">Site déployé avec succès !</div>
                    <a href={deployedUrl} target="_blank" rel="noreferrer"
                      className="text-xs text-emerald-400/70 hover:text-emerald-300 underline">
                      {deployedUrl}
                    </a>
                  </div>
                  <button onClick={() => { setPhase("idle"); setCurrentStep(-1); setAgentLogs([]); }}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs transition-all">
                    <X size={14} /> Nouveau site
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}
