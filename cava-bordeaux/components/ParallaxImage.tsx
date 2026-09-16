"use client";

import { useRef } from "react";
import Image, { type ImageProps } from "next/image";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

/**
 * Léger parallax (scrub, sans pin) sur une image d'ambiance. N'intercepte
 * jamais le scroll natif — la position de l'image suit juste la progression
 * du scroll dans la section. Désactivé si l'utilisateur préfère un
 * mouvement réduit.
 */
export default function ParallaxImage({ alt, ...props }: ImageProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      if (!containerRef.current) return;

      gsap.registerPlugin(ScrollTrigger);

      gsap.to(containerRef.current.querySelector("img"), {
        yPercent: 8,
        ease: "none",
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top bottom",
          end: "bottom top",
          scrub: true,
        },
      });
    },
    { scope: containerRef }
  );

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden">
      <Image
        {...props}
        alt={alt}
        className={`scale-110 ${props.className ?? ""}`}
        style={{ ...props.style, willChange: "transform" }}
      />
    </div>
  );
}
