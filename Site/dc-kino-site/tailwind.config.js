/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'bg-red-900',
    'bg-rose-800',
  ],
  theme: {
    extend: {
      fontFamily: {
        bungee: ['"Bungee Shade"', 'cursive'],
        audiowide: ['"Audiowide"', 'cursive'],
        limelight: ['"Limelight"', 'cursive'],
        montserratalts: ['"Montserrat Alternates"', 'cursive'],
        alumnisc: ['"Alumni Sans SC"', 'cursive'],
      },
    },
  },
  plugins: [

  ],
}
