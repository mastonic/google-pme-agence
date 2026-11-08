import type { Metadata } from 'next'
import { abs, article, breadcrumbs, faqPage, pageMeta } from '../../seo/seo'
import { siteHref } from '../../seo/domains'
import { Byline } from '../../components/Byline'
import { JsonLd } from '../../components/JsonLd'
import { SubShell } from '../../components/SubShell'

const PATH = '/info/seo-aeo-geo/'
const TITLE = 'SEO, AEO et GEO : définitions, différences et méthodes'
const DESC = 'Guide de référence : ce que sont le SEO, l’AEO et le GEO, ce qui les distingue, comment les travailler, leurs limites, un glossaire et les sources officielles.'
const PUBLISHED = '2026-11-08'

export const metadata: Metadata = pageMeta({ title: TITLE, description: DESC, path: PATH, type: 'article' })

const GLOSSARY: [string, string][] = [
  ['SEO (Search Engine Optimization)', 'Ensemble des pratiques visant à rendre un site trouvable, compréhensible et bien classé dans les moteurs de recherche.'],
  ['AEO (Answer Engine Optimization)', 'Pratiques visant à ce qu’un contenu soit repris comme réponse directe à une question (extraits, assistants vocaux, encadrés).'],
  ['GEO (Generative Engine Optimization)', 'Pratiques visant à ce qu’un contenu soit compris, repris et cité par les moteurs génératifs (ChatGPT Search, Gemini, aperçus IA de Google, Perplexity, Claude, Copilot).'],
  ['Indexation', 'Enregistrement d’une page par un moteur après exploration. Une page non indexée ne peut pas apparaître dans les résultats.'],
  ['robots.txt', 'Fichier qui indique aux robots d’exploration les parties d’un site qu’ils peuvent visiter.'],
  ['Canonique', 'URL de référence d’un contenu, déclarée pour éviter que des copies soient traitées comme des pages distinctes.'],
  ['Données structurées', 'Balisage (schema.org) qui décrit le contenu d’une page de façon lisible par les machines : organisation, service, article, FAQ.'],
  ['Fiche Google Business Profile', 'Fiche gratuite qui présente un établissement sur Google Maps et dans la recherche locale.'],
  ['NAP', 'Name, Address, Phone : nom, adresse et téléphone, qui doivent être identiques sur toutes les présences en ligne.'],
  ['Ancrage (grounding)', 'Fait, pour un modèle d’IA, de s’appuyer sur des sources consultées pour produire sa réponse.'],
]

const FAQS: [string, string][] = [
  ['Le GEO remplace-t-il le SEO ?', 'Non. Les moteurs génératifs qui font une recherche web s’appuient sur des pages indexées. Sans bases SEO solides, le GEO n’a pas de matière.'],
  ['Faut-il des balises spéciales pour les IA ?', 'Google indique qu’aucun balisage ni fichier spécifique n’est nécessaire pour ses fonctionnalités IA. Les données structurées restent utiles pour la compréhension des pages.'],
  ['Peut-on mesurer sa visibilité dans les IA ?', 'Oui, de façon approchée : en posant régulièrement les mêmes questions aux mêmes assistants et en notant les citations. Les résultats varient selon l’outil, le mode et la formulation.'],
  ['Quelle discipline prioriser pour une TPE locale ?', 'D’abord la fiche Google et un site clair (SEO local), puis des contenus qui répondent directement aux questions des clients (AEO), ce qui sert aussi le GEO.'],
]

const SOURCES: [string, string][] = [
  ['Google Search Central, « AI features and your website »', 'https://developers.google.com/search/docs/appearance/ai-features'],
  ['Google Search Central, « Google Search Essentials »', 'https://developers.google.com/search/docs/essentials'],
  ['Google Search Central, « Creating helpful, reliable, people-first content »', 'https://developers.google.com/search/docs/fundamentals/creating-helpful-content'],
  ['Google Search Central, introduction aux données structurées', 'https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data'],
  ['Google Search Central, consolider les URL en double (canoniques)', 'https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls'],
  ['Google, classement local (pertinence, distance, notoriété)', 'https://support.google.com/business/answer/7091'],
  ['OpenAI, robots OAI-SearchBot, GPTBot, ChatGPT-User', 'https://developers.openai.com/api/docs/bots'],
  ['Perplexity, robots PerplexityBot et Perplexity-User', 'https://docs.perplexity.ai/guides/bots'],
  ['Anthropic, robots ClaudeBot, Claude-User, Claude-SearchBot', 'https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler'],
  ['Bing Webmaster Guidelines', 'https://www.bing.com/webmasters/help/webmasters-guidelines-30fba23a'],
]

