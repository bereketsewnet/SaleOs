import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3002,
    proxy: {
      "/api/v1/telegram": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
      "/api/v1/core": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
