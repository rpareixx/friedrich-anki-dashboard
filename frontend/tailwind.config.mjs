/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        brawl: {
          bg: "#0e0c1a",
          card: "#1a1730",
          accent: "#ffd64a",
          coin: "#ffb02e",
          streak: "#ff5e57",
          ok: "#50e3a4",
          dim: "#7c7290",
        },
      },
      fontFamily: {
        display: ['"Lilita One"', "system-ui", "sans-serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
