"use client"

import { useState } from 'react'

const FAQS: [string, string][] = [
  [
    'Pulse‑Pro est-il une vraie entreprise ?',
    'Pulse‑Pro est une solution commerciale exploitée par HoldMasto, société française immatriculée au RCS de Fort-de-France sous le numéro 106 121 536.',
  ],
  [
    'Pourquoi ai-je reçu une démo sans l’avoir demandée ?',
    'Nous pouvons préparer une démonstration à partir d’informations professionnelles déjà publiques afin de vous montrer concrètement ce qui pourrait être amélioré. Rien n’est publié sur votre domaine sans votre accord.',
  ],
  [
    'Suis-je obligé de souscrire après avoir vu la démo ?',
    'Non. La démonstration sert uniquement à vous permettre de juger le résultat avant de décider.',
  ],
  [
    'Qui s’occupe du site après la mise en ligne ?',
    'Selon la formule choisie, Pulse‑Pro gère l’hébergement, la maintenance, les modifications prévues au forfait et les services de visibilité associés.',
  ],
  [
    'Puis-je arrêter l’abonnement ?',
    'Les abonnements sont mensuels et sans engagement. Les conditions précises sont présentées avant tout paiement.',
  ],
]

export function Faq() {
  const [open, setOpen] = useState(0)

  return (
    <div className="faq-list">
      {FAQS.map(([q, a], i) => {
        const isOpen = open === i
        return (
          <div className="faq-item" key={q}>
            <h3 style={{ font: 'inherit', margin: 0 }}>
              <button
                className="faq-q"
                type="button"
                id={`faq-q${i}`}
                aria-expanded={isOpen}
                aria-controls={`faq-a${i}`}
                onClick={() => setOpen(isOpen ? -1 : i)}
              >
                <span>{q}</span>
                <span className="faq-icon" aria-hidden="true">{isOpen ? '–' : '+'}</span>
              </button>
            </h3>
            <p className="faq-a" id={`faq-a${i}`} role="region" aria-labelledby={`faq-q${i}`} hidden={!isOpen}>
              {a}
            </p>
          </div>
        )
      })}
    </div>
  )
}
