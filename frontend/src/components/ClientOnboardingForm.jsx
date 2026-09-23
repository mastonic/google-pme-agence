import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { CheckCircle2, ImagePlus, Loader2, Save, AlertTriangle } from 'lucide-react';

const EMPTY = {
  identity: { business_name:'', logo_url:'', colors:[] },
  contact: { phone:'', email:'', address:'' },
  activity: { description:'', services:[], hours:{}, service_areas:[] },
  brand: { tone:'', tagline:'' },
  media: { photos:[], videos:[] },
  goals: { primary:'', secondary:[] },
  google: { profile_url:'', access_granted:false },
  social: { instagram:'', facebook:'', tiktok:'', linkedin:'' },
  faq: [],
  content: { constraints:[], claims_to_avoid:[] },
};

function merge(base, extra) {
  const out = structuredClone(base);
  for (const [k,v] of Object.entries(extra || {})) {
    if (v && typeof v === 'object' && !Array.isArray(v) && out[k] && typeof out[k] === 'object' && !Array.isArray(out[k])) {
      out[k] = { ...out[k], ...v };
    } else out[k] = v;
  }
  return out;
}
const arr = v => typeof v === 'string' ? v.split('\n').map(x=>x.trim()).filter(Boolean) : (v || []);
const text = v => Array.isArray(v) ? v.join('\n') : '';

async function fileToDataUrl(file) {
  if (file.size > 1_500_000) throw new Error('Fichier trop lourd : 1,5 Mo maximum.');
  return await new Promise((resolve,reject)=>{
    const r=new FileReader(); r.onload=()=>resolve(r.result); r.onerror=reject; r.readAsDataURL(file);
  });
}

