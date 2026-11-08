// Pages piliers locales du .fr : /agence-seo-local-yvelines/ et /agence-seo-local-eure-et-loir/.
// Chaque page a son propre angle éditorial (pas un simple remplacement de noms de villes).
// Aucune donnée économique, statistique ou référence client n'est inventée : les constats
// décrits sont des situations courantes, formulées comme telles.

export type Hub = {
  slug: string              // chemin : /<slug>/
  dept: 'yvelines' | 'eure-et-loir'
  region: string            // libellé « Yvelines (78) »
  title: string
  description: string
  keyword: string           // mot-clé principal (documentation)
  h1: string
  lead: string
  enBref: string            // réponse directe 40-80 mots
  presentation: string[]
  problems: [string, string][]
  site: string
  gbp: string
  seo: string
  ia: string
  reception: string
  method: string            // angle local de la méthode (le détail est sur /methode/)
  cities: { name: string; slug?: string; note: string }[]
  faqs: [string, string][]
  guides: string[]          // slugs de guides métier
}

export const HUB_UPDATED = '2026-11-08'

export const HUBS: Hub[] = [
  {
    slug: 'agence-seo-local-yvelines',
    dept: 'yvelines',
    region: 'Yvelines (78)',
    title: 'SEO local et création de sites dans les Yvelines (78) | Pulse Locale PME',
    description: 'Site internet, fiche Google et SEO local pour artisans, commerçants et TPE des Yvelines : Versailles, Saint-Quentin, Poissy, Mantes. Dès 49 € HT/mois.',
    keyword: 'SEO local Yvelines',
    h1: 'Développez votre visibilité sur Google dans les Yvelines',
    lead: 'Artisans, commerçants et petites entreprises du 78 : on crée votre site, on règle votre fiche Google et on répond aux appels que vous manquez, pour que les clients de votre secteur vous trouvent et vous joignent.',
    enBref: 'Pulse Locale PME accompagne les artisans, commerçants et TPE des Yvelines (Versailles, Saint-Quentin-en-Yvelines, Trappes, Poissy, Mantes-la-Jolie, Rambouillet) : création de site internet, optimisation de la fiche Google Business Profile, référencement local, visibilité dans les assistants IA et réceptionniste IA. Abonnement dès 49 € HT par mois, sans engagement, avec une démonstration gratuite avant tout paiement.',
    presentation: [
      'Dans les Yvelines, une même recherche ne donne pas les mêmes résultats à Versailles, à Montigny-le-Bretonneux ou à Rambouillet. Google affiche d’abord les entreprises proches, pertinentes et reconnues : votre visibilité se joue donc commune par commune, pas à l’échelle du département.',
      'Pulse Locale PME s’occupe de la partie technique et éditoriale (site, fiche Google, contenus, suivi des demandes) pour que vous restiez sur vos chantiers ou dans votre commerce. Tout se fait à distance, depuis votre espace client : nous n’avons pas de bureau dans le 78 et nous ne le prétendons pas.',
    ],
    problems: [
      ['Visible à côté de chez soi, invisible à 5 km', 'Un artisan installé à Trappes peut ressortir dans sa commune mais pas à Élancourt ou Guyancourt, faute de zone d’intervention déclarée et de contenus qui citent ces communes.'],
      ['Une concurrence dense dans les pôles', 'À Versailles ou à Saint-Germain-en-Laye, des dizaines de fiches se disputent les trois premières places de la carte : catégories approximatives et photos anciennes suffisent à décrocher.'],
      ['Des appels manqués pendant le travail', 'Sur un chantier ou en plein service, le téléphone sonne dans le vide. Le client rappelle rarement : il passe à la fiche suivante.'],
      ['Des informations différentes partout', 'Ancien numéro sur un annuaire, horaires périmés sur la fiche, adresse différente sur le site : ces incohérences brouillent Google comme les assistants IA.'],
    ],
    site: 'Un site vitrine rapide, lisible sur mobile, qui présente clairement vos services, vos communes d’intervention, vos horaires et un bouton d’appel. Il reprend exactement les mêmes nom, adresse et téléphone que votre fiche Google. La formule Starter inclut le site, l’hébergement, le certificat SSL et la maintenance, sans frais de création.',
    gbp: 'Catégorie principale la plus précise possible, catégories secondaires réellement exercées, zone d’intervention réaliste (Google demande de ne pas dépasser environ deux heures de route depuis votre base), services décrits, photos récentes, horaires spéciaux à jour et réponses aux avis. Disponible en pack unique à 149 € HT ou inclus et suivi chaque mois dans la formule Pro.',
    seo: 'Une page par service important, des contenus qui citent naturellement les communes où vous intervenez réellement, un maillage clair entre vos pages et des données structurées conformes au contenu visible. L’objectif : que Google comprenne qui vous êtes, ce que vous faites et où, sans bourrage de mots-clés.',
    ia: 'ChatGPT, Gemini, Perplexity ou les aperçus IA de Google s’appuient sur des pages indexées et sur des informations cohérentes d’une source à l’autre. On rend vos informations claires et citables (réponses directes, FAQ, données structurées), sans pouvoir garantir qu’un assistant vous recommandera : personne ne peut le garantir.',
    reception: 'Quand vous ne pouvez pas décrocher, l’appel est renvoyé vers votre réceptionniste IA. Elle répond au nom de votre entreprise, demande la commune, le besoin et l’urgence, puis vous envoie un résumé par WhatsApp ou SMS. Avec le Pack Connecté, elle peut proposer un créneau libre de votre Google Agenda.',
    method: 'Pour une entreprise des Yvelines, le diagnostic commence par les communes où vous voulez réellement travailler : on regarde qui sort sur la carte dans chacune, puis on priorise les réglages qui vous manquent.',
    cities: [
      { name: 'Versailles', slug: 'versailles', note: 'Concurrence forte en centre-ville, recherches par quartier.' },
      { name: 'Montigny-le-Bretonneux', note: 'Commune centrale de Saint-Quentin-en-Yvelines, couverte depuis la page de l’agglomération.' },
      { name: 'Saint-Quentin-en-Yvelines', slug: 'saint-quentin-en-yvelines', note: 'Recherches par commune de l’agglomération plutôt que « SQY ».' },
      { name: 'Trappes', note: 'Desservie dans le cadre de Saint-Quentin-en-Yvelines.' },
      { name: 'Rambouillet', slug: 'rambouillet', note: 'Communes étendues : la zone d’intervention est décisive.' },
      { name: 'Poissy', slug: 'poissy', note: 'Bassin de la boucle de Seine, beaucoup de recherches pratiques.' },
      { name: 'Mantes-la-Jolie', slug: 'mantes-la-jolie', note: 'Marché à l’échelle du Mantois.' },
      { name: 'Saint-Germain-en-Laye', slug: 'saint-germain-en-laye', note: 'Clientèle attentive aux avis et aux photos.' },
    ],
    faqs: [
      ['Comment être visible sur Google Maps dans les Yvelines ?', 'Revendiquez et complétez votre fiche Google Business Profile (catégorie précise, services, horaires, photos), déclarez une zone d’intervention réaliste si vous vous déplacez, demandez un avis à chaque client satisfait et gardez les mêmes nom, adresse et téléphone sur votre site et vos annuaires. Google classe les résultats locaux selon la pertinence, la distance et la notoriété.'],
      ['Faut-il un bureau dans les Yvelines pour travailler avec vous ?', 'Non. Tout se fait à distance : échanges par téléphone ou formulaire, validation des contenus et suivi depuis votre espace client.'],
      ['Mon entreprise est à Trappes : puis-je être trouvé à Montigny ou Élancourt ?', 'Si vous intervenez chez vos clients, oui : déclarez ces communes dans votre zone d’intervention et présentez-les sur votre site. Si vous recevez vos clients sur place, c’est surtout la proximité qui joue, la qualité de la fiche et les avis faisant la différence.'],
      ['Combien de temps avant de voir des résultats ?', 'Les corrections de fiche sont prises en compte en quelques jours à quelques semaines. La progression dans le classement dépend ensuite de la concurrence locale et du rythme des avis : comptez plutôt en mois. Nous ne promettons aucune position.'],
      ['Peut-on tester avant de payer ?', 'Oui : le test de visibilité est gratuit, la démonstration de votre site est offerte avant tout paiement et la réceptionniste IA s’essaie 30 jours dans la limite de 60 appels.'],
    ],
    guides: ['plombier', 'electricien', 'artisan-renovation', 'coiffeur', 'restaurant'],
  },
  {
    slug: 'agence-seo-local-eure-et-loir',
    dept: 'eure-et-loir',
    region: 'Eure-et-Loir (28)',
    title: 'SEO local et création de sites en Eure-et-Loir (28) | Pulse Locale PME',
    description: 'Site internet, fiche Google et SEO local pour artisans, commerces et TPE d’Eure-et-Loir : Chartres, Dreux, Lucé, Châteaudun, Nogent-le-Rotrou. Dès 49 € HT/mois.',
    keyword: 'SEO local Eure-et-Loir',
    h1: 'Attirez plus de clients locaux à Chartres, Dreux et en Eure-et-Loir',
    lead: 'De l’agglomération chartraine au Perche, en passant par le Drouais et la Beauce : on rend votre entreprise visible sur Google et joignable, y compris dans les communes rurales que vous desservez.',
    enBref: 'Pulse Locale PME aide les artisans, commerçants et TPE d’Eure-et-Loir (Chartres, Lucé, Mainvilliers, Dreux, Châteaudun, Nogent-le-Rotrou) à être trouvés sur Google Maps et dans les assistants IA : site internet, fiche Google Business Profile optimisée, référencement local et réceptionniste IA pour les appels manqués. Dès 49 € HT par mois, sans engagement, démonstration gratuite avant paiement.',
    presentation: [
      'L’Eure-et-Loir combine une agglomération (Chartres et ses communes voisines), quelques villes moyennes et un vaste territoire rural. Pour beaucoup d’artisans, le vrai sujet n’est pas d’être premier à Chartres, mais d’apparaître dans les villages qu’ils parcourent chaque semaine.',
      'Pulse Locale PME travaille à distance, depuis votre espace client. Nous n’avons pas d’agence dans le 28 : nous déclarons les zones que nous desservons, sans adresse locale fictive.',
    ],
    problems: [
      ['Des communes rurales mal couvertes', 'Sans zone d’intervention déclarée, un chauffagiste installé à Lucé peut rester invisible pour un client de la Beauce à quelques kilomètres.'],
      ['Des fiches Google incomplètes ou jamais revendiquées', 'Dans les secteurs moins denses, de nombreuses fiches restent incomplètes. C’est une opportunité pour celles qui sont bien tenues.'],
      ['Un téléphone difficile à décrocher sur la route', 'Entre deux interventions éloignées, beaucoup d’appels arrivent quand vous conduisez ou travaillez.'],
      ['Une clientèle mixte habitants / visiteurs', 'Autour de Chartres ou dans le Perche, restaurants et hébergements doivent convaincre des visiteurs qui comparent photos et avis avant de réserver.'],
    ],
    site: 'Un site simple et rapide qui liste vos services, les communes et cantons que vous couvrez, vos horaires et un bouton d’appel visible. Pour les hébergements et restaurants, il permet aussi un contact direct, sans dépendre uniquement des plateformes. Inclus dans la formule Starter à 49 € HT par mois, sans frais de création.',
    gbp: 'Revendication et vérification de la fiche si nécessaire, catégorie principale précise, zone d’intervention réaliste couvrant les villages réellement desservis, services, photos de vos chantiers ou de votre établissement, horaires de saison et réponses aux avis. Pack unique à 149 € HT ou suivi mensuel dans la formule Pro.',
    seo: 'Des pages de services claires, la mention naturelle des communes et secteurs desservis (agglomération chartraine, Drouais, Dunois, Perche), et des informations identiques sur la fiche, le site et les annuaires. Dans les zones peu concurrentielles, ces fondamentaux suffisent souvent à faire la différence.',
    ia: 'Les assistants IA reprennent des informations claires, cohérentes et indexées. Une page qui répond simplement à « qui intervient à Dreux pour… » a plus de chances d’être comprise et citée. Aucune citation n’est garantie, mais une information confuse ou contradictoire réduit nettement ces chances.',
    reception: 'Sur la route entre deux villages, la réceptionniste IA prend l’appel à votre place : elle note la commune, le besoin, l’urgence et le créneau souhaité, puis vous envoie un résumé. Vous organisez vos tournées sans perdre de demandes.',
    method: 'Pour une entreprise d’Eure-et-Loir, on part de votre rayon d’intervention réel : on vérifie votre visibilité dans les communes clés de ce rayon (pas seulement à Chartres), puis on corrige d’abord la fiche Google et la zone desservie.',
    cities: [
      { name: 'Chartres', slug: 'chartres', note: 'Agglomération, tourisme autour de la cathédrale.' },
      { name: 'Lucé', note: 'Desservie avec l’agglomération chartraine.' },
      { name: 'Mainvilliers', note: 'Desservie avec l’agglomération chartraine.' },
      { name: 'Dreux', slug: 'dreux', note: 'Drouais, clientèle aussi côté Eure.' },
      { name: 'Châteaudun', slug: 'chateaudun', note: 'Dunois et Beauce, longues distances.' },
      { name: 'Nogent-le-Rotrou', slug: 'nogent-le-rotrou', note: 'Perche, habitants et visiteurs de week-end.' },
    ],
    faqs: [
      ['Peut-on travailler avec Pulse Locale PME depuis Chartres ?', 'Oui. Tout se fait à distance : vous échangez avec nous par téléphone ou formulaire et suivez l’avancement depuis votre espace client. Aucun déplacement n’est nécessaire.'],
      ['Comment être visible dans les villages autour de Chartres ?', 'Si vous vous déplacez chez vos clients, masquez votre adresse si besoin, déclarez les communes réellement desservies dans votre zone d’intervention, citez-les sur votre site et demandez des avis aux clients de ces communes.'],
      ['Mon entreprise est à Dreux, puis-je être trouvée dans l’Eure voisine ?', 'Oui si vous y intervenez : Google raisonne en distance, pas en limites départementales. Déclarez simplement les communes réellement couvertes.'],
      ['Faut-il un abonnement pour optimiser sa fiche Google ?', 'Non. Le pack Fiche Google optimisée est vendu 149 € HT, une seule fois. L’abonnement Pro ajoute le suivi mensuel, le SEO local et le site.'],
      ['La réceptionniste IA fonctionne-t-elle avec mon numéro actuel ?', 'Oui, via un renvoi d’appel quand vous ne décrochez pas. Votre numéro ne change pas et vous pouvez désactiver le renvoi à tout moment.'],
    ],
    guides: ['chauffagiste', 'plombier', 'garage', 'boulangerie', 'hebergement'],
  },
]

export const hubBySlug = (slug: string) => HUBS.find((h) => h.slug === slug)
export const hubByDept = (dept: string) => HUBS.find((h) => h.dept === dept)
export const hubPath = (h: Hub) => `/${h.slug}/`
