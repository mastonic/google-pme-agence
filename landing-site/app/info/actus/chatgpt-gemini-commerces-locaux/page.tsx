import type { Metadata } from 'next'
import { SubShell } from '../../../components/SubShell'

export const metadata: Metadata = {
  title: 'ChatGPT et Gemini recommandent des commerces : comment être dans la liste · Pulse‑Pro',
  description:
    'De plus en plus de clients demandent à une IA « un bon garage près de chez moi ». Comment ces IA choisissent, et ce que vous pouvez faire dès cette semaine.',
  alternates: { canonical: '/info/actus/chatgpt-gemini-commerces-locaux/' },
}

export default function News() {
  return (
    <SubShell variant="info">
      <article className="article">
        <p className="crumbs"><a href="/info/">Ressources</a> / <a href="/info/#actus">Actus</a> / IA</p>
        <span className="eyebrow">Actu · IA &amp; recherche locale</span>
        <h1>ChatGPT et Gemini recommandent des commerces. Êtes-vous dans la liste ?</h1>
        <div className="meta"><span>Lecture : 4 min</span><span>Novembre 2026</span></div>

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
