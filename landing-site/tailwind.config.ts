import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // ── Design system Pulse-PME ──────────────
        porcelaine: '#F2F0E9',  // fond principal
        brume: '#E4E9E2',       // fond alterné (jade-brume)
        encre: '#1C231F',       // texte principal
        jade: '#3C6358',        // accent principal
        laiton: '#C0863F',      // accent chaud – CTA uniquement
      },
      fontFamily: {
        display: ['var(--font-petrona)', 'Georgia', 'serif'],
        sans: ['var(--font-work-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-ibm-plex-mono)', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}

export default config
