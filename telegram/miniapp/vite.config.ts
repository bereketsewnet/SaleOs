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
      // All other Core endpoints used by the Mini App: catalog, core, internal.
      // Order matters — /api/v1/telegram is matched first.
      "/api/v1/catalog": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/api/v1/core": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/api/v1/auth": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      // WebSocket — not used by Mini App today, but ready for the future.
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
