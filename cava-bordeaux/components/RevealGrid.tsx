"use client";

import { motion, useReducedMotion } from "motion/react";

/**
 * Reveal en stagger à l'entrée dans le viewport (une seule fois). Sert de
 * wrapper autour des grilles produits — ne remplace pas leur layout CSS.
 */
export default function RevealGrid({
  children,
  className,
}: {
  children: React.ReactNode[];
  className?: string;
}) {
  const prefersReducedMotion = useReducedMotion();

  if (prefersReducedMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-80px" }}
      variants={{
        visible: { transition: { staggerChildren: 0.08 } },
      }}
    >
      {children.map((child, i) => (
        <motion.div
          key={i}
          variants={{
            hidden: { opacity: 0, y: 24 },
            visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
          }}
        >
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
}
