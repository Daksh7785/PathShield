/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0b10",
        card: "#121420",
        primary: "#3b82f6",
        accent: "#6366f1",
        alert: "#ef4444",
        success: "#10b981",
        warning: "#f59e0b"
      },
    },
  },
  plugins: [],
}