export default function ClientOnboardingForm({ businessId=null, token=null, compact=false, onSaved=null }) {
  const [profile,setProfile]=useState(EMPTY);
  const [progress,setProgress]=useState({percent:0,missing:[]});
  const [plan,setPlan]=useState('starter');
  const [name,setName]=useState('');
  const [loading,setLoading]=useState(true);
  const [saving,setSaving]=useState(false);
  const [msg,setMsg]=useState('');

  const endpoint = token ? `/client/onboarding/${token}` : `/businesses/${businessId}/onboarding`;

  const load=async()=>{
    setLoading(true);
    try{
      const r=await axios.get(endpoint);
      setProfile(merge(EMPTY,r.data.profile||{}));
      setProgress(r.data.progress||{percent:0,missing:[]});
      setPlan(r.data.plan_tier||'starter');
      setName(r.data.business_name||r.data.profile?.identity?.business_name||'');
    } finally { setLoading(false); }
  };
  useEffect(()=>{ if(token||businessId) load().catch(console.error); },[token,businessId]);

  const set=(group,key,value)=>setProfile(p=>({...p,[group]:{...p[group],[key]:value}}));
  const save=async()=>{
    setSaving(true);setMsg('');
    try{
      const r=await axios.put(endpoint,{profile});
      setProgress(r.data.progress||progress);
      setMsg(r.data.progress?.complete ? 'Onboarding complet. Les agents disposent des informations nécessaires.' : 'Enregistré. Il reste quelques informations à compléter.');
      onSaved?.(r.data);
    }catch(e){setMsg(e?.response?.data?.detail||e.message||'Erreur');}
    finally{setSaving(false);}
  };
  const handleLogo=async e=>{
    const f=e.target.files?.[0]; if(!f)return;
    try{set('identity','logo_url',await fileToDataUrl(f));}catch(err){setMsg(err.message);}
  };
  const handlePhotos=async e=>{
    const files=[...(e.target.files||[])].slice(0,6);
    try{
      const urls=[]; for(const f of files) urls.push(await fileToDataUrl(f));
      set('media','photos',[...(profile.media?.photos||[]),...urls].slice(0,10));
    }catch(err){setMsg(err.message);}
  };

  if(loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin"/></div>;

  return <div className={compact?'space-y-5':'max-w-5xl mx-auto p-4 md:p-8 space-y-6'}>
    {!compact && <div>
      <h1 className="text-2xl md:text-3xl font-extrabold">Bienvenue {name ? `— ${name}` : ''}</h1>
      <p className="text-slate-400 mt-2">Complétez ces informations une fois. Elles deviennent la source de vérité de vos équipes d’agents.</p>
    </div>}

    <div className="glass border border-white/10 rounded-2xl p-4">
      <div className="flex justify-between gap-4 items-center">
        <div><p className="font-bold">Onboarding · {plan.toUpperCase()}</p><p className="text-xs text-slate-500">{progress.missing?.length||0} information(s) obligatoire(s) restante(s)</p></div>
        <div className="text-2xl font-extrabold text-brand">{Math.round(progress.percent||0)}%</div>
      </div>
      <div className="h-2 bg-slate-800 rounded-full mt-3 overflow-hidden"><div className="h-full bg-brand" style={{width:`${progress.percent||0}%`}}/></div>
      {progress.missing?.length>0 && <div className="flex flex-wrap gap-1.5 mt-3">{progress.missing.map(x=><span key={x.path} className="text-[10px] px-2 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">{x.label}</span>)}</div>}
    </div>

    <Section title="Identité & marque">
      <Field label="Nom commercial"><input value={profile.identity?.business_name||''} onChange={e=>set('identity','business_name',e.target.value)}/></Field>
      <Field label="Slogan"><input value={profile.brand?.tagline||''} onChange={e=>set('brand','tagline',e.target.value)}/></Field>
      <Field label="Ton de marque"><input placeholder="Ex. chaleureux, premium, familial" value={profile.brand?.tone||''} onChange={e=>set('brand','tone',e.target.value)}/></Field>
      <Field label="Logo">
        <input type="file" accept="image/*" onChange={handleLogo}/>
        {profile.identity?.logo_url && <img src={profile.identity.logo_url} className="mt-2 h-16 max-w-40 object-contain rounded-lg bg-white/5 p-2"/>}
      </Field>
    </Section>

    <Section title="Coordonnées">
      <Field label="Téléphone"><input value={profile.contact?.phone||''} onChange={e=>set('contact','phone',e.target.value)}/></Field>
      <Field label="Email"><input type="email" value={profile.contact?.email||''} onChange={e=>set('contact','email',e.target.value)}/></Field>
      <Field label="Adresse"><input value={profile.contact?.address||''} onChange={e=>set('contact','address',e.target.value)}/></Field>
      <Field label="Fiche Google"><input placeholder="Lien Google Business" value={profile.google?.profile_url||''} onChange={e=>set('google','profile_url',e.target.value)}/></Field>
    </Section>

    <Section title="Activité">
      <Field label="Description"><textarea rows={3} value={profile.activity?.description||''} onChange={e=>set('activity','description',e.target.value)}/></Field>
      <Field label="Services — un par ligne"><textarea rows={5} value={text(profile.activity?.services)} onChange={e=>set('activity','services',arr(e.target.value))}/></Field>
      <Field label="Zones desservies — une par ligne"><textarea rows={4} value={text(profile.activity?.service_areas)} onChange={e=>set('activity','service_areas',arr(e.target.value))}/></Field>
      <Field label="Horaires"><textarea rows={4} placeholder="Lundi 09:00-18:00&#10;Mardi 09:00-18:00" value={typeof profile.activity?.hours==='string'?profile.activity.hours:Object.entries(profile.activity?.hours||{}).map(([k,v])=>`${k}: ${v}`).join('\n')} onChange={e=>set('activity','hours',e.target.value)}/></Field>
    </Section>

    <Section title="Objectifs & contenu">
      <Field label="Objectif principal"><select value={profile.goals?.primary||''} onChange={e=>set('goals','primary',e.target.value)}><option value="">Choisir…</option><option value="calls">Plus d’appels</option><option value="quotes">Demandes de devis</option><option value="booking">Réservations</option><option value="whatsapp">WhatsApp</option><option value="store_visits">Visites en établissement</option></select></Field>
      <Field label="FAQ — une question/réponse par ligne"><textarea rows={4} value={text(profile.faq)} onChange={e=>setProfile(p=>({...p,faq:arr(e.target.value)}))}/></Field>
      <Field label="Contraintes / choses à ne pas dire"><textarea rows={4} value={text(profile.content?.constraints)} onChange={e=>set('content','constraints',arr(e.target.value))}/></Field>
    </Section>

    <Section title="Réseaux sociaux">
      {['instagram','facebook','tiktok','linkedin'].map(k=><Field key={k} label={k[0].toUpperCase()+k.slice(1)}><input value={profile.social?.[k]||''} onChange={e=>set('social',k,e.target.value)}/></Field>)}
    </Section>

    <Section title="Photos">
      <Field label="Ajouter des photos (max 1,5 Mo chacune)"><input type="file" multiple accept="image/*" onChange={handlePhotos}/></Field>
      <div className="md:col-span-2 grid grid-cols-3 sm:grid-cols-5 gap-2">{(profile.media?.photos||[]).map((u,i)=><div key={i} className="relative aspect-square"><img src={u} className="w-full h-full object-cover rounded-lg"/><button onClick={()=>set('media','photos',profile.media.photos.filter((_,x)=>x!==i))} className="absolute top-1 right-1 bg-black/70 rounded-full px-2">×</button></div>)}</div>
    </Section>

    {msg && <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm flex gap-2 items-start">{progress.complete?<CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5"/>:<AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5"/>}{msg}</div>}
    <button onClick={save} disabled={saving} className="w-full md:w-auto bg-brand hover:bg-brand-dark px-6 py-3 rounded-xl font-bold flex items-center justify-center gap-2 disabled:opacity-50">{saving?<Loader2 className="w-4 h-4 animate-spin"/>:<Save className="w-4 h-4"/>}Enregistrer</button>
  </div>;
}

function Section({title,children}){return <div className="glass border border-white/10 rounded-2xl p-4 md:p-5"><h3 className="font-bold mb-4">{title}</h3><div className="grid grid-cols-1 md:grid-cols-2 gap-4">{children}</div></div>}
function Field({label,children}){return <label className="block text-sm"><span className="block text-[11px] uppercase tracking-wider text-slate-500 font-bold mb-2">{label}</span><div className="[&_input]:w-full [&_input]:bg-slate-800 [&_input]:border [&_input]:border-white/10 [&_input]:rounded-xl [&_input]:px-3 [&_input]:py-2.5 [&_textarea]:w-full [&_textarea]:bg-slate-800 [&_textarea]:border [&_textarea]:border-white/10 [&_textarea]:rounded-xl [&_textarea]:px-3 [&_textarea]:py-2.5 [&_select]:w-full [&_select]:bg-slate-800 [&_select]:border [&_select]:border-white/10 [&_select]:rounded-xl [&_select]:px-3 [&_select]:py-2.5">{children}</div></label>}
