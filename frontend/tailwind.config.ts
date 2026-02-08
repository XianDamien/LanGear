import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,ts,tsx,js,jsx}'],
  theme: {
    fontFamily: {
      sans: ['"Source Sans 3"', 'sans-serif'],
      pixel: ['"Pixelify Sans"', 'monospace'],
    },
    extend: {
      colors: {
        'brand-dark': '#f8fafc',
        'brand-panel': '#ffffff',
        'brand-accent': '#ff4d2d',
        'brand-accent-hover': '#e63b22',
        'brand-light': '#ffffff',
        'brand-secondary': '#475569',
        'brand-alert': '#ef4444',
      },
      boxShadow: {
        mech: '0 12px 30px rgba(15, 23, 42, 0.08)',
        'mech-sm': '0 6px 16px rgba(15, 23, 42, 0.08)',
      },
      animation: {
        'spin-slow': 'spin 8s linear infinite',
        fadeIn: 'fadeIn 0.3s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
