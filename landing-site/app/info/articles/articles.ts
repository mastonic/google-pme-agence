// Articles de fond du .info (AEO / GEO) : métadonnées partagées par les pages, l'index,
// le sitemap et llms.txt. Dates réelles : `modified` ne change que si le contenu change.

export type ArticleMeta = {
  slug: string
  title: string          // <title> et titre de l'article
  description: string    // ≤ 160 caractères
  keyword: string        // mot-clé principal (documentation)
  card: string
  published: string
  modified: string
  readMin: number
}

export const ARTICLES: ArticleMeta[] = [
  {
    slug: 'prix-site-internet-artisan-yvelines',
    title: 'Combien coûte un site internet pour artisan dans les Yvelines en 2026 ?',
    description: 'Site vitrine, e-commerce, maintenance, frais récurrents : les prix publics relevés dans les Yvelines, nos tarifs et un tableau comparatif transparent.',
    keyword: 'prix site internet artisan Yvelines',
    card: 'Achat ou abonnement, vitrine ou e-commerce : les prix réels et ce qu’ils incluent.',
    published: '2026-11-08', modified: '2026-11-08', readMin: 8,
  },
  {
    slug: 'visibilite-google-maps-chartres',
    title: 'Comment améliorer sa visibilité sur Google Maps à Chartres ?',
    description: 'Fiche Google Business Profile, catégories, services, photos, avis authentiques et mesure des résultats : la méthode pour les entreprises de Chartres.',
    keyword: 'visibilité Google Maps Chartres',
    card: 'Les réglages de fiche Google qui comptent dans l’agglomération chartraine.',
    published: '2026-11-08', modified: '2026-11-08', readMin: 9,
  },
  {
    slug: 'choisir-agence-seo-local-yvelines',
    title: 'Comment choisir une agence SEO local dans les Yvelines ?',
    description: 'Critères, questions à poser, livrables, contrat, transparence des prix et signaux d’alerte pour choisir une agence de référencement local dans le 78.',
    keyword: 'agence SEO local Yvelines',
    card: 'Les questions à poser avant de signer, et les signaux qui doivent alerter.',
    published: '2026-11-08', modified: '2026-11-08', readMin: 8,
  },
  {
    slug: 'apparaitre-chatgpt-gemini-perplexity',
    title: 'Comment apparaître dans les réponses de ChatGPT, Gemini et Perplexity ?',
    description: 'SEO, AEO et GEO : indexation, robots, contenus citables, réputation, données structurées, limites et méthodes de mesure, d’après les documentations officielles.',
    keyword: 'apparaître dans ChatGPT',
    card: 'Ce que disent vraiment Google, OpenAI, Perplexity et Anthropic, et comment mesurer.',
    published: '2026-11-08', modified: '2026-11-08', readMin: 10,
  },
  {
    slug: 'prix-optimisation-fiche-google-business-profile',
    title: 'Combien coûte l’optimisation d’une fiche Google Business Profile ?',
    description: 'Actions réalisées, facteurs de prix, délais, livrables et limites de l’optimisation d’une fiche Google, avec les prix publics relevés et notre offre à 149 € HT.',
    keyword: 'prix optimisation fiche Google',
    card: 'Ce que l’on paie vraiment, ce qu’on doit recevoir, et ce qu’aucun prestataire ne peut promettre.',
    published: '2026-11-08', modified: '2026-11-08', readMin: 7,
  },
  {
    slug: 'receptionniste-ia-artisan',
    title: 'Réceptionniste IA pour artisan : fonctionnement, limites et tarifs',
    description: 'Renvoi d’appel, qualification, urgences, protection des données, limites de l’IA et tarifs : tout sur la réceptionniste IA pour artisans et TPE.',
    keyword: 'réceptionniste IA artisan',
    card: 'Comment elle répond, ce qu’elle ne fait pas, combien elle coûte.',
    published: '2026-11-08', modified: '2026-11-08', readMin: 8,
  },
]

export const articleBySlug = (slug: string) => ARTICLES.find((a) => a.slug === slug)
export const articlePath = (slug: string) => `/info/articles/${slug}/`
