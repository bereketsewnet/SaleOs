/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
        // Telegram theme variables (filled by initTelegramTheme())
        tg: {
          bg: "var(--tg-bg, #ffffff)",
          text: "var(--tg-text, #000000)",
          hint: "var(--tg-hint, #707579)",
          link: "var(--tg-link, #3390ec)",
          button: "var(--tg-button, #3390ec)",
          buttonText: "var(--tg-button-text, #ffffff)",
          secondaryBg: "var(--tg-secondary-bg, #f1f1f1)",
        },
      },
    },
  },
  plugins: [],
};
