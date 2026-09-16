import Image from "next/image";
import Link from "next/link";
import { site } from "@/lib/site";

export default function Header() {
  return (
    <header className="border-b border-ink/10 bg-cream/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/brand/logo.png"
            alt={site.name}
            width={455}
            height={385}
            className="h-12 w-auto sm:h-14"
            priority
          />
        </Link>
        <nav className="flex items-center gap-4 text-sm font-medium text-ink/80 sm:gap-6">
          <Link href="/" className="hover:text-bordeaux-700">
            Inicio
          </Link>
          <Link href="/tienda" className="hover:text-bordeaux-700">
            Tienda
          </Link>
          <a
            href="#negocios"
            className="rounded-md border border-bordeaux-700 px-3 py-1.5 text-bordeaux-700 transition hover:bg-bordeaux-700 hover:text-cream"
          >
            Para negocios
          </a>
        </nav>
      </div>
    </header>
  );
}
