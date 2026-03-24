<template>
  <div v-if="!session.user || session.user.role !== 'student'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录学生账号进入信息设置">
        <el-button type="primary" round @click="loginDemo">使用学生演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div v-else-if="settings" class="settings-page">
    <section class="workspace-hero workspace-hero--student">
      <div>
        <p class="panel-kicker">{{ settings.user.tenant_name }}</p>
        <h2>{{ settings.user.display_name }} · 学生信息设置</h2>
        <p class="hero-copy">
          这里可以维护学生姓名展示、查看班级学籍信息，并为你的智能体助手挑选一位十二生肖卡通形象。
        </p>
      </div>
      <div class="workspace-hero__panel">
        <div class="hero-actions">
          <el-button round @click="router.push('/student')">返回学生中心</el-button>
          <el-button type="primary" round :loading="saving" @click="handleSave">保存设置</el-button>
        </div>
      </div>
    </section>

    <div class="stats-grid">
      <StatCard title="学号" :value="settings.student_no" hint="学籍编号只读显示">
        <template #icon><el-icon><Reading /></el-icon></template>
      </StatCard>
      <StatCard title="班级" :value="settings.classroom_label" hint="当前归属班级">
        <template #icon><el-icon><School /></el-icon></template>
      </StatCard>
      <StatCard title="年级" :value="settings.grade" hint="当前学段年级">
        <template #icon><el-icon><Collection /></el-icon></template>
      </StatCard>
      <StatCard title="座位号" :value="settings.seat_no ? String(settings.seat_no) : '--'" hint="机房课堂座位编号">
        <template #icon><el-icon><Finished /></el-icon></template>
      </StatCard>
    </div>

    <div class="settings-shell">
      <SectionCard eyebrow="基础资料" title="学生信息">
        <template #icon><el-icon><EditPen /></el-icon></template>
        <el-form label-position="top">
          <el-form-item label="登录账号">
            <el-input :model-value="settings.user.username" disabled />
          </el-form-item>
          <el-form-item label="显示姓名">
            <el-input v-model="form.display_name" maxlength="20" show-word-limit />
          </el-form-item>
          <el-form-item label="智能体助手昵称">
            <el-input :model-value="selectedOption?.label ?? '未选择'" disabled />
          </el-form-item>
        </el-form>
      </SectionCard>

      <SectionCard eyebrow="生肖助手" title="选择你的智能体形象">
        <template #icon><el-icon><MagicStick /></el-icon></template>
        <div class="settings-preview">
          <ZodiacAgentAvatar :animal-key="selectedAvatarKey" :show-label="true" />
          <div class="step-note">
            <p>当前已选：{{ selectedOption?.label ?? "未选择" }}</p>
            <p>{{ selectedOption?.description ?? "从十二生肖里选一个最像你的学习搭子。" }}</p>
          </div>
        </div>
        <div class="avatar-grid">
          <button
            v-for="option in settings.zodiac_options"
            :key="option.key"
            type="button"
            class="avatar-option-card"
            :class="{ 'avatar-option-card--active': selectedAvatarKey === option.key }"
            @click="selectedAvatarKey = option.key"
          >
            <ZodiacAgentAvatar :animal-key="option.key" compact />
            <strong>{{ option.label }}</strong>
            <span>{{ option.description }}</span>
          </button>
        </div>
      </SectionCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Collection, EditPen, Finished, MagicStick, Reading, School } from "@element-plus/icons-vue";

import { api } from "../api/client";
import SectionCard from "../components/SectionCard.vue";
import StatCard from "../components/StatCard.vue";
import ZodiacAgentAvatar from "../components/ZodiacAgentAvatar.vue";
import { useSessionStore } from "../stores/session";
import type { StudentSettingsResponse } from "../types/contracts";

const router = useRouter();
const session = useSessionStore();

const settings = ref<StudentSettingsResponse | null>(null);
const saving = ref(false);
const selectedAvatarKey = ref<string | null>("rabbit");
const form = reactive({
  display_name: "",
});

const selectedOption = computed(() => {
  return settings.value?.zodiac_options.find((item) => item.key === selectedAvatarKey.value) ?? null;
});

onMounted(async () => {
  if (session.user?.role === "student") {
    await loadSettings();
  }
});

watch(
  () => session.user?.id,
  async (value) => {
    if (value && session.user?.role === "student") {
      await loadSettings();
    }
  },
);

async function loginDemo() {
  await session.login("240101", "12345", "xingzhi-school");
  await router.replace("/student/settings");
  await loadSettings();
}

async function loadSettings() {
  if (!session.user) {
    return;
  }
  settings.value = await api.getStudentSettings(session.user.id);
  form.display_name = settings.value.user.display_name;
  selectedAvatarKey.value = settings.value.user.avatar ?? settings.value.zodiac_options[0]?.key ?? "rabbit";
}

async function handleSave() {
  if (!session.user) {
    return;
  }
  saving.value = true;
  try {
    const response = await api.updateStudentSettings({
      user_id: session.user.id,
      display_name: form.display_name.trim(),
      avatar: selectedAvatarKey.value,
    });
    settings.value = response;
    session.setUser(response.user);
    ElMessage.success("学生设置已保存");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}
</script>
