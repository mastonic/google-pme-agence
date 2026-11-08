import type { Metadata } from 'next'
import { ArticleLayout, metaFor, type Section, type Source } from '../../../components/ArticleLayout'
import { siteHref } from '../../../seo/domains'
import { pageMeta } from '../../../seo/seo'

const SLUG = 'apparaitre-chatgpt-gemini-perplexity'
export const metadata: Metadata = pageMeta(metaFor(SLUG))

const SOURCES: Source[] = [
  ['Google Search Central, « AI features and your website »', 'https://developers.google.com/search/docs/appearance/ai-features'],
  ['Google Search Central, robots d’exploration courants de Google (dont Google-Extended)', 'https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers'],
  ['OpenAI, « Overview of OpenAI Crawlers » (OAI-SearchBot, GPTBot, ChatGPT-User)', 'https://developers.openai.com/api/docs/bots'],
  ['Perplexity, « Perplexity Crawlers » (PerplexityBot, Perplexity-User)', 'https://docs.perplexity.ai/guides/bots'],
  ['Anthropic, robots ClaudeBot, Claude-User et Claude-SearchBot', 'https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler'],
  ['Google Search Central, « Creating helpful, reliable, people-first content »', 'https://developers.google.com/search/docs/fundamentals/creating-helpful-content'],
  ['Google Search Central, introduction aux données structurées', 'https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data'],
  ['Bing Webmaster Guidelines', 'https://www.bing.com/webmasters/help/webmasters-guidelines-30fba23a'],
]

const SECTIONS: Section[] = [
  {
    id: 'definitions', title: 'SEO, AEO, GEO : de quoi parle-t-on ?',
    body: (<>
      <ul>
        <li><strong>SEO</strong> (Search Engine Optimization) : être bien classé dans les résultats de Google, Bing et des autres moteurs.</li>
        <li><strong>AEO</strong> (Answer Engine Optimization) : être la réponse directe affichée à une question (extraits, réponses vocales, encadrés).</li>
        <li><strong>GEO</strong> (Generative Engine Optimization) : être compris, repris et cité par les moteurs génératifs (ChatGPT Search, Gemini, aperçus IA de Google, Perplexity, Claude, Copilot).</li>
      </ul>
      <p>AEO et GEO ne remplacent pas le SEO : ils s’appuient dessus. Un assistant qui fait une recherche web ne peut citer que des pages qu’il peut trouver et lire. <a href={siteHref('/info/seo-aeo-geo/')} className="link-underline">Notre guide de référence SEO / AEO / GEO</a> détaille les définitions.</p>
    </>),
  },
  {
    id: 'indexation', title: 'Le préalable : être indexable et accessible aux bons robots',
    body: (<>
      <p>Pour les aperçus IA et le mode IA de Google, Google indique qu’il n’existe pas d’exigence supplémentaire : la page doit être indexée et pouvoir s’afficher dans la recherche avec un extrait [1]. L’accès est contrôlé par Googlebot ; Google-Extended sert à limiter l’usage des contenus pour l’entraînement et l’ancrage de certains modèles Gemini, et non l’indexation dans la recherche Google [1][2].</p>
      <p>Chaque assistant a ses propres robots, aux usages différents :</p>
      <div className="table-wrap">
        <table className="seo-table">
          <caption>Principaux robots des assistants IA (d’après leurs documentations officielles)</caption>
          <thead><tr><th scope="col">Robot</th><th scope="col">Éditeur</th><th scope="col">Usage déclaré</th></tr></thead>
          <tbody>
            <tr><th scope="row">OAI-SearchBot</th><td>OpenAI</td><td>Faire apparaître des sites dans la recherche de ChatGPT [3]</td></tr>
            <tr><th scope="row">ChatGPT-User</th><td>OpenAI</td><td>Visites déclenchées par une demande d’utilisateur [3]</td></tr>
            <tr><th scope="row">GPTBot</th><td>OpenAI</td><td>Collecte pour l’entraînement des modèles [3]</td></tr>
            <tr><th scope="row">PerplexityBot</th><td>Perplexity</td><td>Faire apparaître et lier des sites dans les résultats Perplexity [4]</td></tr>
            <tr><th scope="row">Claude-SearchBot</th><td>Anthropic</td><td>Améliorer la pertinence des résultats de recherche de Claude [5]</td></tr>
            <tr><th scope="row">Claude-User</th><td>Anthropic</td><td>Visites déclenchées par une question d’utilisateur [5]</td></tr>
            <tr><th scope="row">ClaudeBot</th><td>Anthropic</td><td>Collecte pouvant servir à l’entraînement [5]</td></tr>
          </tbody>
        </table>
      </div>
      <p>Conséquence pratique : bloquer un robot de recherche (OAI-SearchBot, PerplexityBot, Claude-SearchBot) réduit votre visibilité dans l’assistant concerné ; bloquer un robot d’entraînement n’a pas cet effet déclaré. Vérifiez votre fichier robots.txt avant tout.</p>
    </>),
  },
  {
    id: 'contenus-citables', title: 'Écrire des contenus faciles à citer',
    body: (<>
      <ul>
        <li><strong>Une réponse directe en tête</strong> : deux à quatre phrases qui répondent à la question, avant le développement.</li>
        <li><strong>Des faits précis</strong> : prix, délais, zones, conditions, avec leur date.</li>
        <li><strong>Une structure explicite</strong> : titres sous forme de questions, listes, tableaux.</li>
        <li><strong>Des sources</strong> pour les faits externes.</li>
        <li><strong>Un contenu utile pour les personnes</strong>, pas écrit pour les moteurs : c’est la recommandation centrale de Google [6].</li>
      </ul>
    </>),
  },
  {
    id: 'autorite', title: 'Autorité et réputation',
    body: (<>
      <p>Les moteurs génératifs croisent plusieurs sources. Une entreprise décrite de façon identique sur son site, sa fiche Google, les annuaires professionnels et la presse locale est plus facile à identifier qu’une entreprise aux informations contradictoires. Les avis clients, les mentions dans des sites locaux et une identité claire (qui édite le site, qui signe les contenus) renforcent cette confiance.</p>
    </>),
  },
  {
    id: 'donnees-structurees', title: 'Données structurées : utiles, pas magiques',
    body: (<>
      <p>Les données structurées (schema.org) aident les moteurs à comprendre une page : organisation, service, article, FAQ, fil d’Ariane [7]. Elles doivent décrire le contenu visible de la page. Google précise qu’aucun balisage spécifique n’est nécessaire pour apparaître dans ses fonctionnalités IA [1] : le balisage aide à la compréhension, il ne garantit aucun affichage.</p>
    </>),
  },
  {
    id: 'limites', title: 'Les limites à connaître',
    body: (<>
      <ul>
        <li>Personne ne peut garantir qu’un assistant citera votre entreprise.</li>
        <li>Les réponses varient selon l’outil, le modèle, le mode (avec ou sans recherche web), la formulation et la localisation.</li>
        <li>Les assistants peuvent se tromper ou reprendre une information obsolète : d’où l’importance d’informations à jour partout.</li>
        <li>Les fichiers comme llms.txt ne sont pas requis par Google [1] ; ils peuvent aider d’autres outils, sans effet garanti.</li>
      </ul>
    </>),
  },
  {
    id: 'mesure', title: 'Comment mesurer sa visibilité dans les IA',
    body: (<>
      <ol>
        <li>Listez 15 à 20 questions que posent vos clients (« quel électricien à Poissy ? », « combien coûte… »).</li>
        <li>Posez-les chaque mois aux mêmes assistants, dans le même mode (recherche web activée).</li>
        <li>Notez : présence ou non de votre entreprise, source citée, concurrents mentionnés.</li>
        <li>Côté Google, le trafic issu des fonctionnalités IA est inclus dans le rapport Performances de la Search Console, type de recherche « Web » [1].</li>
      </ol>
      <p>C’est ce que fait notre <a href={siteHref('/store/#packs')} className="link-underline">audit visibilité IA à 99 € HT</a>.</p>
    </>),
  },
]

