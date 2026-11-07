// Adresse de contact publique unique pour tous les sites (.fr / .store / .info).
export const CONTACT_EMAIL = 'contact-plp@holdmasto.fr'
export const MAIL = `mailto:${CONTACT_EMAIL}?subject=`
export const mail = (subject: string) => MAIL + encodeURIComponent(subject)
