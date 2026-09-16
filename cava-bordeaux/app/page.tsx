import Image from "next/image";
import Link from "next/link";
import ProductCard from "@/components/ProductCard";
import { getFeaturedProducts } from "@/lib/products";
import { site } from "@/lib/site";

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
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Link
              href="/tienda"
              className="inline-block rounded-md bg-bordeaux-700 px-8 py-3 text-sm font-semibold text-cream transition hover:bg-bordeaux-800"
            >
              Comprar vinos
            </Link>
            <a
              href="#negocios"
              className="inline-block rounded-md border border-bordeaux-700 px-8 py-3 text-sm font-semibold text-bordeaux-700 transition hover:bg-bordeaux-700 hover:text-cream"
            >
              Soy restaurante o negocio
            </a>
          </div>
        </div>
      </section>

      {/* Credibilidad: foto real en feria + presencia de marca */}
      <section className="relative">
        <div className="relative h-[340px] w-full sm:h-[420px]">
          <Image
            src="/brand/equipo-feria.jpg"
            alt="Equipo de Cava de Bordeaux presentando sus vinos en un salón del vino en México"
            fill
            priority
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-ink/85 via-ink/20 to-transparent" />
        </div>
        <div className="absolute inset-x-0 bottom-0 mx-auto max-w-6xl px-4 pb-8 sm:px-6">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-gold-400">
            Presencia real en México
          </p>
          <p className="mt-2 max-w-2xl font-serif text-xl text-cream sm:text-2xl">
            Nos presentamos en persona en Gourmet Show CDMX y ZonaVino by Reforma —
            catando cada vino con quienes lo van a servir.
          </p>
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
            <div className="relative aspect-[2/3] w-48 overflow-hidden rounded-lg border border-gold-500/30 shadow-xl sm:w-56">
              <Image
                src="/brand/botella-loubiere.jpg"
                alt="Botella de vino francés seleccionada por Cava de Bordeaux"
                fill
                className="object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* B2C / B2B */}
      <section id="negocios" className="mx-auto max-w-6xl px-4 py-4 sm:px-6">
        <div className="grid gap-6 sm:grid-cols-2">
          <div className="rounded-lg border border-ink/10 bg-white/60 p-8">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-gold-600">
              Para tu mesa
            </p>
            <h3 className="mt-2 font-serif text-2xl text-bordeaux-900">Particulares</h3>
            <p className="mt-3 text-ink/70">
              Compra en línea, elige tu maridaje y recibe tus vinos en la Ciudad de México.
            </p>
            <Link
              href="/tienda"
              className="mt-6 inline-block rounded-md bg-bordeaux-700 px-6 py-3 text-sm font-semibold text-cream transition hover:bg-bordeaux-800"
            >
              Ver catálogo
            </Link>
          </div>
          <div className="rounded-lg border border-bordeaux-900/20 bg-bordeaux-950 p-8 text-cream">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-gold-400">
              Para tu negocio
            </p>
            <h3 className="mt-2 font-serif text-2xl text-cream">
              Restaurantes, hoteles y tiendas
            </h3>
            <p className="mt-3 text-cream/70">
              Cartas de vino, volúmenes por mayoreo y acompañamiento en la selección de
              maridajes para tu menú. Te contactamos en menos de 24 horas.
            </p>
            <a
              href={`mailto:${site.email}?subject=Cotizaci%C3%B3n%20mayoreo%20Cava%20de%20Bordeaux`}
              className="mt-6 inline-block rounded-md border border-cream/40 px-6 py-3 text-sm font-semibold text-cream transition hover:bg-cream hover:text-bordeaux-900"
            >
              Solicitar cotización
            </a>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
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
