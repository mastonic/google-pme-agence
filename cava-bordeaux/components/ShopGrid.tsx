"use client";

import { useMemo, useState } from "react";
import ProductCard from "@/components/ProductCard";
import { colors, products, regions, type WineColor } from "@/lib/products";

const PRICE_BANDS = [
  { label: "Todos los precios", min: 0, max: Infinity },
  { label: "Menos de $600", min: 0, max: 600 },
  { label: "$600 – $900", min: 600, max: 900 },
  { label: "Más de $900", min: 900, max: Infinity },
];

export default function ShopGrid() {
  const [color, setColor] = useState<WineColor | "Todos">("Todos");
  const [region, setRegion] = useState<string>("Todas");
  const [priceBand, setPriceBand] = useState(0);

  const filtered = useMemo(() => {
    const band = PRICE_BANDS[priceBand];
    return products.filter((p) => {
      if (color !== "Todos" && p.color !== color) return false;
      if (region !== "Todas" && p.region !== region) return false;
      if (p.price < band.min || p.price > band.max) return false;
      return true;
    });
  }, [color, region, priceBand]);

  return (
    <div>
      <div className="flex flex-wrap gap-4 border-b border-ink/10 pb-6">
        <FilterGroup label="Color">
          <select
            value={color}
            onChange={(e) => setColor(e.target.value as WineColor | "Todos")}
            className="rounded-md border border-ink/20 bg-white px-3 py-2 text-sm"
          >
            <option value="Todos">Todos</option>
            {colors.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </FilterGroup>

        <FilterGroup label="Región">
          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="rounded-md border border-ink/20 bg-white px-3 py-2 text-sm"
          >
            <option value="Todas">Todas</option>
            {regions.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </FilterGroup>

        <FilterGroup label="Precio">
          <select
            value={priceBand}
            onChange={(e) => setPriceBand(Number(e.target.value))}
            className="rounded-md border border-ink/20 bg-white px-3 py-2 text-sm"
          >
            {PRICE_BANDS.map((band, i) => (
              <option key={band.label} value={i}>
                {band.label}
              </option>
            ))}
          </select>
        </FilterGroup>
      </div>

      {filtered.length === 0 ? (
        <p className="py-16 text-center text-ink/60">
          No encontramos vinos con esos filtros. Prueba otra combinación.
        </p>
      ) : (
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 sm:gap-6 lg:grid-cols-4">
          {filtered.map((product) => (
            <ProductCard key={product.slug} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium uppercase tracking-wide text-ink/60">
      {label}
      {children}
    </label>
  );
}
