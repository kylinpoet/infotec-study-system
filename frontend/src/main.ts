import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import { installElement } from "./element";
import { initializeThemePreset } from "./composables/useThemePreset";
import { router } from "./router";
import "./styles/theme.css";

initializeThemePreset();

const app = createApp(App);

app.use(createPinia());
installElement(app);
app.use(router);
app.mount("#app");
