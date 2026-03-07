# 🕵️‍♂️ Local-Pulse : Agence de Prospection SaaS "Elite"

Local-Pulse est une plateforme SaaS d'automatisation de prospection B2B utilisant **CrewAI** pour orchestrer une équipe d'agents intelligents. Elle aide les agences marketing à scanner des commerces locaux, analyser leur "Digital Gap" et générer des démos (Landing Pages) ultra-personnalisées en moins de 60 secondes.

## 🚀 Fonctionnalités Clés

- **Scout Agent** : Scan profond Google Maps (Avis, Photos propriétaire/clients, Catégories).
- **Designer Agent** : Routage de template automatique par métier (Restaurant, Pharmacie, Garage) et palettes de couleurs ciblées.
- **Copywriter Agent** : Storytelling persuasif et email outreach personnalisé.
- **Ingénieur Agent** : Génération de Landing Page (HTML/Tailwind) et déploiement immédiat sur **Vercel**.
- **Dashboard Elite** : Suivi des KPIs (MRR, Démos), Pipeline CRM et cockpit de contrôle des agents en temps réel.

## 🛠️ Stack Technique

- **Backend** : FastAPI, SQLAlchemy (SQLite), Redis.
- **Frontend** : Streamlit (Dashboard Elite) & React/Vite.
- **AI Engine** : CrewAI, OpenAI GPT-4o-mini, Fal.ai (Flux.1), LangChain.
- **Infrastructure** : Vercel (Hosting démos), Gmail API (Outreach).

## 📦 Installation & Déploiement

### Déploiement Local
1. Clonez le dépôt.
2. Configurez votre fichier `.env` (voir `.env.example`).
3. Lancez les services :
   ```bash
   ./start.sh
   ```

### Déploiement VPS
Utilisez le script automatisé fourni :
```bash
chmod +x deploy_vps.sh
./deploy_vps.sh
```

## 🎨 Templates Métiers
Le système switch automatiquement entre les styles suivants en fonction de la catégorie Google Places :
- **luxury-dining-v3** : Restaurants et Food.
- **clean-medical-v1** : Pharmacies et cabinets médicaux.
- **industrial-bold-v2** : Garages et services techniques.

---
*Développé pour l'automatisation de prospection B2B haute fidélité.*
