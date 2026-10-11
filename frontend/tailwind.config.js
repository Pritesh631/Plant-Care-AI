/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        leaf: {
          50: '#f1f9f1', 100: '#dcf0dc', 200: '#b9e0ba', 300: '#8bc98d', 400: '#5aae5e',
          500: '#389340', 600: '#2a7632', 700: '#235e2a', 800: '#1f4a25', 900: '#1a3d20',
        },
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'], display: ['Poppins', 'Inter', 'sans-serif'] },
    },
  },
  plugins: [],
}