const FAQS: [string, string][] = [
  ['Faut-il un fichier spécial pour apparaître dans ChatGPT ?', 'Non. Pour ChatGPT Search, le site doit être accessible à OAI-SearchBot. Pour Google, aucun fichier ou balisage spécial n’est requis selon sa documentation. Le fichier llms.txt est facultatif.'],
  ['Bloquer GPTBot me retire-t-il de ChatGPT ?', 'Selon OpenAI, GPTBot sert à l’entraînement et OAI-SearchBot à la recherche : bloquer GPTBot seul ne vise pas l’apparition dans la recherche de ChatGPT. Vérifiez la documentation à jour avant de modifier votre robots.txt.'],
  ['Google-Extended bloque-t-il mon site dans Google ?', 'Non. Google-Extended concerne l’usage des contenus par certains modèles Gemini. L’indexation dans Google Search dépend de Googlebot.'],
  ['Combien de temps pour être cité par une IA ?', 'Il n’existe pas de délai garanti. Il faut d’abord que les pages soient explorées et indexées, puis que les informations soient jugées pertinentes et fiables.'],
]

export default function Page() {
  return (
    <ArticleLayout
      slug={SLUG}
      answer="Pour apparaître dans les réponses de ChatGPT, Gemini et Perplexity, il faut d’abord des pages indexables, accessibles aux robots de recherche de ces services (OAI-SearchBot, Googlebot, PerplexityBot), puis des contenus clairs qui répondent directement aux questions, des informations identiques sur toutes vos présences en ligne et une bonne réputation. Aucun balisage ne garantit une citation, et personne ne peut la promettre."
      sections={SECTIONS}
      faqs={FAQS}
      sources={SOURCES}
      related={['choisir-agence-seo-local-yvelines', 'visibilite-google-maps-chartres']}
    />
  )
}
