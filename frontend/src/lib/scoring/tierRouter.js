/**
 * getTier — returns 1, 2, 3 or null (score > 8.5 = out of scope)
 *
 * @param {object} scoreData
 * @param {number}  scoreData.score            – 0-10 digital health score
 * @param {boolean} scoreData.has_website
 * @param {number}  scoreData.nb_avis
 * @param {number}  scoreData.note_moyenne
 * @param {boolean} scoreData.has_photos
 * @param {boolean} scoreData.fiche_revendiquee
 */
export function getTier({ score }) {
  if (score <= 3.0) return 1;
  if (score <= 6.0) return 2;
  if (score <= 8.5) return 3;
  return null; // hors cible
}

export const TIER_LABELS = {
  1: 'Invisible',
  2: 'Présence fragile',
  3: 'Présent, non optimisé',
};

export const TIER_COLORS = {
  1: { bg: 'bg-red-500/20',   text: 'text-red-400',   border: 'border-red-500/30'   },
  2: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
  3: { bg: 'bg-sky-500/20',   text: 'text-sky-400',   border: 'border-sky-500/30'   },
};

/** Derive scoreData shape from a raw business object (API response). */
export function buildScoreData(biz) {
  const photos = Array.isArray(biz.photos) ? biz.photos : [];
  return {
    score:             biz.potential_score ?? 0,
    has_website:       Boolean(biz.website),
    nb_avis:           biz.user_ratings_total ?? 0,
    note_moyenne:      biz.rating ?? 0,
    has_photos:        photos.length > 0,
    fiche_revendiquee: Boolean(biz.fiche_revendiquee),
  };
}
