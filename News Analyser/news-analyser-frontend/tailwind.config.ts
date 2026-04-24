import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
        merriweather: ['Merriweather', 'serif'],
      },
      colors: {
        primary: {
          DEFAULT: '#1A56DB',
          dark: '#1140A8',
          light: '#EBF1FF',
        },
        secondary: {
          DEFAULT: '#0E9F6E',
          dark: '#057A55',
          light: '#DEF7EC',
        },
        sentiment: {
          positive: '#0E9F6E',
          'positive-bg': '#DEF7EC',
          negative: '#E02424',
          'negative-bg': '#FDE8E8',
          neutral: '#6B7280',
          'neutral-bg': '#F3F4F6',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.15s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
