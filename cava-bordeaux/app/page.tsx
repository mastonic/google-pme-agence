import Link from "next/link";
import ProductCard from "@/components/ProductCard";
import { getFeaturedProducts } from "@/lib/products";

export default function HomePage() {
  const featured = getFeaturedProducts();

  return (
    <>
      <section className="border-b border-ink/10 bg-gradient-to-b from-bordeaux-50 to-cream">
        <div className="mx-auto max-w-6xl px-4 py-20 text-center sm:px-6 sm:py-28">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-gold-600">
            Importados de Burdeos a la Ciudad de México
          </p>
          <h1 className="mx-auto mt-4 max-w-2xl font-serif text-4xl leading-tight text-bordeaux-900 sm:text-5xl">
            Vinos franceses pensados para la mesa mexicana
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-ink/70">
            Cinco generaciones de viticultores en Burdeos, seleccionados y traídos a México
            para acompañar mole, tacos, ceviches y todo lo que se comparte en tu mesa.
          </p>
          <Link
            href="/tienda"
            className="mt-8 inline-block rounded-md bg-bordeaux-700 px-8 py-3 text-sm font-semibold text-cream transition hover:bg-bordeaux-800"
          >
            Ver la tienda
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="grid gap-10 sm:grid-cols-2 sm:items-center">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-gold-600">
              Nuestra historia
            </p>
            <h2 className="mt-3 font-serif text-3xl text-bordeaux-900">
              Una familia de vignerons, un puente entre dos mesas
            </h2>
            <p className="mt-4 text-ink/70">
              Somos una familia de viticultores de Burdeos desde hace cinco generaciones. Al
              casarme con una mexicana, descubrí una cocina tan intensa y generosa como
              nuestros propios vinos — y una pregunta obvia: ¿qué vino acompaña un mole, un
              pozole o unos tacos al pastor?
            </p>
            <p className="mt-4 text-ink/70">
              Cava de Bordeaux nació de esa pregunta. Importamos directamente de nuestros
              viñedos y de productores aliados en Burdeos, y seleccionamos cada etiqueta
              pensando en la cocina mexicana: acidez que corta el picante, taninos que
              sostienen las carnes al carbón, burbuja que refresca los antojitos.
            </p>
          </div>
          <div className="flex justify-center">
            <div className="flex gap-4 rounded-lg border border-gold-500/30 bg-bordeaux-50 p-8">
              <p className="font-serif text-6xl text-bordeaux-700">5</p>
              <p className="max-w-[10rem] self-center text-sm text-ink/70">
                generaciones de viticultores en Burdeos, hoy en México
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <div className="flex items-baseline justify-between">
          <h2 className="font-serif text-2xl text-bordeaux-900 sm:text-3xl">
            Selección destacada
          </h2>
          <Link href="/tienda" className="text-sm font-medium text-bordeaux-600 hover:underline">
            Ver todo
          </Link>
        </div>
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 sm:gap-6 lg:grid-cols-4">
          {featured.map((product) => (
            <ProductCard key={product.slug} product={product} />
          ))}
        </div>
      </section>
    </>
  );
}
