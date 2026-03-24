<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-brand">
        <p class="panel-kicker">Infotec Platform</p>
        <h1>义务教育阶段信息科技课程综合平台</h1>
        <p class="app-brand__note">学校门户、课程目录、机房课堂与 AI 作业分析统一协作</p>
      </div>

      <nav class="app-nav">
        <RouterLink class="app-nav__link" to="/">学校门户</RouterLink>
        <RouterLink class="app-nav__link" to="/teacher">教师工作台</RouterLink>
        <RouterLink class="app-nav__link" to="/student">学生中心</RouterLink>
      </nav>

      <div class="app-user" v-if="session.user">
        <el-tag type="primary" effect="light" round>{{ session.user.tenant_name }}</el-tag>
        <div class="app-user__meta">
          <strong>{{ session.user.display_name }}</strong>
          <span>{{ session.user.role === "teacher" ? "教师账号" : "学生账号" }}</span>
        </div>
        <el-button plain round @click="session.logout()">退出</el-button>
      </div>
    </el-header>

    <el-main class="app-main">
      <RouterView />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";

import { useSessionStore } from "./stores/session";

const session = useSessionStore();
</script>
