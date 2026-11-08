// Pages locales : une page par département et une page par ville, rendues par
// app/zones/[dept]/page.tsx et app/zones/[dept]/[ville]/page.tsx.
// Chaque ville a son propre texte (contexte, communes voisines, recherches, FAQ) pour éviter
// les pages satellites dupliquées. Pulse Locale PME travaille à distance : on ne revendique
// aucune adresse locale, on déclare seulement les zones desservies (areaServed).

export type City = {
  slug: string
  name: string
  title: string             // ≤ 62 caractères
  description: string       // ≤ 160 caractères
  h1: string
  enBref: string            // réponse directe (AEO / GEO)
  context: string[]         // paragraphes propres à la ville
  communes: string[]        // zones desservies déclarées autour de la ville
  searches: string[]        // recherches locales typiques
  metiers: string[]         // slugs de guides métier à mettre en avant
  reception: string         // la réceptionniste IA vue depuis cette ville
  faqs: [string, string][]
}

export type Dept = {
  slug: string
  name: string
  code: string
  title: string
  description: string
  h1: string
  lead: string
  enBref: string
  context: string[]
  metiers: string[]
  faqs: [string, string][]
  cities: City[]
}

export const ZONES_UPDATED = '2026-11-08'

export const DEPTS: Dept[] = [
  {
    slug: 'yvelines',
    name: 'Yvelines',
    code: '78',
    title: 'Fiche Google, site et réceptionniste IA dans les Yvelines (78)',
    description: 'Artisans et commerces des Yvelines : site, fiche Google optimisée et réceptionniste IA qui répond aux appels manqués. Dès 49 € HT/mois, sans engagement.',
    h1: 'Être trouvé sur Google Maps dans les Yvelines, et ne plus perdre un appel.',
    lead: 'De Versailles à Mantes-la-Jolie, de Poissy à Rambouillet : vos clients cherchent sur Google Maps et demandent à ChatGPT. On rend votre entreprise visible et joignable, commune par commune.',
    enBref: 'Pulse Locale PME aide les artisans, commerçants et TPE des Yvelines (78) à apparaître dans les premiers résultats de Google Maps et dans les réponses des assistants IA : fiche Google optimisée, site internet, avis clients et réceptionniste IA qui répond aux appels manqués. Abonnement dès 49 € HT par mois, sans engagement, tout se fait en ligne.',
    context: [
      'Les Yvelines mélangent des pôles très denses (Versailles, Saint-Quentin-en-Yvelines, la vallée de la Seine) et de grands secteurs plus ruraux (forêt de Rambouillet, plaine de Versailles, Vexin). Pour un artisan, cela change tout : dans les villes, la concurrence sur Google Maps se joue à quelques centaines de mètres ; dans le sud et l’ouest du département, c’est votre zone d’intervention qui doit être bien déclarée pour remonter dans les communes voisines.',
      'Vos clients ne cherchent presque jamais « Yvelines ». Ils tapent le nom de leur commune, voire de leur quartier : « plombier Montigny-le-Bretonneux », « coiffeur Le Chesnay », « garage Mantes-la-Ville ». Votre fiche Google, votre site et vos avis doivent donc parler de ces communes-là, avec des informations identiques partout.',
    ],
    metiers: ['plombier', 'electricien', 'artisan-renovation', 'coiffeur', 'restaurant', 'garage'],
    faqs: [
      ['Faut-il une adresse dans les Yvelines pour être bien classé sur Google Maps ?', 'Google classe surtout selon la proximité du client, la pertinence de la fiche et sa notoriété (avis). Une entreprise qui intervient chez ses clients peut masquer son adresse et déclarer une zone d’intervention : elle remonte alors dans les communes desservies, à condition que la fiche soit complète et active.'],
      ['Intervenez-vous dans tout le département 78 ?', 'Oui. Tout se fait en ligne : création du site, optimisation de la fiche Google, demandes d’avis et réceptionniste IA. Vous suivez tout depuis votre espace client, sans rendez-vous en agence.'],
      ['Combien coûte l’accompagnement pour une entreprise des Yvelines ?', 'Les tarifs sont les mêmes partout : Starter à 49 € HT par mois, Pro à 149 € HT avec l’optimisation de la fiche Google et le SEO local, Élite à 299 € HT avec la réceptionniste IA incluse. Sans engagement, ou 2 mois offerts en annuel.'],
      ['La réceptionniste IA garde-t-elle mon numéro ?', 'Oui. Vous activez simplement le renvoi d’appel de votre ligne quand vous ne décrochez pas. Le client appelle votre numéro habituel, la réceptionniste répond, note la demande et vous envoie un résumé par WhatsApp ou SMS.'],
    ],
    cities: [
      {
        slug: 'versailles',
        name: 'Versailles',
        title: 'Fiche Google et réceptionniste IA à Versailles (78000)',
        description: 'Restaurants, commerces et artisans de Versailles : sortez en premier sur Google Maps quartier par quartier et ne ratez plus un appel avec l’IA.',
        h1: 'Versailles : sortir en premier sur Google Maps, quartier par quartier.',
        enBref: 'À Versailles, la concurrence sur Google Maps se joue à l’échelle du quartier (Notre-Dame, Saint-Louis, Chantiers, Montreuil, Porchefontaine). Pulse Locale PME optimise votre fiche Google, votre site et vos avis pour ces recherches, et sa réceptionniste IA répond aux appels que vous manquez. Dès 49 € HT par mois.',
        context: [
          'Ville préfecture et très touristique, Versailles concentre une forte densité de restaurants, d’hébergements, de commerces de bouche et d’instituts. Sur une recherche comme « restaurant Versailles », des dizaines de fiches se disputent les trois premières places de la carte : la différence se fait sur les catégories, les photos récentes, les horaires exacts et le nombre d’avis récents.',
          'Pour les artisans, la ville sert souvent de point de départ vers tout le secteur de Versailles Grand Parc. Bien déclarer les communes voisines dans votre zone d’intervention permet d’être proposé au Chesnay-Rocquencourt ou à Viroflay, pas seulement en centre-ville.',
        ],
        communes: ['Versailles', 'Le Chesnay-Rocquencourt', 'Viroflay', 'Vélizy-Villacoublay', 'Buc', 'Jouy-en-Josas', 'Bailly', 'Noisy-le-Roi', 'Saint-Cyr-l’École', 'Fontenay-le-Fleury'],
        searches: ['restaurant Versailles ouvert maintenant', 'plombier Versailles urgence', 'coiffeur quartier Saint-Louis Versailles', 'chambre d’hôtes Versailles', 'électricien Le Chesnay'],
        metiers: ['restaurant', 'hebergement', 'coiffeur', 'plombier'],
        reception: 'Pendant le service ou en plein chantier, vous ne pouvez pas décrocher. À Versailles, un client qui tombe sur une messagerie rappelle simplement la fiche suivante sur la carte. La réceptionniste IA prend l’appel, répond aux questions simples (horaires, accès, disponibilités), note le nom, le besoin et le créneau souhaité, puis vous envoie le résumé. Avec le Pack Connecté, elle peut même proposer un créneau libre de votre Google Agenda.',
        faqs: [
          ['Comment apparaître dans « restaurant Versailles » alors qu’il y a tant de concurrence ?', 'Choisissez la catégorie la plus précise (par exemple « Restaurant français » plutôt que « Restaurant »), publiez des photos récentes de la salle et des plats, gardez des horaires exacts (y compris jours fériés) et demandez un avis à chaque table satisfaite. Les fiches complètes et actives passent devant.'],
          ['Mon entreprise est à Versailles, puis-je être trouvé au Chesnay ou à Vélizy ?', 'Oui, si vous intervenez chez vos clients : déclarez ces communes dans votre zone d’intervention et citez-les sur votre site. Pour un commerce avec accueil sur place, c’est la proximité qui joue : les avis et la qualité de la fiche font la différence.'],
          ['La réceptionniste IA peut-elle répondre pendant le coup de feu ?', 'Oui. Elle répond quand vous ne décrochez pas, note la demande (réservation, question, rappel) et vous envoie un résumé par WhatsApp ou SMS pour que vous rappeliez au calme.'],
          ['Combien de temps pour voir un effet sur Google Maps à Versailles ?', 'Les corrections de fiche (catégories, horaires, services) sont prises en compte en quelques jours à quelques semaines. Le gain de position dépend ensuite de la concurrence et du rythme des avis : comptez plutôt en mois qu’en semaines sur les recherches les plus disputées.'],
        ],
      },
      {
        slug: 'saint-quentin-en-yvelines',
        name: 'Saint-Quentin-en-Yvelines',
        title: 'Fiche Google et réceptionniste IA à Saint-Quentin-en-Yvelines',
        description: 'Montigny, Guyancourt, Élancourt, Trappes, Plaisir… Soyez trouvé commune par commune sur Google Maps et répondez à chaque appel avec la réceptionniste IA.',
        h1: 'Saint-Quentin-en-Yvelines : être trouvé dans chaque commune de l’agglo.',
        enBref: 'À Saint-Quentin-en-Yvelines, les clients cherchent par commune (Montigny-le-Bretonneux, Guyancourt, Élancourt, Trappes, Plaisir…), pas par « SQY ». Pulse Locale PME déclare vos vraies zones d’intervention, optimise votre fiche Google et répond à vos appels manqués avec la réceptionniste IA. Dès 49 € HT par mois.',
        context: [
          'Saint-Quentin-en-Yvelines est une agglomération de plusieurs communes, avec de grandes zones d’activités et beaucoup de familles. Les recherches sont très locales : un habitant de Voisins-le-Bretonneux cherche « électricien Voisins » ou « électricien près de moi », et Google lui propose d’abord les fiches proches qui couvrent sa commune.',
          'C’est aussi un secteur où les clients appellent en journée depuis le bureau, souvent entre deux réunions. S’ils ne vous joignent pas tout de suite, ils passent au suivant : être joignable compte autant que bien sortir sur la carte.',
        ],
        communes: ['Montigny-le-Bretonneux', 'Guyancourt', 'Élancourt', 'Trappes', 'Voisins-le-Bretonneux', 'Plaisir', 'Maurepas', 'La Verrière', 'Coignières', 'Magny-les-Hameaux', 'Les Clayes-sous-Bois', 'Villepreux'],
        searches: ['plombier Montigny-le-Bretonneux', 'garage Guyancourt', 'coiffeur Plaisir', 'électricien Élancourt', 'esthéticienne Voisins-le-Bretonneux'],
        metiers: ['electricien', 'plombier', 'garage', 'estheticienne'],
        reception: 'Vos clients de l’agglo appellent souvent à l’heure du déjeuner ou en fin de journée, exactement quand vous êtes occupé. La réceptionniste IA décroche à votre place, demande la commune, le besoin et le meilleur moment pour rappeler, puis vous envoie un résumé clair. Vous rappelez les bons contacts en priorité, sans écouter de messagerie.',
        faqs: [
          ['Dois-je créer une fiche Google par commune de Saint-Quentin-en-Yvelines ?', 'Non. Une fiche Google correspond à un établissement réel. Si vous intervenez dans plusieurs communes, déclarez-les dans votre zone d’intervention et présentez-les sur votre site. Créer des fiches sans établissement réel est contraire aux règles de Google et peut entraîner une suspension.'],
          ['Pourquoi mon concurrent sort-il à Guyancourt et pas moi ?', 'Le plus souvent : une catégorie principale plus précise, une zone d’intervention bien déclarée, plus d’avis récents et des réponses à ces avis. Notre test gratuit compare votre fiche à ces critères en 8 questions.'],
          ['La réceptionniste IA prend-elle les messages WhatsApp ?', 'Oui. Elle répond aux appels manqués et aux messages WhatsApp au nom de votre entreprise, qualifie la demande et vous transmet un résumé.'],
          ['Proposez-vous un engagement de durée ?', 'Non, l’abonnement mensuel est sans engagement. L’annuel offre 2 mois (10 mois facturés pour 12).'],
        ],
      },
      {
        slug: 'saint-germain-en-laye',
        name: 'Saint-Germain-en-Laye',
        title: 'Fiche Google et réceptionniste IA à Saint-Germain-en-Laye',
        description: 'Commerces et artisans de Saint-Germain-en-Laye, du Pecq et du Vésinet : une fiche Google qui inspire confiance, des avis réguliers et zéro appel manqué.',
        h1: 'Saint-Germain-en-Laye : une fiche Google à la hauteur d’une clientèle exigeante.',
        enBref: 'À Saint-Germain-en-Laye, les clients comparent les avis et les photos avant d’appeler. Pulse Locale PME soigne votre fiche Google, votre site et vos avis, déclare vos zones (Le Pecq, Le Vésinet, Chambourcy, Marly-le-Roi…) et répond à vos appels manqués avec la réceptionniste IA. Dès 49 € HT par mois.',
        context: [
          'Le centre-ville de Saint-Germain-en-Laye concentre de nombreux commerces indépendants, instituts, restaurants et professions de santé. La clientèle lit les avis en détail : une note correcte ne suffit pas, ce sont les avis récents, précis et les réponses du professionnel qui déclenchent l’appel.',
          'Autour, Le Pecq, Le Vésinet, Chambourcy ou Mareil-Marly forment un bassin résidentiel où les artisans interviennent beaucoup à domicile. Pour eux, une zone d’intervention bien réglée et des photos de chantiers réels font la différence face aux plateformes de mise en relation.',
        ],
        communes: ['Saint-Germain-en-Laye', 'Le Pecq', 'Le Vésinet', 'Chambourcy', 'Mareil-Marly', 'Marly-le-Roi', 'Croissy-sur-Seine', 'Aigremont', 'L’Étang-la-Ville', 'Montesson'],
        searches: ['institut de beauté Saint-Germain-en-Laye', 'serrurier Le Vésinet', 'restaurant Saint-Germain-en-Laye terrasse', 'agence immobilière Le Pecq', 'chauffagiste Saint-Germain-en-Laye entretien'],
        metiers: ['estheticienne', 'agence-immobiliere', 'serrurier', 'chauffagiste'],
        reception: 'Une cliente qui veut réserver un soin ou un artisan qu’on appelle pour un devis : si personne ne répond, la demande part ailleurs. La réceptionniste IA répond poliment au nom de votre entreprise, prend les coordonnées et le besoin, et vous envoie le résumé. Votre image reste soignée, même quand vous êtes indisponible.',
        faqs: [
          ['Comment répondre aux avis pour rassurer la clientèle de Saint-Germain-en-Laye ?', 'Répondez à chaque avis, en remerciant précisément (la prestation, le prénom du collaborateur) et, pour un avis négatif, en proposant une solution sans polémique. Les réponses sont lues autant que les avis eux-mêmes.'],
          ['Je suis artisan au Pecq, puis-je être visible à Saint-Germain-en-Laye ?', 'Oui : masquez votre adresse si vous ne recevez pas de clients, déclarez Saint-Germain-en-Laye et les communes voisines dans votre zone d’intervention et montrez vos chantiers réalisés dans ces communes.'],
          ['La réceptionniste IA parle-t-elle comme mon entreprise ?', 'Vous réglez son message d’accueil, les questions à poser et les informations à donner depuis votre espace client. Elle se présente comme l’assistante virtuelle de votre entreprise.'],
          ['Que se passe-t-il après les 30 jours d’essai ?', 'L’essai de la réceptionniste IA couvre 30 jours dans la limite de 60 appels. Ensuite, elle est à 39 € HT par mois avec 100 appels inclus, ou incluse dans la formule Élite.'],
        ],
      },
      {
        slug: 'poissy',
        name: 'Poissy',
        title: 'Fiche Google et réceptionniste IA à Poissy (78300)',
        description: 'Artisans, garages et commerces de Poissy et de la boucle de Seine : sortez sur Google Maps à Carrières, Villennes, Orgeval et répondez à tous vos appels.',
        h1: 'Poissy : être l’artisan ou le commerce qu’on trouve en premier en bord de Seine.',
        enBref: 'À Poissy, beaucoup de clients viennent des communes voisines (Carrières-sous-Poissy, Villennes-sur-Seine, Orgeval, Achères). Pulse Locale PME règle votre fiche Google et votre site pour ces communes, fait monter vos avis et répond à vos appels manqués avec la réceptionniste IA. Dès 49 € HT par mois.',
        context: [
          'Ville industrielle et commerçante, Poissy attire une clientèle qui vient de toute la boucle de Seine. Les garages, artisans du bâtiment et services à domicile y travaillent sur un rayon large : la fiche Google doit le dire clairement, avec les communes réellement couvertes.',
          'Les recherches y sont très pratiques : « garage ouvert samedi », « plombier disponible aujourd’hui », « boulangerie ouverte dimanche ». Des horaires exacts et un téléphone qui répond valent souvent mieux qu’une belle vitrine.',
        ],
        communes: ['Poissy', 'Carrières-sous-Poissy', 'Villennes-sur-Seine', 'Orgeval', 'Achères', 'Médan', 'Vernouillet', 'Chambourcy', 'Andrésy', 'Triel-sur-Seine'],
        searches: ['garage Poissy ouvert samedi', 'plombier Carrières-sous-Poissy', 'boulangerie Poissy dimanche', 'électricien Villennes-sur-Seine', 'taxi Poissy gare'],
        metiers: ['garage', 'plombier', 'boulangerie', 'taxi-vtc'],
        reception: 'Sous une voiture ou sur un chantier, impossible de décrocher. La réceptionniste IA répond à votre place, demande le véhicule ou le type de panne, la commune et l’urgence, puis vous envoie un résumé exploitable. Vous rappelez d’abord les demandes urgentes, et plus aucun client ne part chez le concurrent faute de réponse.',
        faqs: [
          ['Comment être visible à Carrières-sous-Poissy si mon garage est à Poissy ?', 'Pour un établissement qui reçoit ses clients, Google privilégie la proximité, mais une fiche très complète (services détaillés, photos, avis nombreux et récents) peut ressortir au-delà de la commune. Citez aussi les communes voisines sur votre site.'],
          ['Les horaires jouent-ils vraiment sur Google Maps ?', 'Oui : Google met en avant les établissements ouverts au moment de la recherche, et un client qui trouve porte close laisse souvent un mauvais avis. Tenez à jour les horaires spéciaux (jours fériés, congés).'],
          ['La réceptionniste IA peut-elle filtrer les urgences ?', 'Elle demande systématiquement la nature et l’urgence de la demande, et vous la signale dans le résumé envoyé par WhatsApp ou SMS.'],
          ['Faut-il un site internet en plus de la fiche Google ?', 'Ce n’est pas obligatoire, mais un site cohérent avec la fiche (mêmes nom, adresse, téléphone, services) renforce la confiance de Google et des assistants IA. La formule Starter inclut un site vitrine dès 49 € HT par mois.'],
        ],
      },
      {
        slug: 'mantes-la-jolie',
        name: 'Mantes-la-Jolie',
        title: 'Fiche Google et réceptionniste IA à Mantes-la-Jolie',
        description: 'Mantes-la-Jolie, Mantes-la-Ville, Buchelay, Limay : une fiche Google bien réglée, des avis réguliers et une réceptionniste IA pour ne plus rater de client.',
        h1: 'Mantes-la-Jolie : capter les clients du Mantois sur Google Maps.',
        enBref: 'Dans le Mantois, les clients cherchent dans tout le bassin (Mantes-la-Jolie, Mantes-la-Ville, Buchelay, Limay, Magnanville). Pulse Locale PME règle votre fiche Google et votre site pour ces communes, développe vos avis et répond à vos appels manqués avec la réceptionniste IA. Dès 49 € HT par mois.',
        context: [
          'Mantes-la-Jolie est le cœur commercial de l’ouest des Yvelines, avec une clientèle qui circule entre plusieurs communes très proches. Pour un commerçant ou un artisan, le vrai marché est le bassin du Mantois, pas la seule commune : c’est ce bassin qu’il faut couvrir sur la fiche et sur le site.',
          'Beaucoup d’entreprises du secteur ont encore une fiche Google incomplète ou non revendiquée. C’est une opportunité : une fiche complète, avec des photos réelles et des avis récents, peut prendre rapidement l’avantage sur des recherches comme « coiffeur Mantes » ou « garage Buchelay ».',
        ],
        communes: ['Mantes-la-Jolie', 'Mantes-la-Ville', 'Buchelay', 'Magnanville', 'Limay', 'Rosny-sur-Seine', 'Gargenville', 'Épône', 'Porcheville', 'Guerville'],
        searches: ['coiffeur Mantes-la-Jolie', 'garage Buchelay', 'plombier Mantes-la-Ville', 'restaurant Mantes-la-Jolie', 'ambulance Mantes-la-Jolie'],
        metiers: ['coiffeur', 'garage', 'ambulancier', 'restaurant'],
        reception: 'Quand le salon est plein ou que vous êtes en intervention, le téléphone sonne dans le vide. La réceptionniste IA décroche, répond aux questions courantes, prend la demande et le créneau souhaité, puis vous envoie tout par WhatsApp ou SMS. Vous ne perdez plus les clients qui n’aiment pas laisser de message.',
        faqs: [
          ['Ma fiche Google n’est pas revendiquée, est-ce grave ?', 'Oui : n’importe qui peut proposer des modifications (horaires, téléphone) et vous ne pouvez ni répondre aux avis ni publier. Revendiquer et vérifier la fiche est la première étape, nous vous guidons pour le faire.'],
          ['Comment obtenir plus d’avis à Mantes-la-Jolie ?', 'Demandez l’avis au bon moment (juste après la prestation), avec un lien direct ou un QR code au comptoir. Le Pack 50 avis (99 € HT) automatise les demandes par SMS.'],
          ['Peut-on tester sans payer ?', 'Oui : le test de visibilité est gratuit, la démonstration du site est offerte avant tout paiement et la réceptionniste IA s’essaie 30 jours (60 appels).'],
          ['Travaillez-vous avec les ambulanciers et taxis du Mantois ?', 'Oui, nous avons un guide dédié à chaque métier. Pour ces activités, être joignable 24 h/24 compte autant que la position sur Google Maps : la réceptionniste IA prend les appels que vous ne pouvez pas prendre en course.'],
        ],
      },
      {
        slug: 'rambouillet',
        name: 'Rambouillet',
        title: 'Fiche Google et réceptionniste IA à Rambouillet (78120)',
        description: 'Artisans et commerces de Rambouillet et du sud Yvelines : la bonne zone sur Google Maps et une réceptionniste IA qui répond à chaque appel.',
        h1: 'Rambouillet et le sud Yvelines : être trouvé dans toutes les communes que vous couvrez.',
        enBref: 'Autour de Rambouillet, les communes sont étendues et les artisans parcourent de longues distances. Pulse Locale PME déclare votre vraie zone d’intervention (Le Perray-en-Yvelines, Saint-Arnoult, Ablis, Les Essarts-le-Roi…), optimise votre fiche Google et répond à vos appels manqués avec la réceptionniste IA. Dès 49 € HT par mois.',
        context: [
          'Le sud des Yvelines est un territoire de villages et de forêt, avec Rambouillet comme centre de services. Les clients y cherchent « près de moi » depuis des communes éloignées les unes des autres : sans zone d’intervention bien déclarée, un artisan installé à Rambouillet peut être invisible à quelques kilomètres.',
          'Le tourisme vert (forêt, château, randonnées) fait aussi vivre gîtes, chambres d’hôtes et restaurants, pour qui les photos, les horaires de saison et les avis récents sont décisifs.',
        ],
        communes: ['Rambouillet', 'Le Perray-en-Yvelines', 'Les Essarts-le-Roi', 'Gazeran', 'Saint-Arnoult-en-Yvelines', 'Ablis', 'Vieille-Église-en-Yvelines', 'Auffargis', 'Sonchamp', 'Poigny-la-Forêt'],
        searches: ['chauffagiste Rambouillet', 'gîte forêt de Rambouillet', 'électricien Le Perray-en-Yvelines', 'garage Saint-Arnoult-en-Yvelines', 'restaurant Rambouillet'],
        metiers: ['chauffagiste', 'hebergement', 'electricien', 'artisan-renovation'],
        reception: 'Sur la route entre deux chantiers, vous ne pouvez pas répondre. La réceptionniste IA prend l’appel, demande la commune et la nature des travaux, et vous envoie un résumé : vous organisez vos tournées sans perdre les demandes. Avec le Pack Connecté, elle propose directement un créneau libre de votre Google Agenda.',
        faqs: [
          ['Quelle zone d’intervention déclarer autour de Rambouillet ?', 'Les communes que vous couvrez réellement, en restant raisonnable : Google indique que la zone ne doit pas dépasser environ deux heures de route depuis votre base. Mieux vaut une zone précise et crédible qu’un département entier.'],
          ['Un gîte près de Rambouillet a-t-il intérêt à avoir sa fiche Google ?', 'Oui : beaucoup de voyageurs réservent après avoir vu les photos et les avis sur Google Maps. Une fiche complète avec un lien de réservation directe limite la dépendance aux plateformes.'],
          ['La réceptionniste IA réserve-t-elle des rendez-vous ?', 'Avec le Pack Connecté (inclus dans Élite, offert pendant l’essai), elle consulte vos créneaux réellement libres dans Google Agenda, les propose au client et crée le rendez-vous.'],
          ['Faut-il se déplacer pour mettre tout ça en place ?', 'Non, tout se fait en ligne depuis votre espace client. Vous validez les contenus, nous nous occupons du reste.'],
        ],
      },
    ],
  },
  {
    slug: 'eure-et-loir',
    name: 'Eure-et-Loir',
    code: '28',
    title: 'Fiche Google, site et réceptionniste IA en Eure-et-Loir (28)',
    description: 'Artisans et commerces d’Eure-et-Loir : site, fiche Google optimisée et réceptionniste IA pour les appels manqués. Chartres, Dreux, Châteaudun, Nogent-le-Rotrou.',
    h1: 'Être trouvé sur Google Maps en Eure-et-Loir, et répondre à chaque client.',
    lead: 'De Chartres à Dreux, de la Beauce au Perche : vos clients cherchent sur Google Maps et posent leurs questions à ChatGPT. On rend votre entreprise visible et joignable dans toutes les communes que vous couvrez.',
    enBref: 'Pulse Locale PME aide les artisans, commerçants et TPE d’Eure-et-Loir (28) à apparaître dans Google Maps et dans les réponses des assistants IA : fiche Google optimisée, site internet, avis clients et réceptionniste IA qui répond aux appels manqués. Abonnement dès 49 € HT par mois, sans engagement, tout se fait en ligne.',
    context: [
      'L’Eure-et-Loir réunit quelques pôles urbains (Chartres, Dreux, Châteaudun, Nogent-le-Rotrou) et de très nombreuses communes rurales en Beauce et dans le Perche. Les artisans y couvrent souvent un large rayon : sur Google Maps, c’est la zone d’intervention déclarée et la qualité de la fiche qui décident s’ils apparaissent dans les villages voisins.',
      'Dans les secteurs moins denses, beaucoup de fiches Google sont incomplètes. Une fiche bien tenue, avec des photos réelles, des avis réguliers et un téléphone qui répond, prend vite l’avantage.',
    ],
    metiers: ['plombier', 'chauffagiste', 'artisan-renovation', 'garage', 'boulangerie', 'hebergement'],
    faqs: [
      ['Intervenez-vous dans tout l’Eure-et-Loir ?', 'Oui. Tout se fait en ligne : site, fiche Google, avis et réceptionniste IA. Vous suivez l’avancement depuis votre espace client, sans rendez-vous.'],
      ['Un artisan rural peut-il vraiment sortir sur Google Maps ?', 'Oui. Dans les zones peu denses, la concurrence est plus faible : une fiche complète, une zone d’intervention bien déclarée et des avis réguliers suffisent souvent à passer devant.'],
      ['Combien coûte l’accompagnement en Eure-et-Loir ?', 'Les mêmes tarifs partout : Starter 49 € HT par mois, Pro 149 € HT avec l’optimisation de la fiche Google et le SEO local, Élite 299 € HT avec la réceptionniste IA incluse. Sans engagement.'],
      ['La réceptionniste IA fonctionne-t-elle avec mon numéro actuel ?', 'Oui, via un simple renvoi d’appel quand vous ne décrochez pas. Votre numéro ne change pas.'],
    ],
    cities: [
      {
        slug: 'chartres',
        name: 'Chartres',
        title: 'Fiche Google et réceptionniste IA à Chartres (28000)',
        description: 'Commerces, restaurants et artisans de Chartres, Lucé, Mainvilliers : sortez en premier sur Google Maps et ne ratez plus un appel avec la réceptionniste IA.',
        h1: 'Chartres : sortir en premier sur Google Maps dans toute l’agglomération.',
        enBref: 'À Chartres, les clients cherchent dans toute l’agglomération (Lucé, Mainvilliers, Lèves, Luisant, Champhol). Pulse Locale PME optimise votre fiche Google et votre site pour ces communes, développe vos avis et répond à vos appels manqués avec la réceptionniste IA. Dès 49 € HT par mois.',
        context: [
          'Préfecture et ville touristique autour de sa cathédrale, Chartres concentre restaurants, hébergements, commerces et services. Les visiteurs cherchent « restaurant près de la cathédrale » ou « ouvert maintenant » : les fiches aux horaires exacts et aux photos récentes captent ces recherches.',
          'Pour les artisans, l’agglomération chartraine forme un seul marché. Déclarer Lucé, Mainvilliers ou Luisant dans votre zone d’intervention et y montrer vos chantiers vous rend visible bien au-delà du centre-ville.',
        ],
        communes: ['Chartres', 'Lucé', 'Mainvilliers', 'Lèves', 'Luisant', 'Champhol', 'Le Coudray', 'Saint-Prest', 'Gellainville', 'Barjouville'],
        searches: ['restaurant Chartres cathédrale', 'plombier Chartres urgence', 'coiffeur Lucé', 'chambre d’hôtes Chartres', 'électricien Mainvilliers'],
        metiers: ['restaurant', 'hebergement', 'plombier', 'coiffeur'],
        reception: 'Pendant le service ou sur un chantier, vous ne pouvez pas répondre, et le client appelle le suivant sur la carte. La réceptionniste IA décroche, répond aux questions simples, note la demande et le créneau souhaité, puis vous envoie le résumé par WhatsApp ou SMS.',
        faqs: [
          ['Comment apparaître dans « restaurant Chartres » face aux nombreux établissements du centre ?', 'Choisissez la catégorie la plus précise, publiez régulièrement des photos réelles, tenez vos horaires à jour et demandez un avis à chaque client satisfait. Répondre aux avis aide aussi à convaincre.'],
          ['Je suis à Lucé, puis-je être trouvé à Chartres ?', 'Si vous intervenez chez vos clients, oui : déclarez Chartres et les communes voisines dans votre zone d’intervention. Pour un commerce avec accueil, la proximité compte, mais une fiche très complète ressort plus loin.'],
          ['La réceptionniste IA prend-elle les réservations ?', 'Elle note la demande et le créneau souhaité. Avec le Pack Connecté, elle propose les créneaux libres de votre Google Agenda et crée le rendez-vous.'],
          ['Combien de temps pour voir des résultats ?', 'Les corrections de fiche sont prises en compte en quelques jours à quelques semaines ; la progression dans le classement dépend ensuite des avis et de la concurrence.'],
        ],
      },
      {
        slug: 'dreux',
        name: 'Dreux',
        title: 'Fiche Google et réceptionniste IA à Dreux (28100)',
        description: 'Artisans, garages et commerces de Dreux et Vernouillet : une fiche Google complète, des avis réguliers et une réceptionniste IA pour ne plus perdre d’appel.',
        h1: 'Dreux : capter les clients du Drouais sur Google Maps.',
        enBref: 'Autour de Dreux, le marché couvre tout le Drouais (Vernouillet, Chérisy, Luray, Sainte-Gemme-Moronval…), aux portes de la Normandie. Pulse Locale PME règle votre fiche Google et votre site pour ces communes, fait monter vos avis et répond à vos appels manqués avec la réceptionniste IA. Dès 49 € HT par mois.',
        context: [
          'Dreux est le pôle du nord de l’Eure-et-Loir, avec une clientèle qui vient aussi des communes voisines de l’Eure. Les recherches sont pratiques et urgentes : dépannage, garage, serrurier, boulangerie ouverte.',
          'Dans ces recherches, Google favorise les fiches ouvertes au moment de la recherche, bien notées et qui répondent. Une fiche à jour et un téléphone toujours joignable font la différence.',
        ],
        communes: ['Dreux', 'Vernouillet', 'Chérisy', 'Luray', 'Sainte-Gemme-Moronval', 'Garnay', 'Tréon', 'Saint-Rémy-sur-Avre', 'Anet', 'Nogent-le-Roi'],
        searches: ['garage Dreux', 'serrurier Dreux urgence', 'boulangerie Vernouillet', 'plombier Dreux', 'taxi Dreux gare'],
        metiers: ['garage', 'serrurier', 'boulangerie', 'taxi-vtc'],
        reception: 'En intervention, vous ratez des appels urgents. La réceptionniste IA répond à votre place, demande la commune, le problème et l’urgence, puis vous envoie un résumé : vous rappelez d’abord les urgences, et aucun client ne part faute de réponse.',
        faqs: [
          ['Puis-je être trouvé dans l’Eure voisine depuis Dreux ?', 'Si vous vous déplacez chez vos clients, déclarez les communes réellement couvertes, y compris de l’autre côté de la limite départementale. Google ne raisonne pas en départements mais en distance.'],
          ['Comment se démarquer en serrurerie, un métier où les clients se méfient ?', 'Avec la transparence : tarifs indicatifs sur le site, photos de votre véhicule et de vous, avis vérifiés et réponses à chaque avis. Notre guide serrurier détaille la méthode.'],
          ['La réceptionniste IA fonctionne-t-elle la nuit ?', 'Elle répond chaque fois que l’appel est renvoyé vers elle, y compris le soir et le week-end, et vous envoie le résumé pour que vous décidiez de rappeler.'],
          ['Y a-t-il un engagement ?', 'Non, le mensuel est sans engagement. L’annuel offre 2 mois.'],
        ],
      },
      {
        slug: 'chateaudun',
        name: 'Châteaudun',
        title: 'Fiche Google et réceptionniste IA à Châteaudun (28200)',
        description: 'Artisans et commerces de Châteaudun et du Dunois : la bonne zone sur Google Maps, des avis réguliers et une réceptionniste IA pour chaque appel.',
        h1: 'Châteaudun et le Dunois : être visible dans toutes les communes que vous couvrez.',
        enBref: 'Autour de Châteaudun, les communes sont dispersées en Beauce et le long du Loir. Pulse Locale PME déclare votre vraie zone d’intervention, optimise votre fiche Google et votre site, et répond à vos appels manqués avec la réceptionniste IA. Dès 49 € HT par mois.',
        context: [
          'Châteaudun est le centre de services du sud de l’Eure-et-Loir. Les clients y viennent de villages parfois éloignés : pour un artisan, la zone d’intervention déclarée sur Google est le réglage le plus important.',
          'Les recherches y sont souvent faites au téléphone, au dernier moment : « chauffagiste disponible », « garage ouvert ». Être joignable rapporte autant que d’être bien classé.',
        ],
        communes: ['Châteaudun', 'Saint-Denis-Lanneray', 'Jallans', 'Marboué', 'Donnemain-Saint-Mamès', 'La Chapelle-du-Noyer', 'Cloyes-les-Trois-Rivières', 'Bonneval', 'Logron', 'Varize'],
        searches: ['chauffagiste Châteaudun', 'garage Châteaudun', 'électricien Bonneval', 'boulangerie Châteaudun dimanche', 'couvreur Châteaudun'],
        metiers: ['chauffagiste', 'garage', 'electricien', 'artisan-renovation'],
        reception: 'Entre deux interventions à la campagne, le réseau ou le temps manquent pour répondre. La réceptionniste IA décroche, note la commune, le besoin et le créneau souhaité, puis vous envoie le résumé : vous organisez vos tournées sans perdre de clients.',
        faqs: [
          ['Dois-je afficher mon adresse si je travaille à domicile ?', 'Non : si vous ne recevez pas de clients, masquez l’adresse et déclarez une zone d’intervention. Google l’autorise et c’est même recommandé.'],
          ['Comment être trouvé à Bonneval ou Cloyes si je suis à Châteaudun ?', 'Déclarez ces communes dans votre zone d’intervention, citez-les sur votre site avec des exemples de chantiers et demandez des avis aux clients de ces communes.'],
          ['La réceptionniste IA parle-t-elle de mes tarifs ?', 'Elle donne les informations que vous avez renseignées dans vos réglages (tarifs indicatifs, zone, horaires) et ne s’engage jamais sur un devis à votre place.'],
          ['Peut-on tout faire à distance ?', 'Oui, depuis votre espace client. Vous validez les contenus, nous nous occupons du reste.'],
        ],
      },
      {
        slug: 'nogent-le-rotrou',
        name: 'Nogent-le-Rotrou',
        title: 'Fiche Google et réceptionniste IA à Nogent-le-Rotrou',
        description: 'Artisans, commerces et gîtes du Perche autour de Nogent-le-Rotrou : une fiche Google qui attire, des avis réguliers et zéro appel manqué grâce à l’IA.',
        h1: 'Nogent-le-Rotrou et le Perche : être trouvé par les habitants et les visiteurs.',
        enBref: 'Autour de Nogent-le-Rotrou, les clients sont à la fois des habitants du Perche et des visiteurs de week-end. Pulse Locale PME optimise votre fiche Google et votre site pour les deux, développe vos avis et répond à vos appels manqués avec la réceptionniste IA. Dès 49 € HT par mois.',
        context: [
          'Nogent-le-Rotrou est la ville principale du Perche d’Eure-et-Loir, aux confins de l’Orne et de la Sarthe. Les artisans y couvrent un territoire qui déborde des limites départementales, et les gîtes, chambres d’hôtes et restaurants vivent beaucoup du tourisme de week-end.',
          'Pour les visiteurs, les photos, les horaires de saison et les avis récents décident du choix. Pour les habitants, c’est la réactivité : un appel sans réponse est un client perdu.',
        ],
        communes: ['Nogent-le-Rotrou', 'Margon', 'Champrond-en-Perchet', 'Nogent-le-Bernard', 'Brunelles', 'Souancé-au-Perche', 'Trizay-Coutretot-Saint-Serge', 'Arcisses', 'Thiron-Gardais', 'La Loupe'],
        searches: ['gîte Perche Nogent-le-Rotrou', 'restaurant Nogent-le-Rotrou', 'plombier Nogent-le-Rotrou', 'menuisier Perche', 'garage Nogent-le-Rotrou'],
        metiers: ['hebergement', 'restaurant', 'plombier', 'artisan-renovation'],
        reception: 'Accueil des clients, ménage entre deux séjours ou chantier : vous ne pouvez pas toujours décrocher. La réceptionniste IA répond aux appels et aux messages WhatsApp, renseigne sur l’accès et les disponibilités, prend la demande et vous envoie un résumé.',
        faqs: [
          ['Un gîte du Perche a-t-il besoin d’un site en plus de Google ?', 'Un site simple avec vos photos, vos tarifs et un contact direct vous rend moins dépendant des plateformes. Relié à votre fiche Google, il aide aussi les assistants IA à vous recommander.'],
          ['Puis-je couvrir l’Orne et la Sarthe depuis Nogent-le-Rotrou ?', 'Oui, déclarez les communes réellement desservies, quel que soit le département. Google raisonne en distance, pas en limites administratives.'],
          ['La réceptionniste IA répond-elle sur WhatsApp ?', 'Oui, aux appels manqués et aux messages WhatsApp, au nom de votre établissement.'],
          ['Combien coûte la réceptionniste IA ?', 'Essai gratuit de 30 jours dans la limite de 60 appels, puis 39 € HT par mois avec 100 appels inclus, ou incluse dans la formule Élite.'],
        ],
      },
    ],
  },
]

export const deptBySlug = (slug: string) => DEPTS.find((d) => d.slug === slug)
export const cityOf = (dept: string, ville: string) => deptBySlug(dept)?.cities.find((c) => c.slug === ville)
/** Page département = page pilier locale du .fr (/agence-seo-local-…/). */
export const deptPath = (d: Dept) => `/agence-seo-local-${d.slug}/`
export const cityPath = (d: Dept, c: City) => `/zones/${d.slug}/${c.slug}/`
