/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          50: '#f0f4ff',
          100: '#d9e2ff',
          800: '#0d1117',
          900: '#080c14',
          950: '#040709',
        },
        surface: '#0f1623',
        card: '#141c2e',
        border: '#1e2d45',
        bull: '#00d084',
        bear: '#ff4d6d',
        accent: '#3b82f6',
        gold: '#f59e0b',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        pulse_slow: 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        glow: 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(59,130,246,0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(59,130,246,0.8)' },
        },
      },
    },
  },
  plugins: [],
}
