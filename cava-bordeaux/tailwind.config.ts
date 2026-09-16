import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: "rgb(var(--color-cream) / <alpha-value>)",
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        bordeaux: {
          50: "#fbf2f3",
          100: "#f5dfe1",
          200: "#e8b9bf",
          300: "#d68a95",
          400: "#bd5766",
          500: "#9c2f42",
          600: "#7c1f30",
          700: "#5e1725",
          800: "#450e1b",
          900: "#2e0a12",
          950: "#1a050a",
        },
        gold: {
          400: "#d9b45a",
          500: "#c79a3f",
          600: "#a67c2e",
        },
      },
      fontFamily: {
        serif: ["var(--font-display)", "Georgia", "Cambria", "serif"],
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
