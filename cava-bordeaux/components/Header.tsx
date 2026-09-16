"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useMotionValueEvent, useScroll } from "motion/react";
import { site } from "@/lib/site";

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const { scrollY } = useScroll();

  useMotionValueEvent(scrollY, "change", (latest) => {
    setScrolled(latest > 24);
  });

  return (
    <header
      className={`sticky top-0 z-40 border-b transition-[background-color,box-shadow,padding] duration-300 ${
        scrolled
          ? "border-ink/10 bg-cream/95 py-2 shadow-sm backdrop-blur"
          : "border-transparent bg-cream/0 py-3"
      }`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/brand/logo.png"
            alt={site.name}
            width={455}
            height={385}
            className={`w-auto transition-[height] duration-300 ${scrolled ? "h-10 sm:h-11" : "h-12 sm:h-14"}`}
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
