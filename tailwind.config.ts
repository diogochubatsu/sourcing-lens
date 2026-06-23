import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#0A0A0A',
          soft: '#1F1F1F',
          muted: '#525252',
          faint: '#8A8A8A',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          warm: '#FAF8F2',
          page: '#F4F1EA',
        },
        brand: {
          DEFAULT: '#C8102E',
          hover: '#A00D24',
          soft: '#FBE7EA',
          deep: '#7A0A1A',
        },
        mustard: {
          DEFAULT: '#B45309',
          soft: '#FEF3C7',
        },
        border: {
          DEFAULT: '#1F1F1F',
          soft: '#C8C2B5',
          faint: '#DDD8CB',
        },
      },
      fontFamily: {
        sans: ['IBM Plex Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['IBM Plex Mono', 'JetBrains Mono', 'SF Mono', 'monospace'],
        serif: ['IBM Plex Serif', 'Georgia', 'serif'],
      },
      borderRadius: {
        sm: '2px',
        md: '4px',
        lg: '6px',
      },
      boxShadow: {
        sm: '0 1px 0 rgba(0,0,0,0.04)',
        md: '0 2px 8px rgba(0,0,0,0.06)',
        lg: '0 4px 16px rgba(0,0,0,0.08)',
      },
      animation: {
        'fade-in': 'fadeIn 0.25s ease both',
        'fade-in-up': 'fadeInUp 0.4s ease both',
        'slide-in': 'slideInRight 0.25s ease both',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        fadeInUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          from: { opacity: '0', transform: 'translateX(8px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
