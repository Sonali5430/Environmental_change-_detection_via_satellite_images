/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#060913",
          900: "#0a1124",
          850: "#0e1834",
          800: "#132247",
          700: "#1b2f63",
          600: "#26428c"
        },
        deforest: "#22c55e",
        water: "#06b6d4",
        burn: "#ef4444",
        urban: "#a855f7"
      }
    },
  },
  plugins: [],
}
