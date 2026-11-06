"use client"

import { useEffect } from 'react'

/**
 * Animations d'apparition au défilement.
 * Les éléments portent data-reveal="<délai ms>" ou data-reveal="stagger" (décalage de 110 ms
 * entre frères). Le masquage initial n'a lieu que si <html> porte la classe .motion
 * (posée dans le layout avant affichage, sauf prefers-reduced-motion).
 */
export function Reveal() {
  useEffect(() => {
    const root = document.documentElement
    if (!root.classList.contains('motion')) return
    if (!('IntersectionObserver' in window)) {
      root.classList.remove('motion')
      return
    }

    const els = Array.from(document.querySelectorAll<HTMLElement>('[data-reveal]'))
    const delays = new Map<HTMLElement, number>()
    const groups = new Map<Element | null, number>()
    els.forEach((el) => {
      let d = parseInt(el.dataset.reveal || '', 10) || 0
      if (el.dataset.reveal === 'stagger') {
        const i = groups.get(el.parentElement) || 0
        groups.set(el.parentElement, i + 1)
        d = i * 110
      }
      el.style.setProperty('--reveal-delay', `${d}ms`)
      delays.set(el, d)
    })

    const timers: number[] = []
    const show = (el: HTMLElement) => {
      el.classList.add('is-visible')
      // Une fois l'apparition terminée, l'élément retrouve ses styles normaux (survol des cartes…)
      timers.push(
        window.setTimeout(() => {
          el.removeAttribute('data-reveal')
          el.removeAttribute('data-reveal-scale')
          el.classList.remove('is-visible')
          el.style.removeProperty('--reveal-delay')
        }, 950 + (delays.get(el) || 0)),
      )
    }

    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            show(e.target as HTMLElement)
            io.unobserve(e.target)
          }
        }),
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' },
    )
    const raf = requestAnimationFrame(() => els.forEach((el) => io.observe(el)))

    return () => {
      cancelAnimationFrame(raf)
      io.disconnect()
      timers.forEach(clearTimeout)
    }
  }, [])

  return null
}
