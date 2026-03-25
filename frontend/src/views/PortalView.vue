<template>
  <div class="portal-page" v-if="portal && selectedSchool">
    <section class="hero-grid hero-grid--portal">
      <el-card class="panel-card hero-card hero-card--portal" :style="heroStyle" shadow="never">
        <div class="hero-card__content hero-card__content--portal">
          <div class="hero-card__masthead">
            <div class="hero-card__copy hero-card__copy--portal">
              <div class="hero-card__eyebrow">
                <span class="hero-eyebrow-badge">
                  <el-icon><School /></el-icon>
                  <span>学校门户</span>
                </span>
                <span class="hero-eyebrow-note">多校一体化部署，保留每所学校自己的课程气质</span>
              </div>

              <div>
                <h2>{{ portal.hero_title }}</h2>
                <p class="hero-copy">{{ portal.hero_subtitle }}</p>
              </div>

              <div class="hero-control-panel">
                <div class="hero-school-switcher hero-school-switcher--portal">
                  <span class="panel-note">当前浏览学校</span>
                  <el-select v-model="selectedSchoolCode" class="school-select" size="large">
                    <el-option
                      v-for="school in portal.schools"
                      :key="school.code"
                      :label="school.name"
                      :value="school.code"
                    />
                  </el-select>
                </div>

                <div class="feature-pill-row feature-pill-row--portal">
                  <el-tag
                    v-for="feature in portal.platform_highlights"
                    :key="feature.title"
                    effect="plain"
                    round
                    class="hero-tag hero-tag--portal"
                  >
                    {{ feature.title }}
                  </el-tag>
                </div>
              </div>
            </div>

            <article class="hero-spotlight-panel">
              <div class="hero-spotlight-panel__head">
                <span class="hero-spotlight-chip">本期主推学校</span>
                <el-tag effect="plain" round>{{ selectedSchool.grade_scope }}</el-tag>
              </div>

              <div class="hero-spotlight-panel__school">
                <div class="hero-spotlight-panel__district">
                  <el-icon><LocationInformation /></el-icon>
                  <span>{{ selectedSchool.district }}</span>
                </div>
                <h3>{{ selectedSchool.name }}</h3>
                <p>{{ selectedSchool.slogan }}</p>
              </div>

              <div class="hero-spotlight-list">
                <div
                  v-for="feature in portalHighlights"
                  :key="feature.title"
                  class="hero-spotlight-item"
                >
                  <span class="hero-spotlight-item__icon">
                    <el-icon><component :is="feature.icon" /></el-icon>
                  </span>
                  <div>
                    <strong>{{ feature.title }}</strong>
                    <p>{{ feature.description }}</p>
                  </div>
                </div>
              </div>
            </article>
          </div>

          <article class="hero-school-stage hero-school-stage--portal">
            <div class="hero-school-stage__summary">
              <div class="hero-school-stage__head">
                <div>
                  <p class="panel-kicker">{{ selectedSchool.district }}</p>
                  <h3>{{ selectedSchool.name }}</h3>
                </div>

                <div class="hero-stage-badges">
                  <el-tag effect="dark" round>{{ selectedSchool.grade_scope }}</el-tag>
                  <span class="hero-stage-theme">
                    <span
                      v-for="color in [selectedSchool.theme.primary, selectedSchool.theme.secondary, selectedSchool.theme.accent]"
                      :key="color"
                      class="hero-stage-theme__dot"
                      :style="{ background: color }"
                    />
                    校园主题
                  </span>
                </div>
              </div>

              <p class="hero-school-stage__slogan">{{ selectedSchool.slogan }}</p>

              <div class="tag-row tag-row--portal">
                <span class="school-code-pill">{{ selectedSchool.code }}</span>
                <span class="school-code-pill">{{ selectedSchool.district }}</span>
                <span class="school-code-pill">{{ selectedSchool.grade_scope }}</span>
              </div>
            </div>

            <div class="hero-stage-metrics hero-stage-metrics--portal">
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

            <div class="hero-stage-feature-list">
              <div
                v-for="feature in selectedSchoolFeatures"
                :key="feature.title"
                class="hero-stage-feature-chip"
              >
                <span class="hero-stage-feature-chip__icon">
                  <el-icon><component :is="feature.icon" /></el-icon>
                </span>
                <strong>{{ feature.title }}</strong>
              </div>
            </div>
          </article>
        </div>
      </el-card>

      <el-card
        class="panel-card login-panel login-panel--portal login-panel--portal-refined"
        :style="schoolThemeStyle(selectedSchool.theme)"
        shadow="never"
      >
        <template #header>
          <div class="panel-head">
            <div>
              <p class="panel-kicker">统一登录</p>
              <h3>进入教学平台</h3>
            </div>
            <el-tag round effect="plain">学校专属入口</el-tag>
          </div>
        </template>

        <div class="login-panel__school-brief">
          <div class="login-panel__school-chip">
            <span class="login-panel__school-dot" />
            <span>{{ selectedSchool.district }} · {{ selectedSchool.name }}</span>
          </div>
          <p class="panel-note">教师进入工作台，学生进入学习中心，所有课程与数据按学校边界隔离。</p>
        </div>

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

        <div class="demo-button-row demo-button-row--portal">
          <el-button round @click="useDemo('teacher')">教师演示账号</el-button>
          <el-button round @click="useDemo('student')">学生演示账号</el-button>
          <el-button round @click="applicationDialogVisible = true">学校申请入驻</el-button>
        </div>

        <div class="login-panel__helper-list">
          <div class="login-panel__helper-item">
            <el-icon><Management /></el-icon>
            <span>教师端聚合课程发布、机房上课、讲评导出与 AI 备课。</span>
          </div>
          <div class="login-panel__helper-item">
            <el-icon><DataAnalysis /></el-icon>
            <span>学生端聚合课程目录、总分成绩、作品提交与成长图表。</span>
          </div>
        </div>

        <p class="panel-note">当前演示账号仅开放在「行知信息科技实验学校」。</p>
        <p v-if="errorMessage" class="status-text status-text--error">{{ errorMessage }}</p>
      </el-card>
    </section>

    <section class="portal-grid portal-grid--refined">
      <el-card
        class="panel-card school-focus-card school-focus-card--portal"
        :style="schoolThemeStyle(selectedSchool.theme)"
        shadow="hover"
      >
        <template #header>
          <div class="panel-head">
            <div class="panel-head__title">
              <span class="panel-icon">
                <el-icon><Reading /></el-icon>
              </span>
              <div>
                <p class="panel-kicker">{{ selectedSchool.district }}</p>
                <h3>{{ selectedSchool.name }}</h3>
              </div>
            </div>
            <el-tag effect="plain" round>{{ selectedSchool.grade_scope }}</el-tag>
          </div>
        </template>

        <div class="school-focus-layout">
          <div class="school-story school-story--editorial">
            <p class="school-slogan">{{ selectedSchool.slogan }}</p>
            <p class="school-story__lead">门户先展示学校的课程主题，再把教师和学生送入各自沉浸式的课程空间。</p>
            <p class="panel-note">
              当前学校可保留自己的机房管理习惯、课程活动节奏和配色主题，同时复用统一的 AI 作业、图表分析和智能体能力。
            </p>

            <div class="tag-row tag-row--portal">
              <span class="school-code-pill">{{ selectedSchool.code }}</span>
              <span class="school-code-pill">{{ selectedSchool.district }}</span>
              <span class="school-code-pill">{{ selectedSchool.grade_scope }}</span>
            </div>
          </div>

          <div class="school-feature-grid school-feature-grid--portal">
            <article
              v-for="(feature, index) in selectedSchoolFeatures"
              :key="feature.title"
              class="mini-panel mini-panel--portal"
              :class="{ 'mini-panel--wide': index === selectedSchoolFeatures.length - 1 && selectedSchoolFeatures.length % 2 === 1 }"
            >
              <span class="mini-panel__icon">
                <el-icon><component :is="feature.icon" /></el-icon>
              </span>
              <div>
                <p class="panel-kicker">学校亮点</p>
                <h4>{{ feature.title }}</h4>
                <p class="panel-note">{{ feature.description }}</p>
              </div>
            </article>
          </div>
        </div>
      </el-card>

      <el-card class="panel-card announcement-card announcement-card--portal" shadow="hover">
        <template #header>
          <div class="panel-head">
            <div class="panel-head__title">
              <span class="panel-icon">
                <el-icon><Opportunity /></el-icon>
              </span>
              <div>
                <p class="panel-kicker">校园动态</p>
                <h3>公告与平台更新</h3>
              </div>
            </div>
            <el-tag effect="plain" round>{{ portal.announcements.length }} 条</el-tag>
          </div>
        </template>

        <div class="announcement-stack">
          <article
            v-for="announcement in portal.announcements"
            :key="`${announcement.tag}-${announcement.title}`"
            class="announcement-entry"
          >
            <div class="announcement-entry__date">
              <span>{{ formatMonth(announcement.published_at) }}</span>
              <strong>{{ formatDay(announcement.published_at) }}</strong>
            </div>
            <div class="announcement-entry__body">
              <div class="announcement-entry__head">
                <el-tag size="small" round>{{ announcement.tag }}</el-tag>
                <span class="announcement-entry__status">已发布</span>
              </div>
              <strong>{{ announcement.title }}</strong>
              <p class="panel-note">{{ announcement.summary }}</p>
            </div>
          </article>
        </div>
      </el-card>
    </section>

    <section class="school-gallery school-gallery--portal">
      <div class="gallery-head gallery-head--portal">
        <div>
          <p class="panel-kicker">学校特色</p>
          <h3>不同学校可共用平台能力，但保留自己的展示风格</h3>
        </div>
        <p class="panel-note">点击卡片即可切换当前门户学校与主题色。</p>
      </div>

      <div class="school-card-row school-card-row--portal">
        <el-card
          v-for="school in portal.schools"
          :key="school.code"
          class="panel-card school-gallery-card"
          :class="{ 'school-gallery-card--active': school.code === selectedSchoolCode }"
          :style="schoolThemeStyle(school.theme)"
          shadow="hover"
          @click="selectedSchoolCode = school.code"
        >
          <span class="school-gallery-card__accent" />
          <div class="school-gallery-card__header">
            <div>
              <strong>{{ school.name }}</strong>
              <p class="panel-note">{{ school.district }} · {{ school.grade_scope }}</p>
            </div>
            <el-tag round effect="plain">
              {{ school.code === selectedSchoolCode ? "当前学校" : "切换学校" }}
            </el-tag>
          </div>
          <p class="panel-note">{{ school.slogan }}</p>

          <div class="school-gallery-card__metrics">
            <div
              v-for="metric in school.metrics.slice(0, 2)"
              :key="metric.title"
              class="school-gallery-card__metric"
            >
              <strong>{{ metric.value }}</strong>
              <span>{{ metric.title }}</span>
            </div>
          </div>

          <ul class="feature-list feature-list--portal">
            <li v-for="feature in school.features.slice(0, 2)" :key="feature.title">{{ feature.title }}</li>
          </ul>
        </el-card>
      </div>
    </section>

    <el-dialog v-model="applicationDialogVisible" title="学校申请入驻" width="620px">
      <el-form label-position="top">
        <div class="workflow-grid">
          <div class="workflow-panel">
            <el-form-item label="学校名称">
              <el-input v-model="schoolApplicationForm.school_name" />
            </el-form-item>
            <el-form-item label="学校编码">
              <el-input v-model="schoolApplicationForm.school_code" placeholder="建议使用英文或拼音缩写" />
            </el-form-item>
            <el-form-item label="所在区">
              <el-input v-model="schoolApplicationForm.district" />
            </el-form-item>
            <el-form-item label="覆盖学段">
              <el-input v-model="schoolApplicationForm.grade_scope" />
            </el-form-item>
            <el-form-item label="学校标语">
              <el-input v-model="schoolApplicationForm.slogan" type="textarea" :rows="2" />
            </el-form-item>
          </div>

          <div class="workflow-panel workflow-panel--aside">
            <el-form-item label="联系人">
              <el-input v-model="schoolApplicationForm.contact_name" />
            </el-form-item>
            <el-form-item label="联系电话">
              <el-input v-model="schoolApplicationForm.contact_phone" />
            </el-form-item>
            <el-form-item label="首位管理员姓名">
              <el-input v-model="schoolApplicationForm.applicant_display_name" />
            </el-form-item>
            <el-form-item label="首位管理员账号">
              <el-input v-model="schoolApplicationForm.applicant_username" />
            </el-form-item>
            <el-form-item label="首位管理员密码">
              <el-input v-model="schoolApplicationForm.applicant_password" show-password />
            </el-form-item>
            <el-form-item label="补充说明">
              <el-input v-model="schoolApplicationForm.note" type="textarea" :rows="3" />
            </el-form-item>
          </div>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-actions">
          <el-button @click="applicationDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="applicationSubmitting" @click="handleSubmitSchoolApplication">
            提交申请
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>

  <el-skeleton v-else animated :rows="8" />
