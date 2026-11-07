import type { MetadataRoute } from 'next'
import { abs } from './seo/seo'

export const dynamic = 'force-static'

// Moteurs classiques ET moteurs de réponse IA (GEO) : tous autorisés, sauf l'espace admin.
const AI_BOTS = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'PerplexityBot', 'Google-Extended', 'Applebot-Extended', 'Bingbot']

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: '*', allow: '/', disallow: ['/admin/', '/app/', '/espace/'] },
      ...AI_BOTS.map((userAgent) => ({ userAgent, allow: '/', disallow: ['/admin/', '/app/', '/espace/'] })),
    ],
    sitemap: abs('/sitemap.xml'),
  }
}
