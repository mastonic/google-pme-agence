"use client";

import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";

/**
 * Smooth-scroll (Lenis) synchronisé avec GSAP ScrollTrigger. Ne fait rien si
 * l'utilisateur préfère un mouvement réduit : le scroll natif reste inchangé.
 * Ne prend jamais le contrôle du scroll (pas de scroll-jacking) — Lenis ne
 * fait que lisser les deltas, il n'intercepte pas la navigation.
 */
export default function SmoothScroll() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    const lenis = new Lenis({
      autoRaf: false,
    });

    lenis.on("scroll", ScrollTrigger.update);

    const tick = (time: number) => {
      lenis.raf(time * 1000);
    };
    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(tick);
      lenis.destroy();
    };
  }, []);

  return null;
}
