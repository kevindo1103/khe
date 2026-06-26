/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // #204 responsive nav breakpoint: sidebar ≥760, bottom-tabs + header <760
      screens: {
        nav: '760px',
      },
      colors: {
        // ── Existing v0.1 semantic values (UNCHANGED) ──
        // Per Designer migrate-on-touch (#208 Q2): shipped screens keep their
        // current look; v0.2 value refresh (primary hue, AA-darkened warning)
        // is applied per-screen when each is next touched, not big-bang here.
        primary: {
          DEFAULT: '#1F6F5C',
          hover: '#185A4A',
          soft: '#E6F1ED',
          // v0.2 additive — for new components (#208 design system v0.2 §1)
          active: '#0A5740',
          border: '#BFE0D1',
        },
        success: {
          DEFAULT: '#2E7D32',
          soft: '#E7F4E8',
          border: '#BBE3C7',   // v0.2 additive
        },
        warning: {
          DEFAULT: '#B26A00',
          soft: '#FBEFD9',
          border: '#ECD7A6',   // v0.2 additive
        },
        danger: {
          DEFAULT: '#C0392B',
          soft: '#FBE9E7',
          border: '#F2C5C1',   // v0.2 additive
        },
        info: {
          DEFAULT: '#2563A8',
          soft: '#E6EEF7',
          border: '#C2D7F5',   // v0.2 additive
        },
        ink: {
          DEFAULT: '#1A1D1C',
          body: '#333E4F',     // v0.2 additive — body copy (neutral-700)
          muted: '#5B6360',
          subtle: '#8A918E',
        },
        border: {
          DEFAULT: '#DADEDC',
          strong: '#C2C8C5',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          alt: '#F5F7F6',
          sunken: '#F6F8FA',   // v0.2 additive — hover/track fill (neutral-50)
        },
        // ── v0.2 additive: neutral ramp (Atlassian N-scale) + focus ring ──
        // Net-new token names; the backbone for v0.2 minimalist screens.
        neutral: {
          0: '#FFFFFF',
          25: '#FBFCFD',
          50: '#F6F8FA',
          100: '#EDF1F5',
          200: '#E2E8F0',
          300: '#CBD4E1',
          400: '#94A3B8',
          500: '#647488',
          600: '#4A5567',
          700: '#333E4F',
          800: '#1F2733',
          900: '#0E141B',
        },
        ring: 'rgba(15,122,86,0.32)',  // v0.2 focus ring (WCAG 2.4.7)
      },
      fontFamily: {
        sans: ["'Inter'", "'Be Vietnam Pro'", 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['12px', { lineHeight: '1.5' }],
        xs: ['14px', { lineHeight: '1.5' }],
        sm: ['16px', { lineHeight: '1.5' }],
        md: ['18px', { lineHeight: '1.5' }],
        lg: ['22px', { lineHeight: '1.25' }],
        xl: ['28px', { lineHeight: '1.25' }],
        '2xl': ['34px', { lineHeight: '1.25' }],
      },
      spacing: {
        '0': '0px',
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
      },
      borderRadius: {
        xs: '4px',   // v0.2 additive
        sm: '6px',
        md: '10px',
        lg: '14px',
        xl: '20px',
        '2xl': '20px', // v0.2 additive
        pill: '999px',
      },
      boxShadow: {
        // Existing v0.1 names (unchanged)
        sm: '0 1px 2px rgba(20,29,28,0.06)',
        md: '0 2px 8px rgba(20,29,28,0.10)',
        lg: '0 8px 24px rgba(20,29,28,0.16)',
        // v0.2 layered elevation (soft, low-spread — Stripe/Atlassian)
        e0: 'none',
        e1: '0 1px 2px rgba(14,20,27,0.06), 0 1px 1px rgba(14,20,27,0.04)',
        e2: '0 2px 6px -1px rgba(14,20,27,0.08), 0 1px 3px rgba(14,20,27,0.05)',
        e3: '0 16px 32px -12px rgba(14,20,27,0.18), 0 6px 12px -4px rgba(14,20,27,0.08)',
        // focus ring as a box-shadow (use `shadow-ring` on focus-visible)
        ring: '0 0 0 3px rgba(15,122,86,0.32)',
      },
      // v0.2 motion tokens — uniform transitions
      transitionDuration: {
        fast: '120ms',
        base: '180ms',
        slow: '240ms',
      },
      transitionTimingFunction: {
        standard: 'cubic-bezier(0.2, 0, 0, 1)',
      },
      zIndex: {
        sticky: '100',
        overlay: '1000',
        modal: '1100',
        toast: '1200',
      },
    },
  },
  plugins: [],
}
