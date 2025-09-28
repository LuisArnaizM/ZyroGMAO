/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx}', 
    './src/components/**/*.{js,ts,jsx,tsx}',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Usar las variables CSS que definiste
        primary: 'var(--primary)',
        'primary-dark': 'var(--primary-dark)', 
        'primary-light': 'var(--primary-light)',
        'primary-light-100': 'var(--primary-light-100)',
        secondary: 'var(--secondary)',
        'secondary-50': 'var(--secondary-50)',
        'secondary-100': 'var(--secondary-100)',
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        muted: 'var(--muted)',
        'muted-2': 'var(--muted-2)',
        border: 'var(--border)',
      },
      backgroundImage: {
        'primary-gradient': 'var(--primary-gradient)',
        'secondary-gradient': 'var(--secondary-gradient)',
        'header-gradient': 'var(--header-gradient)',
      },
      fontFamily: {
        sans: ['Roboto', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Montserrat', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': '.75rem',
        'sm': '.875rem',
        'base': '1rem',
        'lg': '1.125rem',
        'xl': '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
        '4xl': '2.25rem',
        '5xl': '3rem',
        '6xl': '3.75rem',
      },
      fontWeight: {
        'normal': 400,
        'medium': 500,
        'bold': 700,
        'extrabold': 800,
      }
    },
  },
  plugins: [],
}

export default config
