/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1F6F5C',
          hover: '#185A4A',
          soft: '#E6F1ED',
        },
        success: {
          DEFAULT: '#2E7D32',
          soft: '#E7F4E8',
        },
        warning: {
          DEFAULT: '#B26A00',
          soft: '#FBEFD9',
        },
        danger: {
          DEFAULT: '#C0392B',
          soft: '#FBE9E7',
        },
        info: {
          DEFAULT: '#2563A8',
          soft: '#E6EEF7',
        },
        ink: {
          DEFAULT: '#1A1D1C',
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
        },
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
        sm: '6px',
        md: '10px',
        lg: '14px',
        xl: '20px',
        pill: '999px',
      },
      boxShadow: {
        sm: '0 1px 2px rgba(20,29,28,0.06)',
        md: '0 2px 8px rgba(20,29,28,0.10)',
        lg: '0 8px 24px rgba(20,29,28,0.16)',
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
