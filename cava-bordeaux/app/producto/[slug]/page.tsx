import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { BottleGlyph } from "@/components/ProductCard";
import { getProductBySlug, products } from "@/lib/products";
import { formatMXN, site } from "@/lib/site";

export function generateStaticParams() {
  return products.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const product = getProductBySlug(slug);
  if (!product) return {};
  return {
    title: `${product.name} — ${product.vintage}`,
    description: product.description,
    openGraph: {
      title: `${product.name} (${product.vintage})`,
      description: product.description,
    },
  };
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = getProductBySlug(slug);
  if (!product) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    description: product.description,
    sku: product.slug,
    brand: { "@type": "Brand", name: site.name },
    offers: {
      "@type": "Offer",
      url: `${site.url}/producto/${product.slug}`,
      priceCurrency: "MXN",
      price: product.price,
      availability:
        product.stock > 0 ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
    },
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      {/* eslint-disable-next-line react/no-danger */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="grid gap-10 sm:grid-cols-2">
        <div className="flex items-center justify-center rounded-lg bg-gradient-to-b from-bordeaux-50 to-bordeaux-100 py-16">
          <BottleGlyph color={product.color} />
        </div>

        <div>
          <span className="text-xs font-medium uppercase tracking-wide text-gold-600">
            {product.color} · {product.region}
          </span>
          <h1 className="mt-2 font-serif text-3xl text-bordeaux-900 sm:text-4xl">
            {product.name}
          </h1>
          <p className="mt-1 text-ink/60">
            {product.appellation} · Añada {product.vintage}
          </p>
          <p className="mt-6 text-2xl font-semibold text-bordeaux-800">
            {formatMXN(product.price)}
          </p>

          <p className="mt-6 text-ink/80">{product.description}</p>

          <div className="mt-6 flex flex-wrap gap-2">
            {product.tastingNotes.map((note) => (
              <span
                key={note}
                className="rounded-full border border-gold-500/40 bg-gold-400/10 px-3 py-1 text-xs text-bordeaux-800"
              >
                {note}
              </span>
            ))}
          </div>

          <div className="mt-8 rounded-lg border border-bordeaux-200 bg-bordeaux-50 p-5">
            <p className="text-sm font-semibold uppercase tracking-wide text-bordeaux-700">
              Maridaje sugerido
            </p>
            <p className="mt-2 text-ink/80">{product.pairing}</p>
          </div>

          <button
            type="button"
            disabled
            title="El carrito y el pago en línea llegan en la siguiente fase del sitio"
            className="mt-8 w-full cursor-not-allowed rounded-md bg-ink/20 px-6 py-3 text-sm font-semibold text-ink/50 sm:w-auto sm:px-10"
          >
            Añadir al carrito — próximamente
          </button>
        </div>
      </div>
    </div>
  );
}
