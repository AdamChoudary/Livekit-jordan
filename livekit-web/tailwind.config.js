/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        'sora': ['Sora', 'sans-serif'],
      },
      colors: {
        'crypto': {
          'bg': '#0A0F0D',
          'surface': '#0C1412',
          'primary': '#22E58C',
          'primary-hover': '#1ACB79',
          'text-primary': '#E7F7F0',
          'text-secondary': '#A4B9B0',
          'border': 'rgba(22, 58, 51, 0.4)',
          'accent-teal': '#00E5C1',
          'danger': '#FF5C77',
        }
      },
      fontSize: {
        'tag': ['12px', { lineHeight: '16px', letterSpacing: '0.01em' }],
        'tag-lg': ['14px', { lineHeight: '20px', letterSpacing: '0.01em' }],
        'hero-sm': ['32px', { lineHeight: '1.08', letterSpacing: '-0.01em' }],
        'hero-md': ['44px', { lineHeight: '1.08', letterSpacing: '-0.01em' }],
        'hero-lg': ['56px', { lineHeight: '1.08', letterSpacing: '-0.01em' }],
        'hero-xl': ['64px', { lineHeight: '1.08', letterSpacing: '-0.01em' }],
        'body': ['18px', { lineHeight: '28px' }],
        'body-sm': ['14px', { lineHeight: '20px' }],
        'body-md': ['16px', { lineHeight: '24px' }],
        'button': ['16px', { lineHeight: '20px' }],
      },
      animation: {
        'aurora': 'aurora 60s linear infinite',
        'chart-shimmer': 'chart-shimmer 15s linear infinite',
        'dock-rise': 'dock-rise 400ms cubic-bezier(0.22, 0.61, 0.36, 1) forwards',
        'micro-glow': 'micro-glow 2s ease-in-out infinite',
      },
      keyframes: {
        aurora: {
          '0%, 100%': { backgroundPosition: '50% 50%, 50% 50%' },
          '50%': { backgroundPosition: '350% 50%, 350% 50%' },
        },
        'chart-shimmer': {
          '0%': { strokeDashoffset: '0' },
          '100%': { strokeDashoffset: '-1000' },
        },
        'dock-rise': {
          'from': { transform: 'translateY(8px)', opacity: '0' },
          'to': { transform: 'translateY(0)', opacity: '1' },
        },
        'micro-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(34, 229, 140, 0.2)' },
          '50%': { boxShadow: '0 0 30px rgba(34, 229, 140, 0.4)' },
        },
      },
      transitionTimingFunction: {
        'ease-out-custom': 'cubic-bezier(0.22, 0.61, 0.36, 1)',
      },
      backdropBlur: {
        'custom': '12px',
        'strong': '16px',
      },
      maxWidth: {
        'container': '1200px',
        'container-sm': '1100px',
      },
    },
  },
  plugins: [],
};
