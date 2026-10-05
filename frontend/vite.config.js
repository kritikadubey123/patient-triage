import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // The backend's CORS rule only allows http://localhost:5173, so fail loudly
    // instead of silently moving to 5174 (which would make every request fail).
    strictPort: true,
    // Listen on all interfaces so the dev server is reachable inside Docker (Phase 4).
    host: true,
  },
});