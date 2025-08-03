/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'bg-red-900/75',
    'bg-rose-800/75',
    'bg-orange-600/75',
    'bg-yellow-300/75',
    'bg-zinc-950/75',
    'bg-amber-50/75',
    'bg-lime-400/75',
    'bg-indigo-500/75',
    'border-zinc-600'
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
