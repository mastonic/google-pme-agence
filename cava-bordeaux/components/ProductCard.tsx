import Link from "next/link";
import type { Product } from "@/lib/products";
import { formatMXN } from "@/lib/site";

export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link
      href={`/producto/${product.slug}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-ink/10 bg-white/60 transition-shadow duration-300 hover:border-gold-500/60 hover:shadow-lg motion-safe:hover:-translate-y-1 motion-safe:transition-transform"
    >
      <div className="flex aspect-[4/5] items-center justify-center overflow-hidden bg-gradient-to-b from-bordeaux-50 to-bordeaux-100">
        <div className="motion-safe:transition-transform motion-safe:duration-500 motion-safe:group-hover:scale-110">
          <BottleGlyph color={product.color} />
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-1 p-4">
        <span className="text-xs font-medium uppercase tracking-wide text-gold-600">
          {product.color} · {product.region}
        </span>
        <h3 className="font-serif text-lg text-ink group-hover:text-bordeaux-700">
          {product.name}
        </h3>
        <p className="text-sm text-ink/60">
          {product.appellation} · {product.vintage}
        </p>
        <div className="mt-auto flex items-center justify-between pt-3">
          <span className="font-semibold text-bordeaux-800">{formatMXN(product.price)}</span>
          <span className="text-sm text-bordeaux-600 underline-offset-2 group-hover:underline">
            Ver detalle
          </span>
        </div>
      </div>
    </Link>
  );
}

export function BottleGlyph({ color }: { color: Product["color"] }) {
  const fill =
    color === "Tinto"
      ? "#5e1725"
      : color === "Blanco"
        ? "#d9b45a"
        : color === "Rosado"
          ? "#d68a95"
          : "#c79a3f";
  return (
    <svg width="64" height="140" viewBox="0 0 64 140" fill="none" aria-hidden="true">
      <path
        d="M26 4h12v20c8 6 12 14 12 24v72a10 10 0 0 1-10 10H24a10 10 0 0 1-10-10V48c0-10 4-18 12-24V4Z"
        fill={fill}
        opacity="0.85"
      />
      <rect x="24" y="2" width="16" height="10" rx="2" fill="#2e0a12" />
    </svg>
  );
}
