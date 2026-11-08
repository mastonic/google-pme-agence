import type { MetadataRoute } from 'next'
import { CURRENT_ORIGIN } from './seo/domains'

export const dynamic = 'force-static'

const PRIVATE = ['/admin/', '/app/', '/espace/']

// Robots de moteurs de recherche et de réponse : ils font apparaître le site dans leurs résultats.
//  - Googlebot / Bingbot : recherche Google (y compris aperçus IA) et Bing / Copilot.
//  - OAI-SearchBot : recherche ChatGPT. ChatGPT-User : visites déclenchées par un utilisateur.
//  - PerplexityBot : résultats Perplexity. Claude-SearchBot / Claude-User : recherche et visites de Claude.
const SEARCH_BOTS = ['Googlebot', 'Bingbot', 'OAI-SearchBot', 'ChatGPT-User', 'PerplexityBot', 'Perplexity-User', 'Claude-SearchBot', 'Claude-User', 'Applebot']

// Robots de collecte pour l'entraînement des modèles (pas d'effet déclaré sur la visibilité en recherche).
// Autorisés à ce jour : décision éditoriale À VALIDER (voir docs/seo/SEO_AEO_GEO_AUDIT.md).
// Google-Extended ne contrôle PAS l'indexation Google Search (c'est Googlebot).
const TRAINING_BOTS = ['GPTBot', 'ClaudeBot', 'Google-Extended', 'Applebot-Extended']

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: '*', allow: '/', disallow: PRIVATE },
      { userAgent: SEARCH_BOTS, allow: '/', disallow: PRIVATE },
      { userAgent: TRAINING_BOTS, allow: '/', disallow: PRIVATE },
    ],
    sitemap: `${CURRENT_ORIGIN}/sitemap.xml`,
  }
}
