<template>
  <div class="portal-page" v-if="portal && selectedSchool">
    <section class="hero-grid">
      <el-card class="panel-card hero-card" :style="heroStyle" shadow="never">
        <div class="hero-card__content">
          <div class="hero-card__copy">
            <div>
              <p class="panel-kicker">学校门户</p>
              <h2>{{ portal.hero_title }}</h2>
              <p class="hero-copy">{{ portal.hero_subtitle }}</p>
            </div>

            <div class="hero-school-switcher">
              <span class="panel-note">学校选择</span>
              <el-select v-model="selectedSchoolCode" class="school-select" size="large">
                <el-option
                  v-for="school in portal.schools"
                  :key="school.code"
                  :label="school.name"
                  :value="school.code"
                />
              </el-select>
            </div>

            <div class="feature-pill-row">
              <el-tag
                v-for="feature in portal.platform_highlights"
                :key="feature.title"
                effect="dark"
                round
                class="hero-tag"
              >
                {{ feature.title }}
              </el-tag>
            </div>
          </div>

          <article class="hero-school-stage">
            <div class="hero-school-stage__head">
              <div>
                <p class="panel-kicker">{{ selectedSchool.district }}</p>
                <h3>{{ selectedSchool.name }}</h3>
              </div>
              <el-tag effect="dark" round>{{ selectedSchool.grade_scope }}</el-tag>
            </div>
            <p class="hero-school-stage__slogan">{{ selectedSchool.slogan }}</p>
            <div class="hero-stage-metrics">
              <div
                v-for="metric in selectedSchool.metrics"
                :key="metric.title"
                class="hero-stage-metric"
              >
                <span>{{ metric.title }}</span>
                <strong>{{ metric.value }}</strong>
                <p>{{ metric.hint }}</p>
              </div>
            </div>
          </article>
        </div>
      </el-card>

      <el-card class="panel-card login-panel login-panel--portal" shadow="never">
        <template #header>
          <div class="panel-head">
            <div>
              <p class="panel-kicker">统一登录</p>
              <h3>进入教学平台</h3>
            </div>
            <el-tag round effect="plain">{{ selectedSchool.name }}</el-tag>
          </div>
        </template>

        <el-form label-position="top" @submit.prevent="handleSubmit">
          <el-form-item label="用户名">
            <el-input v-model="username" placeholder="教师：kylin / 学生：240101" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="password" show-password placeholder="请输入密码" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" class="fill-button" :loading="loading" @click="handleSubmit">
              登录并进入平台
            </el-button>
          </el-form-item>
        </el-form>

        <div class="demo-button-row">
          <el-button round @click="useDemo('teacher')">教师演示账号</el-button>
          <el-button round @click="useDemo('student')">学生演示账号</el-button>
        </div>
        <p class="panel-note">当前演示账号仅开放在「行知信息科技实验学校」。</p>
        <p v-if="errorMessage" class="status-text status-text--error">{{ errorMessage }}</p>
      </el-card>
    </section>

    <section class="portal-grid">
      <el-card class="panel-card school-focus-card" shadow="hover">
        <template #header>
          <div class="panel-head">
            <div>
              <p class="panel-kicker">{{ selectedSchool.district }}</p>
              <h3>{{ selectedSchool.name }}</h3>
            </div>
            <el-tag effect="plain" round>{{ selectedSchool.grade_scope }}</el-tag>
          </div>
        </template>

        <p class="school-slogan">{{ selectedSchool.slogan }}</p>

        <div class="school-story">
          <p class="panel-note">
            当前学校门户把学校展示、课程运营、机房课堂和 AI 教学能力放在同一个品牌叙事里，
            让家长、教师和学生都能先理解这所学校的信息科技特色，再进入各自的工作空间。
          </p>
          <div class="tag-row">
            <el-tag round effect="plain">{{ selectedSchool.code }}</el-tag>
            <el-tag round effect="plain">{{ selectedSchool.district }}</el-tag>
            <el-tag round effect="plain">{{ selectedSchool.grade_scope }}</el-tag>
          </div>
        </div>

        <div class="school-feature-grid">
          <el-card
            v-for="feature in selectedSchool.features"
            :key="feature.title"
            class="mini-panel"
            shadow="never"
          >
            <p class="panel-kicker">学校亮点</p>
            <h4>{{ feature.title }}</h4>
            <p class="panel-note">{{ feature.description }}</p>
          </el-card>
        </div>
      </el-card>

      <el-card class="panel-card announcement-card" shadow="hover">
        <template #header>
          <div class="panel-head">
            <div>
              <p class="panel-kicker">校园动态</p>
              <h3>公告与平台更新</h3>
            </div>
          </div>
        </template>

        <el-timeline>
          <el-timeline-item
            v-for="announcement in portal.announcements"
            :key="`${announcement.tag}-${announcement.title}`"
            :timestamp="formatDate(announcement.published_at)"
            placement="top"
          >
            <div class="announcement-item">
              <el-tag size="small" round>{{ announcement.tag }}</el-tag>
              <strong>{{ announcement.title }}</strong>
              <p class="panel-note">{{ announcement.summary }}</p>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </section>

    <section class="school-gallery">
      <div class="gallery-head">
        <div>
          <p class="panel-kicker">学校特色</p>
          <h3>不同学校可共用平台能力，但保留自己的展示风格</h3>
        </div>
      </div>

      <div class="school-card-row">
        <el-card
          v-for="school in portal.schools"
          :key="school.code"
          class="panel-card school-gallery-card"
          shadow="hover"
          @click="selectedSchoolCode = school.code"
        >
          <div class="school-gallery-card__header">
            <div>
              <strong>{{ school.name }}</strong>
              <p class="panel-note">{{ school.district }} · {{ school.grade_scope }}</p>
            </div>
            <el-tag round effect="plain">查看学校</el-tag>
          </div>
          <p class="panel-note">{{ school.slogan }}</p>
          <ul class="feature-list">
            <li v-for="feature in school.features.slice(0, 2)" :key="feature.title">{{ feature.title }}</li>
          </ul>
        </el-card>
      </div>
    </section>
  </div>

  <el-skeleton v-else animated :rows="8" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { api } from "../api/client";
