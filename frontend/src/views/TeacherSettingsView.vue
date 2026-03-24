<template>
  <div v-if="!session.user || session.user.role !== 'teacher'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录教师账号进入信息设置">
        <el-button type="primary" round @click="loginDemo">使用教师演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div v-else-if="settings" class="settings-page">
    <section class="workspace-hero workspace-hero--teacher">
      <div>
        <p class="panel-kicker">{{ settings.user.tenant_name }}</p>
        <h2>{{ settings.user.display_name }} · 教师信息设置</h2>
        <p class="hero-copy">
          这里用于维护教师姓名、学科、职称和课程智能体默认形象。保存后，工作台和助手抽屉会同步更新。
        </p>
      </div>
      <div class="workspace-hero__panel">
        <div class="hero-actions">
          <el-button round @click="router.push('/teacher')">返回教师工作台</el-button>
          <el-button type="primary" round :loading="saving" @click="handleSave">保存设置</el-button>
        </div>
      </div>
    </section>

    <div class="stats-grid">
      <StatCard title="教师号" :value="settings.teacher_no" hint="教师档案编号">
        <template #icon><el-icon><School /></el-icon></template>
      </StatCard>
      <StatCard title="任教学科" :value="settings.subject" hint="用于课程智能体上下文识别">
        <template #icon><el-icon><Reading /></el-icon></template>
      </StatCard>
      <StatCard title="职称" :value="settings.title ?? '--'" hint="教师职称与角色标签">
        <template #icon><el-icon><Medal /></el-icon></template>
      </StatCard>
      <StatCard title="默认形象" :value="selectedOption?.animal ?? '--'" hint="课程与通用助手的默认门面">
        <template #icon><el-icon><MagicStick /></el-icon></template>
      </StatCard>
    </div>

    <div class="settings-shell">
      <SectionCard eyebrow="基础资料" title="教师信息">
        <template #icon><el-icon><EditPen /></el-icon></template>
        <el-form label-position="top">
          <el-form-item label="登录账号">
            <el-input :model-value="settings.user.username" disabled />
          </el-form-item>
          <el-form-item label="显示姓名">
            <el-input v-model="form.display_name" maxlength="20" show-word-limit />
          </el-form-item>
          <el-form-item label="任教学科">
            <el-input v-model="form.subject" />
          </el-form-item>
          <el-form-item label="教师职称">
            <el-input v-model="form.title" />
          </el-form-item>
        </el-form>
      </SectionCard>

      <SectionCard eyebrow="智能体形象" title="选择教师助手默认卡通形象">
        <template #icon><el-icon><MagicStick /></el-icon></template>
        <div class="settings-preview">
          <ZodiacAgentAvatar :animal-key="selectedAvatarKey" :show-label="true" />
          <div class="step-note">
            <p>当前已选：{{ selectedOption?.label ?? "未选择" }}</p>
            <p>{{ selectedOption?.description ?? "可为教师工作台与课程助手挑选默认形象。" }}</p>
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
import { EditPen, MagicStick, Medal, Reading, School } from "@element-plus/icons-vue";

import { api } from "../api/client";
import SectionCard from "../components/SectionCard.vue";
import StatCard from "../components/StatCard.vue";
import ZodiacAgentAvatar from "../components/ZodiacAgentAvatar.vue";
import { useSessionStore } from "../stores/session";
import type { TeacherSettingsResponse } from "../types/contracts";

const router = useRouter();
const session = useSessionStore();

const settings = ref<TeacherSettingsResponse | null>(null);
const saving = ref(false);
const selectedAvatarKey = ref<string | null>("dragon");
const form = reactive({
  display_name: "",
  subject: "",
  title: "",
});

const selectedOption = computed(() => {
  return settings.value?.zodiac_options.find((item) => item.key === selectedAvatarKey.value) ?? null;
});

onMounted(async () => {
  if (session.user?.role === "teacher") {
    await loadSettings();
  }
});

watch(
  () => session.user?.id,
  async (value) => {
    if (value && session.user?.role === "teacher") {
      await loadSettings();
    }
  },
);

async function loginDemo() {
  await session.login("kylin", "222221", "xingzhi-school");
  await router.replace("/teacher/settings");
  await loadSettings();
}

async function loadSettings() {
  if (!session.user) {
    return;
  }
  settings.value = await api.getTeacherSettings(session.user.id);
  form.display_name = settings.value.user.display_name;
  form.subject = settings.value.subject;
  form.title = settings.value.title ?? "";
  selectedAvatarKey.value = settings.value.user.avatar ?? settings.value.zodiac_options[0]?.key ?? "dragon";
}

async function handleSave() {
  if (!session.user) {
    return;
  }
  saving.value = true;
  try {
    const response = await api.updateTeacherSettings({
      user_id: session.user.id,
      display_name: form.display_name.trim(),
      subject: form.subject.trim(),
      title: form.title.trim() || null,
      avatar: selectedAvatarKey.value,
    });
    settings.value = response;
    session.setUser(response.user);
    ElMessage.success("教师设置已保存");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}
</script>
