import type { Metadata } from 'next'
import { article, breadcrumbs, faqPage, pageMeta } from '../../../lib/seo'
import { JsonLd } from '../../../components/JsonLd'
import { SubShell } from '../../../components/SubShell'

const TITLE = 'ChatGPT et Gemini recommandent des commerces locaux : comment être cité par les IA'
const DESC = 'De plus en plus de clients demandent à une IA « un bon artisan près de chez moi ». Comment ChatGPT et Gemini choisissent les commerces qu’ils citent, et ce que vous pouvez faire cette semaine.'
const PATH = '/info/actus/chatgpt-gemini-commerces-locaux/'

export const metadata: Metadata = pageMeta({ title: TITLE, description: DESC, path: PATH, type: 'article' })

const FAQS: [string, string][] = [
  ['Peut-on payer pour apparaître dans les réponses de ChatGPT ?', 'Non. Les réponses ne sont pas des emplacements publicitaires : elles s’appuient sur les informations publiques disponibles sur votre commerce.'],
  ['Comment savoir si une IA recommande mon commerce ?', 'Posez la question vous-même à ChatGPT et Gemini avec votre métier et votre ville, à plusieurs moments, et notez les noms cités.'],
  ['Le référencement Google sert-il aussi pour les IA ?', 'Oui. Une fiche Google complète, des avis et un site clair sont aussi les sources principales des IA pour les recherches locales.'],
]

export default function News() {
  return (
    <SubShell variant="info">
      <JsonLd items={[breadcrumbs([['Accueil', '/'], ['Ressources', '/info/'], ['Actus', '/info/#actus'], ['IA et commerces locaux', '/info/actus/chatgpt-gemini-commerces-locaux/']]), article({ path: PATH, title: TITLE, description: DESC, published: '2026-11-07', section: 'Actus' }), faqPage(FAQS)]} />
      <article className="article">
        <p className="crumbs"><a href="/info/">Ressources</a> / <a href="/info/#actus">Actus</a> / IA</p>
        <span className="eyebrow">Actu · IA &amp; recherche locale</span>
        <h1>ChatGPT et Gemini recommandent des commerces. Êtes-vous dans la liste ?</h1>
        <div className="meta"><span>Lecture : 4 min</span><time dateTime="2026-11-07">Publié le 7 novembre 2026</time></div>

        <div className="callout" role="note">
          <strong className="mont">En bref</strong>
          <p>ChatGPT, Gemini et les assistants vocaux citent les commerces locaux dont ils trouvent des informations claires et cohérentes en ligne : fiche Google complète, avis nombreux et descriptifs, site qui dit précisément quoi, où et pour qui, et présence dans les annuaires. On ne paie pas pour y figurer : on augmente ses chances en soignant ces sources.</p>
        </div>

        <p>
          « Trouve-moi un bon coiffeur à Trappes ouvert le samedi. » Cette question, vos clients ne la tapent plus
          seulement dans Google : ils la posent à ChatGPT, Gemini ou à l’assistant de leur téléphone. Et l’IA ne
          donne pas dix liens. Elle cite deux ou trois noms. Si vous n’en faites pas partie, vous n’existez pas pour ce
          client.
        </p>

        <h2>Comment ces IA choisissent</h2>
        <p>Elles ne « connaissent » pas votre commerce. Elles assemblent ce qu’elles trouvent en ligne :</p>
        <ul>
          <li><strong>Votre fiche Google</strong> : catégorie, horaires, note, nombre d’avis.</li>
          <li><strong>Le contenu de vos avis</strong> : les mots que vos clients utilisent (« rapide », « accueillant »).</li>
          <li><strong>Votre site web</strong> : s’il explique clairement qui vous êtes, où et quoi.</li>
          <li><strong>Les annuaires</strong> : Pages Jaunes, sites de mairie, plateformes de votre métier.</li>
        </ul>

        <h2>Ce que vous pouvez faire cette semaine</h2>
        <ol>
          <li>Posez vous-même la question à ChatGPT et Gemini avec votre métier et votre ville. Notez qui sort.</li>
          <li>Vérifiez que votre fiche Google est complète et que vos horaires sont justes.</li>
          <li>Ajoutez sur votre site une phrase simple : « [Métier] à [ville], depuis [année], spécialisé en [x]. »</li>
          <li>Demandez des avis qui décrivent le service rendu, pas juste « super ».</li>
        </ol>

        <div className="callout">
          <strong className="mont">Bon à savoir</strong>
          <p>
            Les réponses des IA changent d’un jour à l’autre et selon la façon de poser la question. On ne « paye » pas
            pour y être : on augmente ses chances en ayant des informations claires, cohérentes et récentes partout.
          </p>
        </div>

        <h2>Questions fréquentes</h2>
        {FAQS.map(([q, a]) => (
          <div key={q}>
            <h3>{q}</h3>
            <p>{a}</p>
          </div>
        ))}

        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>On teste pour vous</strong>
          <p>L’audit visibilité IA compare votre présence à celle de 3 concurrents sur Google Maps, ChatGPT et Gemini.</p>
          <div className="hero-ctas">
            <a href="/store/" className="btn btn-primary btn-sm">Audit visibilité IA · 79 € →</a>
            <a href="/info/guide-gratuit/" className="btn btn-ghost btn-sm">Guide PDF gratuit</a>
          </div>
        </div>
      </article>
    </SubShell>
  )
}
