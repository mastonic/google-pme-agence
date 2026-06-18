"use client"

import { useEffect, useRef, useState } from 'react'

const STATS = [
  {
    value: 76,
    suffix: '%',
    label: 'des recherches locales aboutissent à une visite en commerce sous 24 h',
    source: 'Google',
  },
  {
    value: 3,
    suffix: '×',
    label: 'plus de visites pour une fiche Google optimisée vs une fiche vide',
    source: 'Google',
  },
  {
    value: 97,
    suffix: '%',
    label: 'des consommateurs lisent les avis en ligne avant de choisir',
    source: 'BrightLocal',
  },
] as const

function StatCard({
  value,
  suffix,
  label,
  source,
  delay,
}: {
  value: number
  suffix: string
  label: string
  source: string
  delay: number
}) {
  const [count, setCount] = useState(0)
  const [visible, setVisible] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const started = useRef(false)

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true
          setVisible(true)

          if (reduced) {
            setCount(value)
            return
          }

          setTimeout(() => {
            const duration = 1100
            const startTime = performance.now()
            const tick = (now: number) => {
              const progress = Math.min((now - startTime) / duration, 1)
              const eased = 1 - Math.pow(1 - progress, 3)
              setCount(Math.round(eased * value))
              if (progress < 1) requestAnimationFrame(tick)
            }
            requestAnimationFrame(tick)
          }, delay)
        }
      },
      { threshold: 0.4 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [value, delay])

  // Bar fills to stat value for %, to 60% visual for × (no natural max)
  const barTarget = suffix === '%' ? value : 60
  const reduced =
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false

  return (
    <div ref={ref}>
      {/* Animated number */}
      <p className="font-mono text-[3.25rem] leading-none tracking-tight text-jade sm:text-[3.75rem] tabular-nums">
        {count}
        {suffix}
      </p>

      {/* Fill bar */}
      <div className="mt-3 h-px w-full max-w-[180px] overflow-hidden bg-porcelaine/10">
        <div
          className="h-full bg-jade"
          style={{
            width: visible ? `${barTarget}%` : '0%',
            transition: reduced
              ? 'none'
              : `width 1.4s cubic-bezier(0.2, 0, 0.5, 1) ${delay + 250}ms`,
          }}
        />
      </div>

      {/* Label */}
      <p className="mt-4 text-[0.875rem] leading-[1.65] text-porcelaine/58">
        {label}
      </p>

      {/* Source */}
      <p className="mt-2 font-mono text-[0.625rem] uppercase tracking-[0.2em] text-porcelaine/25">
        {source}
      </p>
    </div>
  )
}

export function StatStrip() {
  return (
    <section className="bg-encre px-6 py-16 sm:py-24" aria-label="Chiffres clés">
      <div className="mx-auto max-w-[680px]">
        <p className="mb-10 font-mono text-[0.68rem] uppercase tracking-[0.25em] text-jade/55">
          Pourquoi ça compte
        </p>
        <div className="grid grid-cols-1 gap-12 sm:grid-cols-3 sm:gap-8">
          {STATS.map((stat, i) => (
            <StatCard key={stat.label} {...stat} delay={i * 160} />
          ))}
        </div>
      </div>
    </section>
  )
}
