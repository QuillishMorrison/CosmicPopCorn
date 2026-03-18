/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0b1118',
        panel: '#111a24',
        panelSoft: '#172434',
        borderSoft: '#233246',
        accent: '#79e6c5',
        accentWarm: '#f6c76e',
        textMain: '#e7eef7',
        textMute: '#89a0bb',
        danger: '#ff7f7f'
      },
      boxShadow: {
        panel: '0 20px 40px rgba(2, 8, 16, 0.35)'
      },
      borderRadius: {
        xl2: '1.25rem'
      }
    }
  },
  plugins: []
}
