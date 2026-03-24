import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";

import App from "./App.vue";
import "./charts/setup";
import { initializeThemePreset } from "./composables/useThemePreset";
import { router } from "./router";
import "./styles/theme.css";

initializeThemePreset();

const app = createApp(App);

app.use(createPinia());
app.use(ElementPlus);
app.use(router);
app.mount("#app");
