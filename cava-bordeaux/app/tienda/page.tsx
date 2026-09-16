import type { Metadata } from "next";
import ShopGrid from "@/components/ShopGrid";

export const metadata: Metadata = {
  title: "Tienda",
  description:
    "Explora nuestro catálogo de vinos franceses importados de Burdeos: tintos, blancos, rosados y espumosos, con maridaje sugerido para la cocina mexicana.",
};

export default function TiendaPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <div className="mb-8">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-gold-600">
          Catálogo
        </p>
        <h1 className="mt-2 font-serif text-3xl text-bordeaux-900 sm:text-4xl">
          Nuestros vinos
        </h1>
      </div>
      <ShopGrid />
    </div>
  );
}
