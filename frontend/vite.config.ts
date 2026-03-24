import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/echarts") || id.includes("node_modules/vue-echarts")) {
            return "charts";
          }
          if (id.includes("node_modules/element-plus") || id.includes("node_modules/@element-plus")) {
            return "element-plus";
          }
          if (id.includes("node_modules/vue") || id.includes("node_modules/pinia") || id.includes("node_modules/vue-router")) {
            return "vue-core";
          }
          return undefined;
        }
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true
      }
    }
  }
});