</template>

<script setup lang="ts">
import {
  DataAnalysis,
  DataLine,
  LocationInformation,
  MagicStick,
  Management,
  Monitor,
  Opportunity,
  Reading,
  School
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { reactive } from "vue";
import type { Component } from "vue";
import { useRouter } from "vue-router";

import { api } from "../api/client";
import { useSessionStore } from "../stores/session";
import type { PortalResponse, ThemePalette } from "../types/contracts";

interface PortalFeatureWithIcon {
  title: string;
  description: string;
  icon: Component;
}

const router = useRouter();
const session = useSessionStore();

const portalHighlightIcons: Component[] = [School, MagicStick, DataLine];
const schoolFeatureIcons: Component[] = [Monitor, MagicStick, Reading];

const portal = ref<PortalResponse | null>(null);
const selectedSchoolCode = ref("");
const username = ref("");
const password = ref("");
const errorMessage = ref("");
const loading = ref(false);
const applicationDialogVisible = ref(false);
const applicationSubmitting = ref(false);
const schoolApplicationForm = reactive({
  school_name: "",
  school_code: "",
  district: "",
  grade_scope: "",
  slogan: "",
  contact_name: "",
  contact_phone: "",
  applicant_display_name: "",
  applicant_username: "",
  applicant_password: "",
  note: ""
});

const selectedSchool = computed(() => {
  if (!portal.value) {
    return null;
  }
  return (
    portal.value.schools.find((school) => school.code === selectedSchoolCode.value) ??
    portal.value.schools[0]
  );
});

const portalHighlights = computed<PortalFeatureWithIcon[]>(() =>
  (portal.value?.platform_highlights ?? []).map((feature, index) => ({
    ...feature,
    icon: portalHighlightIcons[index % portalHighlightIcons.length]
  }))
);

const selectedSchoolFeatures = computed<PortalFeatureWithIcon[]>(() =>
  (selectedSchool.value?.features ?? []).map((feature, index) => ({
    ...feature,
    icon: schoolFeatureIcons[index % schoolFeatureIcons.length]
  }))
);

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

function schoolThemeStyle(theme: ThemePalette) {
  return {
    "--school-primary": theme.primary,
    "--school-secondary": theme.secondary,
    "--school-accent": theme.accent
  };
}

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
    const nextPath =
      user.role === "teacher"
        ? "/teacher"
        : user.role === "student"
          ? "/student"
          : user.role === "school_admin"
            ? "/school-admin"
            : "/admin";
    await router.push(nextPath);
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

async function handleSubmitSchoolApplication() {
  applicationSubmitting.value = true;
  try {
    const response = await api.createSchoolApplication({
      school_name: schoolApplicationForm.school_name.trim(),
      school_code: schoolApplicationForm.school_code.trim(),
      district: schoolApplicationForm.district.trim(),
      grade_scope: schoolApplicationForm.grade_scope.trim(),
      slogan: schoolApplicationForm.slogan.trim(),
      contact_name: schoolApplicationForm.contact_name.trim(),
      contact_phone: schoolApplicationForm.contact_phone.trim(),
      applicant_display_name: schoolApplicationForm.applicant_display_name.trim(),
      applicant_username: schoolApplicationForm.applicant_username.trim(),
      applicant_password: schoolApplicationForm.applicant_password,
      note: schoolApplicationForm.note.trim() || null
    });
    ElMessage.success(response.message);
    applicationDialogVisible.value = false;
    schoolApplicationForm.school_name = "";
    schoolApplicationForm.school_code = "";
    schoolApplicationForm.district = "";
    schoolApplicationForm.grade_scope = "";
    schoolApplicationForm.slogan = "";
    schoolApplicationForm.contact_name = "";
    schoolApplicationForm.contact_phone = "";
    schoolApplicationForm.applicant_display_name = "";
    schoolApplicationForm.applicant_username = "";
    schoolApplicationForm.applicant_password = "";
    schoolApplicationForm.note = "";
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "提交申请失败");
  } finally {
    applicationSubmitting.value = false;
  }
}

function formatMonth(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit"
  }).format(new Date(value));
}

function formatDay(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    day: "2-digit"
  }).format(new Date(value));
}
</script>
