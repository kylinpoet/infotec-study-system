<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-brand">
        <p class="panel-kicker">Infotec Platform</p>
        <h1>义务教育阶段信息科技课程综合平台</h1>
        <p class="app-brand__note">学校门户、课程目录、机房课堂与 AI 教学分析统一协作</p>
      </div>

      <nav class="app-nav">
        <RouterLink class="app-nav__link" to="/">学校门户</RouterLink>
        <RouterLink class="app-nav__link" to="/teacher">教师工作台</RouterLink>
        <RouterLink class="app-nav__link" to="/student">学生中心</RouterLink>
        <RouterLink v-if="session.user?.role === 'teacher'" class="app-nav__link" to="/teacher/settings">教师设置</RouterLink>
        <RouterLink v-if="session.user?.role === 'student'" class="app-nav__link" to="/student/settings">学生设置</RouterLink>
        <RouterLink v-if="session.user?.role === 'admin'" class="app-nav__link" to="/admin">门户后台</RouterLink>
      </nav>

      <div class="app-toolbar">
        <div class="theme-switcher">
          <span class="theme-switcher__label">主题风格</span>
          <el-select
            v-model="currentThemeKey"
            size="small"
            class="theme-switcher__select"
            @change="applyThemePreset"
          >
            <el-option
              v-for="preset in themePresets"
              :key="preset.key"
              :label="`${preset.name} · ${preset.description}`"
              :value="preset.key"
            />
          </el-select>
        </div>

        <div class="app-user" v-if="session.user">
          <ZodiacAgentAvatar :animal-key="session.user.avatar ?? 'dragon'" compact />
          <el-tag type="primary" effect="light" round>{{ session.user.tenant_name }}</el-tag>
          <div class="app-user__meta">
            <strong>{{ session.user.display_name }}</strong>
            <span>
              {{
                session.user.role === "teacher"
                  ? "教师账号"
                  : session.user.role === "student"
                    ? "学生账号"
                    : "门户管理员"
              }}
            </span>
          </div>
          <el-button plain round @click="session.logout()">退出</el-button>
        </div>
      </div>
    </el-header>

    <el-main class="app-main">
      <RouterView />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";

import ZodiacAgentAvatar from "./components/ZodiacAgentAvatar.vue";
import { useThemePreset } from "./composables/useThemePreset";
import { useSessionStore } from "./stores/session";

const session = useSessionStore();
const { currentThemeKey, themePresets, applyThemePreset } = useThemePreset();
</script>
