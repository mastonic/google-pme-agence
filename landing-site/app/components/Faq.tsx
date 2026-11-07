"use client"

import { useState } from 'react'
import { FAQS } from '../seo/faq-data'


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
