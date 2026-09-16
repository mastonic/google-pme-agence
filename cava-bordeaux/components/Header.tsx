import Link from "next/link";
import { site } from "@/lib/site";

export default function Header() {
  return (
    <header className="border-b border-ink/10 bg-cream/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link href="/" className="font-serif text-xl tracking-wide text-bordeaux-800 sm:text-2xl">
          {site.name}
        </Link>
        <nav className="flex items-center gap-6 text-sm font-medium text-ink/80">
          <Link href="/" className="hover:text-bordeaux-700">
            Inicio
          </Link>
          <Link href="/tienda" className="hover:text-bordeaux-700">
            Tienda
          </Link>
        </nav>
      </div>
    </header>
  );
}
