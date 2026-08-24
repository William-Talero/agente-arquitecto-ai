import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5186,
    proxy: {
      "/api": "http://127.0.0.1:8050",
      "/metrics": "http://127.0.0.1:8050",
    },
  },
});
