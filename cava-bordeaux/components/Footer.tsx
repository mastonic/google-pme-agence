import { site } from "@/lib/site";

export default function Footer() {
  return (
    <footer className="mt-24 border-t border-ink/10 bg-bordeaux-950 text-cream/80">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <div className="grid gap-8 sm:grid-cols-2">
          <div>
            <p className="font-serif text-xl text-cream">{site.name}</p>
            <p className="mt-2 max-w-sm text-sm text-cream/70">{site.description}</p>
          </div>
          <div className="text-sm text-cream/70 sm:text-right">
            <p>{site.city}, México</p>
            <p>{site.email}</p>
            <p className="mt-4 text-xs uppercase tracking-wide text-gold-400">
              Venta exclusiva a mayores de 18 años. Prohibida su venta a menores de edad.
              Consumo con moderación.
            </p>
          </div>
        </div>
        <p className="mt-10 border-t border-cream/10 pt-6 text-xs text-cream/50">
          © {new Date().getFullYear()} {site.name}. Todos los derechos reservados.
        </p>
      </div>
    </footer>
  );
}