export default function SeoAeoGeo() {
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Ressources', '/info/'], ['SEO, AEO et GEO', PATH]]),
          { ...article({ path: PATH, title: TITLE, description: DESC, published: PUBLISHED, modified: PUBLISHED, section: 'Guides de référence', about: 'SEO, AEO et GEO' }), citation: SOURCES.map(([, u]) => u) },
          { '@type': 'DefinedTermSet', '@id': abs(PATH) + '#glossaire', name: 'Glossaire SEO, AEO et GEO', hasDefinedTerm: GLOSSARY.map(([t, d]) => ({ '@type': 'DefinedTerm', name: t, description: d, inDefinedTermSet: abs(PATH) + '#glossaire' })) },
          faqPage(FAQS),
        ]}
      />
      <article className="article">
        <p className="crumbs"><a href={siteHref('/info/')}>Ressources</a> / SEO, AEO et GEO</p>
        <span className="eyebrow">Guide de référence</span>
        <h1>SEO, AEO et GEO : définitions, différences et méthodes</h1>
        <div className="meta">
          <time dateTime={PUBLISHED}>Publié le 8 novembre 2026</time>
          <Byline />
        </div>
        <div className="callout" role="note">
          <strong className="mont">La réponse courte</strong>
          <p>
            Le SEO rend un site trouvable et bien classé dans les moteurs de recherche. L’AEO vise à fournir la réponse
            directe à une question. Le GEO vise à être compris et cité par les moteurs génératifs comme ChatGPT, Gemini ou
            Perplexity. Les trois reposent sur la même base : des pages indexables, utiles, claires et des informations
            cohérentes partout.
          </p>
        </div>

        <nav className="toc" aria-label="Sommaire">
          <strong className="mont">Au sommaire</strong>
          <ol>
            <li><a href="#definitions">Définitions</a></li>
            <li><a href="#differences">Différences</a></li>
            <li><a href="#methodes">Méthodes</a></li>
            <li><a href="#exemples">Exemples pour une entreprise locale</a></li>
            <li><a href="#limites">Limites</a></li>
            <li><a href="#faq">Questions fréquentes</a></li>
            <li><a href="#glossaire">Glossaire</a></li>
            <li><a href="#sources">Sources</a></li>
          </ol>
        </nav>

        <h2 id="definitions">Définitions</h2>
        <h3>SEO : être trouvé dans les moteurs de recherche</h3>
        <p>Le référencement naturel regroupe la technique (exploration, indexation, vitesse, canoniques), le contenu (pages utiles qui répondent aux recherches) et la notoriété (liens, citations, avis). Pour une entreprise locale, il inclut la fiche Google Business Profile, dont le classement dépend de la pertinence, de la distance et de la notoriété.</p>
        <h3>AEO : être la réponse</h3>
        <p>L’optimisation pour les moteurs de réponse consiste à formuler des réponses courtes, exactes et bien structurées aux questions réelles des utilisateurs, pour qu’elles puissent être reprises telles quelles : extrait en tête de résultats, réponse vocale, encadré.</p>
        <h3>GEO : être cité par les IA génératives</h3>
        <p>L’optimisation pour les moteurs génératifs vise les assistants qui rédigent une réponse à partir de sources : ChatGPT Search, Gemini et les aperçus IA de Google, Perplexity, Claude, Copilot. Ils s’appuient sur des pages qu’ils peuvent explorer, et croisent les informations de plusieurs sources.</p>

        <h2 id="differences">Différences</h2>
        <div className="table-wrap">
          <table className="seo-table">
            <caption>SEO, AEO et GEO en un coup d’œil</caption>
            <thead><tr><th scope="col"></th><th scope="col">SEO</th><th scope="col">AEO</th><th scope="col">GEO</th></tr></thead>
            <tbody>
              <tr><th scope="row">Objectif</th><td>Être classé</td><td>Être la réponse</td><td>Être cité</td></tr>
              <tr><th scope="row">Où</th><td>Pages de résultats, Google Maps</td><td>Extraits, réponses vocales</td><td>Réponses rédigées par les IA</td></tr>
              <tr><th scope="row">Robots</th><td>Googlebot, Bingbot</td><td>Les mêmes</td><td>OAI-SearchBot, PerplexityBot, Claude-SearchBot… et Googlebot pour Google</td></tr>
              <tr><th scope="row">Mesure</th><td>Search Console, Bing Webmaster Tools</td><td>Search Console (requêtes, extraits)</td><td>Tests réguliers de questions, sources citées</td></tr>
            </tbody>
          </table>
        </div>

        <h2 id="methodes">Méthodes</h2>
        <ol>
          <li><strong>Rendre le site explorable</strong> : robots.txt qui autorise les robots de recherche, sitemap, canoniques correctes, pages rapides.</li>
          <li><strong>Répondre aux vraies questions</strong> : une réponse directe en tête, puis le détail, avec des titres explicites.</li>
          <li><strong>Donner des faits vérifiables</strong> : prix, délais, zones, conditions, datés et sourcés.</li>
          <li><strong>Être cohérent partout</strong> : mêmes nom, coordonnées, services sur le site, la fiche Google et les annuaires.</li>
          <li><strong>Identifier les auteurs et l’éditeur</strong> : qui écrit, qui est responsable.</li>
          <li><strong>Baliser sans tricher</strong> : données structurées conformes au contenu visible.</li>
          <li><strong>Mesurer</strong> : Search Console, Bing Webmaster Tools, et suivi d’une liste fixe de questions posées aux assistants.</li>
        </ol>

        <h2 id="exemples">Exemples pour une entreprise locale</h2>
        <ul>
          <li><strong>SEO</strong> : un électricien de Poissy crée une page « dépannage électrique » qui cite les communes desservies et la relie à sa fiche Google.</li>
          <li><strong>AEO</strong> : il ajoute en tête de page « Intervention le jour même à Poissy, Carrières-sous-Poissy et Villennes-sur-Seine, du lundi au samedi ».</li>
          <li><strong>GEO</strong> : il vérifie que ses horaires, sa zone et son téléphone sont identiques sur son site, sa fiche Google et les annuaires, et suit chaque mois la question « quel électricien à Poissy ? » dans trois assistants.</li>
        </ul>
        <p>Les guides de cette rubrique appliquent ces principes métier par métier : <a href={siteHref('/info/guides/')} className="link-underline">voir les guides métier</a>.</p>

        <h2 id="limites">Limites</h2>
        <ul>
          <li>Aucune méthode ne garantit une position Google ni une citation par une IA.</li>
          <li>Les réponses des assistants varient selon l’outil, le modèle, le mode et la formulation.</li>
          <li>Google indique qu’aucun fichier ni balisage spécial n’est nécessaire pour ses fonctionnalités IA.</li>
          <li>Les effets se mesurent sur des mois, pas sur des jours.</li>
        </ul>

        <h2 id="faq">Questions fréquentes</h2>
        {FAQS.map(([q, a]) => (<div key={q}><h3>{q}</h3><p>{a}</p></div>))}

        <h2 id="glossaire">Glossaire</h2>
        <dl className="glossary">
          {GLOSSARY.map(([t, d]) => (<div key={t}><dt><strong>{t}</strong></dt><dd>{d}</dd></div>))}
        </dl>

        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>Passer à la pratique</strong>
          <p>Pulse Locale PME applique ces méthodes pour les artisans et TPE, notamment dans les Yvelines et en Eure-et-Loir.</p>
          <div className="hero-ctas">
            <a href={siteHref('/methode/')} className="btn btn-primary btn-sm">Notre méthode →</a>
            <a href={siteHref('/store/#packs')} className="btn btn-ghost btn-sm">Audit visibilité IA à 99 € HT</a>
          </div>
        </div>

        <h2 id="sources">Sources</h2>
        <ol className="sources">{SOURCES.map(([l, u]) => <li key={u}><a href={u} rel="noopener" target="_blank">{l}</a></li>)}</ol>

        <nav aria-label="À lire aussi">
          <h2>À lire aussi</h2>
          <ul>
            <li><a href={siteHref('/info/articles/apparaitre-chatgpt-gemini-perplexity/')} className="link-underline">Comment apparaître dans les réponses de ChatGPT, Gemini et Perplexity ?</a></li>
            <li><a href={siteHref('/info/articles/')} className="link-underline">Tous les articles</a></li>
          </ul>
        </nav>
      </article>
    </SubShell>
  )
}
