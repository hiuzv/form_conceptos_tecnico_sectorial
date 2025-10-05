import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/llenado": { target: "http://localhost:8000", changeOrigin: true },
      "/descarga": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