import { useSessionStore } from "../stores/session";
import type { PortalResponse } from "../types/contracts";

const router = useRouter();
const session = useSessionStore();

const portal = ref<PortalResponse | null>(null);
const selectedSchoolCode = ref("");
const username = ref("");
const password = ref("");
const errorMessage = ref("");
const loading = ref(false);

const selectedSchool = computed(() => {
  if (!portal.value) {
    return null;
  }
  return (
    portal.value.schools.find((school) => school.code === selectedSchoolCode.value) ??
    portal.value.schools[0]
  );
});

const heroStyle = computed(() => {
  const school = selectedSchool.value;
  if (!school) {
    return {};
  }
  return {
    "--hero-primary": school.theme.primary,
    "--hero-secondary": school.theme.secondary,
    "--hero-accent": school.theme.accent
  };
});

onMounted(async () => {
  portal.value = await api.getPortal();
  selectedSchoolCode.value = portal.value.featured_school_code ?? portal.value.schools[0]?.code ?? "";
});

async function handleSubmit() {
  if (!selectedSchool.value) {
    return;
  }
  errorMessage.value = "";
  loading.value = true;
  try {
    const user = await session.login(username.value, password.value, selectedSchool.value.code);
    await router.push(user.role === "teacher" ? "/teacher" : "/student");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "登录失败";
  } finally {
    loading.value = false;
  }
}

function useDemo(role: "teacher" | "student") {
  selectedSchoolCode.value = "xingzhi-school";
  username.value = role === "teacher" ? "kylin" : "240101";
  password.value = role === "teacher" ? "222221" : "12345";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit"
  }).format(new Date(value));
}
</script>
