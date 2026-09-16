export type WineColor = "Tinto" | "Blanco" | "Rosado" | "Espumoso";

export type Product = {
  slug: string;
  name: string;
  appellation: string;
  region: string;
  vintage: number;
  color: WineColor;
  price: number;
  stock: number;
  featured: boolean;
  description: string;
  pairing: string;
  tastingNotes: string[];
  image: string;
};

/**
 * Catálogo de demostración. Se usa mientras no haya un proyecto de Firebase
 * conectado (ver lib/firebase.ts) o hasta recibir el catálogo real en CSV.
 */
export const products: Product[] = [
  {
    slug: "chateau-rive-haute-2019",
    name: "Château Rive Haute",
    appellation: "Bordeaux Supérieur AOC",
    region: "Bordeaux",
    vintage: 2019,
    color: "Tinto",
    price: 690,
    stock: 24,
    featured: true,
    description:
      "Ensamble clásico de Merlot y Cabernet Sauvignon, criado 12 meses en barrica de roble francés. Cuerpo medio, taninos redondos y un final especiado.",
    pairing:
      "Ideal con cochinita pibil, mole poblano o costillas al carbón: la fruta madura del vino suaviza el picor y acompaña las notas ahumadas.",
    tastingNotes: ["Ciruela", "Cassis", "Vainilla", "Especias dulces"],
    image: "/wines/rive-haute.svg",
  },
  {
    slug: "domaine-des-collines-blanc-2021",
    name: "Domaine des Collines Blanc",
    appellation: "Entre-deux-Mers AOC",
    region: "Bordeaux",
    vintage: 2021,
    color: "Blanco",
    price: 540,
    stock: 30,
    featured: true,
    description:
      "Ensamble de Sauvignon Blanc y Sémillon, fresco y aromático, fermentado en tanque de acero inoxidable para preservar su frescura cítrica.",
    pairing:
      "Excelente con ceviche, aguachile o pescado a la veracruzana: su acidez viva limpia el paladar frente a los cítricos y el picante suave.",
    tastingNotes: ["Toronja", "Flor de azahar", "Piedra mojada", "Hierbas frescas"],
    image: "/wines/collines-blanc.svg",
  },
  {
    slug: "chateau-perle-du-medoc-2018",
    name: "Château Perle du Médoc",
    appellation: "Médoc AOC",
    region: "Bordeaux",
    vintage: 2018,
    color: "Tinto",
    price: 890,
    stock: 15,
    featured: true,
    description:
      "Cabernet Sauvignon dominante con Petit Verdot, crianza de 16 meses en barrica. Estructura firme, taninos elegantes y gran potencial de guarda.",
    pairing:
      "Perfecto con arrachera, barbacoa de res o birria: la estructura tánica del vino sostiene la grasa y la intensidad de las carnes rojas.",
    tastingNotes: ["Mora negra", "Grafito", "Tabaco", "Cedro"],
    image: "/wines/perle-du-medoc.svg",
  },
  {
    slug: "clos-saint-emilion-2017",
    name: "Clos Saint-Émilion Grand Cru",
    appellation: "Saint-Émilion Grand Cru AOC",
    region: "Bordeaux",
    vintage: 2017,
    color: "Tinto",
    price: 1450,
    stock: 8,
    featured: true,
    description:
      "Merlot predominante de viñedos de más de 40 años, crianza de 18 meses en barrica nueva. Untuoso, complejo y con un final muy persistente.",
    pairing:
      "Marida con mole negro oaxaqueño o chiles en nogada: la untuosidad del vino dialoga con las especias y frutos secos del mole.",
    tastingNotes: ["Cereza negra", "Chocolate", "Trufa", "Regaliz"],
    image: "/wines/saint-emilion.svg",
  },
  {
    slug: "chateau-rosee-de-gascogne-2022",
    name: "Château Rosée de Gascogne",
    appellation: "Côtes de Gascogne IGP",
    region: "Suroeste de Francia",
    vintage: 2022,
    color: "Rosado",
    price: 480,
    stock: 40,
    featured: true,
    description:
      "Rosado pálido de Merlot y Cabernet Franc, fermentación en frío para resaltar la fruta roja fresca. Ligero y muy versátil.",
    pairing:
      "Acompaña tacos al pastor, esquites o quesadillas de flor de calabaza: la frescura frutal contrasta con la grasa y el picante moderado.",
    tastingNotes: ["Fresa", "Sandía", "Pétalo de rosa", "Cítricos"],
    image: "/wines/rosee-gascogne.svg",
  },
  {
    slug: "chateau-graves-tradition-2020",
    name: "Château Graves Tradition",
    appellation: "Graves AOC",
    region: "Bordeaux",
    vintage: 2020,
    color: "Tinto",
    price: 760,
    stock: 20,
    featured: false,
    description:
      "Cabernet Sauvignon y Merlot en partes iguales, con notas minerales características de la denominación Graves. Equilibrado y fácil de disfrutar.",
    pairing:
      "Ideal con pozole rojo o enchiladas suizas: su acidez y mineralidad equilibran la riqueza del caldo y el queso gratinado.",
    tastingNotes: ["Grosella", "Pimienta negra", "Tierra húmeda", "Roble tostado"],
    image: "/wines/graves-tradition.svg",
  },
  {
    slug: "cremant-de-bordeaux-brut",
    name: "Crémant de Bordeaux Brut",
    appellation: "Crémant de Bordeaux AOC",
    region: "Bordeaux",
    vintage: 2021,
    color: "Espumoso",
    price: 620,
    stock: 18,
    featured: true,
    description:
      "Espumoso elaborado por método tradicional con Sémillon y Muscadelle, once meses sobre lías. Burbuja fina y persistente.",
    pairing:
      "Perfecto para brindar con un brunch de chilaquiles o con antojitos de botana: la burbuja y la acidez cortan la grasa de lo frito.",
    tastingNotes: ["Manzana verde", "Cítricos", "Pan tostado", "Almendra"],
    image: "/wines/cremant-brut.svg",
  },
  {
    slug: "chateau-fontaine-moulis-2019",
    name: "Château Fontaine Moulis",
    appellation: "Moulis-en-Médoc AOC",
    region: "Bordeaux",
    vintage: 2019,
    color: "Tinto",
    price: 980,
    stock: 12,
    featured: false,
    description:
      "Cabernet Sauvignon con un toque de Merlot y Petit Verdot, crianza de 14 meses en barrica de roble francés. Vino de guarda con gran personalidad.",
    pairing:
      "Combina muy bien con carnitas o cochinita al horno: la acidez y los taninos maduros equilibran la untuosidad del cerdo.",
    tastingNotes: ["Frutos negros", "Violeta", "Especias", "Roble fino"],
    image: "/wines/fontaine-moulis.svg",
  },
];

export function getFeaturedProducts(): Product[] {
  return products.filter((p) => p.featured);
}

export function getProductBySlug(slug: string): Product | undefined {
  return products.find((p) => p.slug === slug);
}

export const regions = Array.from(new Set(products.map((p) => p.region)));
export const colors: WineColor[] = ["Tinto", "Blanco", "Rosado", "Espumoso"];
