import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f6f8ff",
          100: "#e9edff",
          200: "#c9d5ff",
          500: "#3b5ccc",
          700: "#1f3480",
          900: "#0b1438"
        }
      }
    }
  },
  plugins: [],
};
export default config;

