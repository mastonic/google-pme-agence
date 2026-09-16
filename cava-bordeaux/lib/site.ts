export const site = {
  name: "Cava de Bordeaux",
  tagline: "Vinos franceses pensados para la mesa mexicana",
  description:
    "Importador de vinos franceses en la Ciudad de México. Cinco generaciones de viticultores en Burdeos, seleccionados para maridar con la cocina mexicana.",
  city: "Ciudad de México",
  url: "https://cavadebordeaux.mx",
  email: "hola@cavadebordeaux.mx",
  instagram: "https://instagram.com/cavadebordeaux",
};

export function formatMXN(amount: number): string {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    maximumFractionDigits: 0,
  }).format(amount);
}
