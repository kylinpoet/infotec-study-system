import { ref } from "vue";

type ThemePreset = {
  key: string;
  name: string;
  description: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    paper: string;
    line: string;
    text: string;
    subtext: string;
  };
};

const STORAGE_KEY = "infotec-theme-preset";

export const themePresets: ThemePreset[] = [
  {
    key: "campus-blue",
    name: "学校蓝",
    description: "稳重、清爽，适合综合校园门户",
    colors: {
      primary: "#2F6FED",
      secondary: "#14B8A6",
      accent: "#F59E0B",
      background: "#F3F6FB",
      paper: "rgba(255, 255, 255, 0.92)",
      line: "#D7E0EC",
      text: "#1F2937",
      subtext: "#5B6778",
    },
  },
  {
    key: "mint-tech",
    name: "青绿科技",
    description: "更偏信息科技实验室氛围",
    colors: {
      primary: "#0F766E",
      secondary: "#0EA5E9",
      accent: "#FB7185",
      background: "#EFF8F7",
      paper: "rgba(255, 255, 255, 0.92)",
      line: "#CFE5E2",
      text: "#15303A",
      subtext: "#4C6570",
    },
  },
  {
    key: "sunset-campus",
    name: "暖橙校园",
    description: "更有成果展板和校园展示气质",
    colors: {
      primary: "#C2410C",
      secondary: "#EAB308",
      accent: "#2563EB",
      background: "#FFF7ED",
      paper: "rgba(255, 255, 255, 0.94)",
      line: "#F0D8BE",
      text: "#4A2A16",
      subtext: "#7C5A45",
    },
  },
];

const currentThemeKey = ref(localStorage.getItem(STORAGE_KEY) ?? themePresets[0].key);

function resolvePreset(key: string) {
  return themePresets.find((preset) => preset.key === key) ?? themePresets[0];
}

export function applyThemePreset(key: string) {
  const preset = resolvePreset(key);
  const root = document.documentElement;
  root.dataset.themePreset = preset.key;
  root.style.setProperty("--theme-primary", preset.colors.primary);
  root.style.setProperty("--theme-secondary", preset.colors.secondary);
  root.style.setProperty("--theme-accent", preset.colors.accent);
  root.style.setProperty("--app-bg", preset.colors.background);
  root.style.setProperty("--app-paper", preset.colors.paper);
  root.style.setProperty("--app-paper-strong", "#FFFFFF");
  root.style.setProperty("--app-line", preset.colors.line);
  root.style.setProperty("--app-text", preset.colors.text);
  root.style.setProperty("--app-subtext", preset.colors.subtext);
  root.style.setProperty("--el-color-primary", preset.colors.primary);
  currentThemeKey.value = preset.key;
  localStorage.setItem(STORAGE_KEY, preset.key);
}

export function initializeThemePreset() {
  applyThemePreset(currentThemeKey.value);
}

export function useThemePreset() {
  return {
    themePresets,
    currentThemeKey,
    applyThemePreset,
  };
}
