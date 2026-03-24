import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { api } from "../api/client";
import type { SessionUser } from "../types/contracts";

const STORAGE_KEY = "infotec-session";

export const useSessionStore = defineStore("session", () => {
  const token = ref<string | null>(null);
  const user = ref<SessionUser | null>(null);

  const cached = localStorage.getItem(STORAGE_KEY);
  if (cached) {
    const parsed = JSON.parse(cached) as { token: string; user: SessionUser };
    token.value = parsed.token;
    user.value = parsed.user;
  }

  const isLoggedIn = computed(() => Boolean(token.value && user.value));

  function persist() {
    if (token.value && user.value) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: token.value, user: user.value }));
      return;
    }
    localStorage.removeItem(STORAGE_KEY);
  }

  async function login(username: string, password: string, schoolCode?: string | null) {
    const response = await api.login(username, password, schoolCode);
    token.value = response.access_token;
    user.value = response.user;
    persist();
    return response.user;
  }

  function setUser(nextUser: SessionUser) {
    user.value = nextUser;
    persist();
  }

  function logout() {
    token.value = null;
    user.value = null;
    persist();
  }

  return {
    token,
    user,
    isLoggedIn,
    login,
    setUser,
    logout
  };
});
