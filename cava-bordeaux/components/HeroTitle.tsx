"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";

/**
 * Moment "signature" unique du site : le titre du hero se compose mot par
 * mot, une seule fois. Volontairement pas répété ailleurs.
 *
 * Attend l'événement "cava:unlocked" (envoyé par AgeGate) avant de jouer
 * l'animation : sinon le titre finit de s'animer pendant que le modal
 * d'âge le cache encore, et personne ne la voit jamais.
 */
export default function HeroTitle({ text, className }: { text: string; className?: string }) {
  const prefersReducedMotion = useReducedMotion();
  const [unlocked, setUnlocked] = useState(false);
  const words = text.split(" ");

  useEffect(() => {
    const onUnlock = () => setUnlocked(true);
    window.addEventListener("cava:unlocked", onUnlock);
    return () => window.removeEventListener("cava:unlocked", onUnlock);
  }, []);

  if (prefersReducedMotion) {
    return <h1 className={className}>{text}</h1>;
  }

  return (
    <motion.h1
      className={className}
      initial="hidden"
      animate={unlocked ? "visible" : "hidden"}
      variants={{
        visible: { transition: { staggerChildren: 0.06, delayChildren: 0.1 } },
      }}
    >
      {words.map((word, i) => (
        <span key={i}>
          <span className="inline-block overflow-hidden">
            <motion.span
              className="inline-block"
              variants={{
                hidden: { y: "110%", opacity: 0 },
                visible: {
                  y: "0%",
                  opacity: 1,
                  transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
                },
              }}
            >
              {word}
            </motion.span>
          </span>
          {i < words.length - 1 ? " " : ""}
        </span>
      ))}
    </motion.h1>
  );
}
