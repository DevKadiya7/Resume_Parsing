import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
    // Tests live beside nothing — they are collected from src/test/ only, so
    // a stray .test.js elsewhere in the tree is still picked up but the
    // default `dist/` and `node_modules/` scans stay excluded.
    exclude: ["node_modules", "dist"],
  },
});
