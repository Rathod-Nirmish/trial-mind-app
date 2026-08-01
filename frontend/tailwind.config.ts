import type { Config } from "tailwindcss";

/**
 * Tokens live in src/styles/tokens.css as CSS variables. Tailwind reads
 * them here as var(--...) so that changing a token in one file cascades
 * to every utility (bg-accent-500, text-neutral-700, etc.).
 */
const config: Config = {
  content: ["./index.html", "./src/**/*.{vue,ts}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--color-bg)",
        surface: "var(--color-surface)",
        text: "var(--color-text)",
        divider: "var(--color-divider)",
        accent: {
          DEFAULT: "var(--color-accent)",
          100: "var(--color-accent-100)",
          200: "var(--color-accent-200)",
          300: "var(--color-accent-300)",
          400: "var(--color-accent-400)",
          500: "var(--color-accent-500)",
          600: "var(--color-accent-600)",
          700: "var(--color-accent-700)",
          800: "var(--color-accent-800)",
          900: "var(--color-accent-900)",
        },
        neutral: {
          100: "var(--color-neutral-100)",
          200: "var(--color-neutral-200)",
          300: "var(--color-neutral-300)",
          400: "var(--color-neutral-400)",
          500: "var(--color-neutral-500)",
          600: "var(--color-neutral-600)",
          700: "var(--color-neutral-700)",
          800: "var(--color-neutral-800)",
          900: "var(--color-neutral-900)",
        },
      },
      fontFamily: {
        heading: ["Barlow Condensed", "system-ui", "sans-serif"],
        body: ["Barlow", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        DEFAULT: "var(--radius-md)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        DEFAULT: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
      },
      keyframes: {
        "tm-pulse": { "0%,100%": { opacity: "1" }, "50%": { opacity: ".55" } },
        "tm-spin": { to: { transform: "rotate(360deg)" } },
        "tm-blink": { "0%,49%": { opacity: "1" }, "50%,100%": { opacity: "0" } },
        "tm-rise": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "none" },
        },
        "tm-sheet": {
          from: { opacity: "0", transform: "translateY(28px)" },
          to: { opacity: "1", transform: "none" },
        },
      },
      animation: {
        "tm-pulse": "tm-pulse 1.4s ease-in-out infinite",
        "tm-spin": "tm-spin 1s linear infinite",
        "tm-blink": "tm-blink 1s step-end infinite",
        "tm-rise": "tm-rise 0.25s ease both",
        "tm-sheet": "tm-sheet 0.28s cubic-bezier(.32,.72,.33,1) both",
      },
    },
  },
  plugins: [],
};

export default config;
