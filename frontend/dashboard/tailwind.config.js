/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Safe global remap: `gray` is used purely as neutral chrome throughout
        // the dashboard (never for status/semantic meaning), so bucketing every
        // shade onto our light/dark tokens re-themes existing `bg-white`,
        // `text-gray-900`, `border-gray-200` etc. classes app-wide with no
        // per-file edits needed. `white`/`black` are intentionally left alone —
        // both are used for text sitting on solid color badges/buttons
        // (e.g. `text-white` on `bg-red-600`) and must stay literal.
        gray: {
          50: 'var(--page)',
          100: 'var(--subtle)',
          200: 'var(--line)',
          300: 'var(--line-strong)',
          400: 'var(--ink-muted)',
          500: 'var(--ink-muted)',
          600: 'var(--ink-muted)',
          700: 'var(--ink)',
          800: 'var(--ink)',
          900: 'var(--ink)',
        },
        page: 'var(--page)',
        surface: 'var(--surface)',
        subtle: 'var(--subtle)',
        line: 'var(--line)',
        brand: {
          DEFAULT: 'var(--brand)',
          hover: 'var(--brand-hover)',
          tint: 'var(--brand-tint)',
          ink: 'var(--brand-ink)',
        },
      },
    },
  },
  plugins: [],
}
