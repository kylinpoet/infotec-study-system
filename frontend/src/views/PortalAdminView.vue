<template>
  <div v-if="!session.user || session.user.role !== 'admin'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录门户管理员账号进入后台">
        <el-button type="primary" round @click="loginDemo">使用门户管理员演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div v-else-if="dashboard" class="workspace-page">
    <section class="workspace-hero workspace-hero--teacher">
      <div>
        <p class="panel-kicker">Portal Admin</p>
        <h2>{{ dashboard.admin_name }} · 门户管理后台</h2>
        <p class="hero-copy">
          在这里统一维护门户首屏文案、多校学校资料、主题配色和公告内容。保存后，学校门户首页会同步显示最新内容。
        </p>
      </div>
      <div class="workspace-hero__panel">
        <div class="hero-actions">
          <el-button round @click="router.push('/')">查看门户首页</el-button>
          <el-button type="primary" round :loading="heroSaving" @click="handleSaveHero">保存首屏配置</el-button>
        </div>
      </div>
    </section>

    <div class="stats-grid">
      <StatCard v-for="item in dashboard.quick_stats" :key="item.title" :title="item.title" :value="item.value" :hint="item.hint">
        <template #icon><el-icon><component :is="adminStatIcon(item.title)" /></el-icon></template>
      </StatCard>
    </div>

    <div class="portal-admin-layout">
      <div class="detail-stack">
        <SectionCard eyebrow="门户首屏" title="主视觉与默认学校">
          <template #icon><el-icon><Monitor /></el-icon></template>
          <el-form label-position="top">
            <el-form-item label="门户标题">
              <el-input v-model="heroForm.hero_title" />
            </el-form-item>
            <el-form-item label="门户副标题">
              <el-input v-model="heroForm.hero_subtitle" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="默认主推学校">
              <el-select v-model="heroForm.featured_school_code" class="fill-button">
                <el-option v-for="school in dashboard.schools" :key="school.code" :label="school.name" :value="school.code" />
              </el-select>
            </el-form-item>
          </el-form>
        </SectionCard>

        <SectionCard eyebrow="大模型配置" title="AI 接口与模型参数">
          <template #icon><el-icon><Setting /></el-icon></template>
          <div class="workflow-panel workflow-panel--aside">
            <div class="workflow-panel__head">
              <div>
                <p class="panel-kicker">模型连接</p>
                <h4>{{ llmForm.model_name || "未配置模型" }}</h4>
              </div>
              <el-button type="primary" :loading="llmSaving" @click="handleSaveLlmConfig">保存模型配置</el-button>
            </div>

            <el-form label-position="top">
              <el-form-item label="启用大模型">
                <el-switch v-model="llmForm.is_enabled" active-text="启用" inactive-text="停用" />
              </el-form-item>

              <div class="workflow-grid">
                <div class="workflow-panel">
                  <el-form-item label="接口标识">
                    <el-input
                      v-model="llmForm.provider_name"
                      placeholder="例如：OpenAI Compatible / DashScope / DeepSeek"
                    />
                  </el-form-item>
                  <el-form-item label="Base URL">
                    <el-input
                      v-model="llmForm.base_url"
                      placeholder="例如：https://api.openai.com/v1"
                    />
                  </el-form-item>
                  <el-form-item label="API Key">
                    <el-input
                      v-model="llmForm.api_key"
                      show-password
                      placeholder="留空则保留当前密钥"
                    />
                  </el-form-item>
                  <p class="panel-note">
                    当前状态：{{ llmForm.has_api_key ? `已保存 ${llmForm.api_key_masked}` : "尚未保存 API Key" }}
                  </p>
                  <el-checkbox v-model="llmForm.clear_api_key">清空已保存的 API Key</el-checkbox>
                </div>

                <div class="workflow-panel">
                  <el-form-item label="模型名称">
                    <el-select
                      v-model="llmForm.model_name"
                      class="fill-button"
                      filterable
                      allow-create
                      default-first-option
                    >
                      <el-option
                        v-for="item in llmForm.model_options"
                        :key="item.value"
                        :label="item.provider_hint ? `${item.label} · ${item.provider_hint}` : item.label"
                        :value="item.value"
                      />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="Temperature">
                    <el-slider v-model="llmForm.temperature" :min="0" :max="2" :step="0.1" show-input />
                  </el-form-item>
                  <el-form-item label="Max Tokens">
                    <el-input-number v-model="llmForm.max_tokens" :min="256" :max="32768" :step="256" class="fill-button" />
                  </el-form-item>
                </div>
              </div>

              <el-form-item label="补充说明">
                <el-input
                  v-model="llmForm.notes"
                  type="textarea"
                  :rows="3"
                  placeholder="例如：课程智能体允许联网，作业生成优先使用该模型。"
                />
              </el-form-item>
            </el-form>
          </div>
        </SectionCard>

        <SectionCard eyebrow="学校资料" title="多校门户编辑">
          <template #icon><el-icon><School /></el-icon></template>
          <div class="course-activity-layout">
            <aside class="activity-outline">
              <button
                v-for="school in dashboard.schools"
                :key="school.code"
                type="button"
                class="activity-outline-card"
                :class="{ 'activity-outline-card--active': selectedSchoolCode === school.code }"
                @click="selectSchool(school.code)"
              >
                <div class="activity-card__header">
                  <div>
                    <p class="panel-kicker">{{ school.code }}</p>
                    <strong>{{ school.name }}</strong>
                  </div>
                  <el-tag round effect="plain">{{ school.district }}</el-tag>
                </div>
                <p class="panel-note">{{ school.slogan }}</p>
              </button>
            </aside>

            <div class="workflow-shell" v-if="selectedSchool">
              <div class="workflow-panel">
                <div class="workflow-panel__head">
                  <div>
                    <p class="panel-kicker">学校资料</p>
                    <h4>{{ selectedSchool.name }}</h4>
                  </div>
                  <el-button type="primary" :loading="schoolSaving" @click="handleSaveSchool">保存学校资料</el-button>
                </div>
                <el-form label-position="top">
                  <el-form-item label="学校名称">
                    <el-input v-model="schoolForm.name" />
                  </el-form-item>
                  <el-form-item label="所在区">
                    <el-input v-model="schoolForm.district" />
                  </el-form-item>
                  <el-form-item label="学校标语">
                    <el-input v-model="schoolForm.slogan" type="textarea" :rows="2" />
                  </el-form-item>
                  <el-form-item label="覆盖学段">
                    <el-input v-model="schoolForm.grade_scope" />
                  </el-form-item>
                </el-form>

                <div class="workflow-grid">
                  <div class="workflow-panel">
                    <div class="workflow-panel__head">
                      <strong>主题配色</strong>
                    </div>
                    <el-form label-position="top">
                      <el-form-item label="主色">
                        <el-input v-model="schoolForm.theme.primary" />
                      </el-form-item>
                      <el-form-item label="辅助色">
                        <el-input v-model="schoolForm.theme.secondary" />
                      </el-form-item>
                      <el-form-item label="强调色">
                        <el-input v-model="schoolForm.theme.accent" />
                      </el-form-item>
                    </el-form>
                  </div>

                  <div class="workflow-panel">
                    <div class="workflow-panel__head">
                      <strong>门户亮点</strong>
                      <el-button text @click="addFeature">新增亮点</el-button>
                    </div>
                    <div class="editor-list">
                      <div v-for="(item, index) in schoolForm.features" :key="`feature-${index}`" class="editor-row">
                        <el-input v-model="item.title" placeholder="亮点标题" />
                        <el-input v-model="item.description" placeholder="亮点说明" />
                      </div>
                    </div>
                  </div>
                </div>

                <div class="workflow-panel workflow-panel--aside">
                  <div class="workflow-panel__head">
                    <strong>门户指标</strong>
                    <el-button text @click="addMetric">新增指标</el-button>
                  </div>
                  <div class="editor-list">
                    <div v-for="(item, index) in schoolForm.metrics" :key="`metric-${index}`" class="editor-row editor-row--triple">
                      <el-input v-model="item.title" placeholder="指标标题" />
                      <el-input v-model="item.value" placeholder="指标值" />
                      <el-input v-model="item.hint" placeholder="指标说明" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="门户公告" title="公告管理">
          <template #icon><el-icon><Bell /></el-icon></template>
          <div class="workflow-grid">
            <div class="workflow-panel">
              <div class="workflow-panel__head">
                <div>
                  <p class="panel-kicker">公告列表</p>
                  <h4>当前公告</h4>
                </div>
                <el-button text @click="prepareNewAnnouncement">新增公告</el-button>
              </div>
              <div class="info-list">
                <button
                  v-for="item in dashboard.announcements"
                  :key="item.id ?? item.title"
                  type="button"
                  class="activity-outline-card"
                  :class="{ 'activity-outline-card--active': selectedAnnouncementId === item.id }"
                  @click="editAnnouncement(item.id)"
                >
                  <div class="activity-card__header">
                    <strong>{{ item.title }}</strong>
                    <el-tag round :type="item.is_active ? 'success' : 'info'">{{ item.tag }}</el-tag>
                  </div>
                  <p class="panel-note">{{ item.summary }}</p>
                </button>
              </div>
            </div>

            <div class="workflow-panel">
              <div class="workflow-panel__head">
                <div>
                  <p class="panel-kicker">公告编辑</p>
                  <h4>{{ selectedAnnouncementId ? "修改公告" : "新建公告" }}</h4>
                </div>
                <el-button type="primary" :loading="announcementSaving" @click="handleSaveAnnouncement">保存公告</el-button>
              </div>
              <el-form label-position="top">
                <el-form-item label="公告标题">
                  <el-input v-model="announcementForm.title" />
                </el-form-item>
                <el-form-item label="公告标签">
                  <el-input v-model="announcementForm.tag" />
                </el-form-item>
                <el-form-item label="公告摘要">
                  <el-input v-model="announcementForm.summary" type="textarea" :rows="3" />
                </el-form-item>
                <el-form-item label="发布时间">
                  <el-date-picker
                    v-model="announcementForm.published_at"
                    type="datetime"
                    value-format="YYYY-MM-DDTHH:mm:ss"
                    class="fill-picker"
                  />
                </el-form-item>
                <el-form-item label="是否上架">
                  <el-switch v-model="announcementForm.is_active" />
                </el-form-item>
              </el-form>
            </div>
          </div>
        </SectionCard>
      </div>

      <SectionCard eyebrow="即时预览" title="门户预览">
        <template #icon><el-icon><View /></el-icon></template>
        <div class="portal-preview" :style="previewVars">
          <p class="panel-kicker">Preview</p>
          <h3>{{ heroForm.hero_title }}</h3>
          <p class="panel-note">{{ heroForm.hero_subtitle }}</p>
          <div class="portal-preview__school" v-if="selectedSchool">
            <h4>{{ schoolForm.name }}</h4>
            <p>{{ schoolForm.slogan }}</p>
            <div class="tag-row">
              <el-tag round>{{ schoolForm.district }}</el-tag>
              <el-tag round effect="plain">{{ schoolForm.grade_scope }}</el-tag>
            </div>
          </div>
        </div>
      </SectionCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Bell, Monitor, School, Setting, View } from "@element-plus/icons-vue";

import { api } from "../api/client";
import SectionCard from "../components/SectionCard.vue";
import StatCard from "../components/StatCard.vue";
import type { PortalAdminDashboardResponse, PortalAnnouncement, PortalSchoolAdminItem } from "../types/contracts";
import { useSessionStore } from "../stores/session";

const router = useRouter();
const session = useSessionStore();

const dashboard = ref<PortalAdminDashboardResponse | null>(null);
const selectedSchoolCode = ref<string>("");
const selectedAnnouncementId = ref<number | null>(null);
const heroSaving = ref(false);
const schoolSaving = ref(false);
const announcementSaving = ref(false);
const llmSaving = ref(false);

const heroForm = reactive({
  hero_title: "",
  hero_subtitle: "",
  featured_school_code: "",
});

const schoolForm = reactive({
  name: "",
  district: "",
  slogan: "",
  grade_scope: "",
  theme: { primary: "#2F6FED", secondary: "#14B8A6", accent: "#F59E0B" },
  features: [] as Array<{ title: string; description: string }>,
  metrics: [] as Array<{ title: string; value: string; hint: string }>,
});

const announcementForm = reactive({
  title: "",
  tag: "",
  summary: "",
  published_at: "",
  is_active: true,
});

const llmForm = reactive({
  provider_name: "",
  base_url: "",
  api_key: "",
  api_key_masked: "",
  has_api_key: false,
  model_name: "",
  model_options: [] as Array<{ label: string; value: string; provider_hint: string | null }>,
  temperature: 0.4,
  max_tokens: 4096,
  is_enabled: false,
  notes: "",
  clear_api_key: false,
});

const selectedSchool = computed(() => {
  return dashboard.value?.schools.find((item) => item.code === selectedSchoolCode.value) ?? null;
});

const previewVars = computed(() => ({
  "--preview-primary": schoolForm.theme.primary,
  "--preview-secondary": schoolForm.theme.secondary,
  "--preview-accent": schoolForm.theme.accent,
}));

onMounted(async () => {
  if (session.user?.role === "admin") {
    await loadDashboard();
  }
});

watch(
  () => session.user?.id,
  async (value) => {
    if (value && session.user?.role === "admin") {
      await loadDashboard();
    }
  },
);

function adminStatIcon(title: string) {
  if (title.includes("学校")) {
    return School;
  }
  if (title.includes("公告")) {
    return Bell;
  }
  if (title.includes("模型")) {
    return Setting;
  }
  return Monitor;
}

async function loginDemo() {
  await session.login("portaladmin", "333333", "xingzhi-school");
  await router.replace("/admin");
  await loadDashboard();
}

async function loadDashboard() {
  if (!session.user) {
    return;
  }
  dashboard.value = await api.getPortalAdminDashboard(session.user.id);
  heroForm.hero_title = dashboard.value.hero.hero_title;
  heroForm.hero_subtitle = dashboard.value.hero.hero_subtitle;
  heroForm.featured_school_code = dashboard.value.hero.featured_school_code ?? dashboard.value.schools[0]?.code ?? "";
  selectedSchoolCode.value = selectedSchoolCode.value || dashboard.value.schools[0]?.code || "";
  syncSchoolForm();
  syncLlmForm();
  prepareAnnouncement(dashboard.value.announcements[0] ?? null);
}

function syncSchoolForm() {
  if (!selectedSchool.value) {
    return;
  }
  schoolForm.name = selectedSchool.value.name;
  schoolForm.district = selectedSchool.value.district;
  schoolForm.slogan = selectedSchool.value.slogan;
  schoolForm.grade_scope = selectedSchool.value.grade_scope;
  schoolForm.theme = { ...selectedSchool.value.theme };
  schoolForm.features = selectedSchool.value.features.map((item) => ({ ...item }));
  schoolForm.metrics = selectedSchool.value.metrics.map((item) => ({ ...item }));
}

function selectSchool(code: string) {
  selectedSchoolCode.value = code;
  syncSchoolForm();
}

function addFeature() {
  schoolForm.features.push({ title: "", description: "" });
}

function addMetric() {
  schoolForm.metrics.push({ title: "", value: "", hint: "" });
}

function syncLlmForm() {
  if (!dashboard.value) {
    return;
  }
  llmForm.provider_name = dashboard.value.llm_config.provider_name;
  llmForm.base_url = dashboard.value.llm_config.base_url;
  llmForm.api_key = "";
  llmForm.api_key_masked = dashboard.value.llm_config.api_key_masked ?? "";
  llmForm.has_api_key = dashboard.value.llm_config.has_api_key;
  llmForm.model_name = dashboard.value.llm_config.model_name;
  llmForm.model_options = dashboard.value.llm_config.model_options.map((item) => ({ ...item }));
  llmForm.temperature = dashboard.value.llm_config.temperature;
  llmForm.max_tokens = dashboard.value.llm_config.max_tokens;
  llmForm.is_enabled = dashboard.value.llm_config.is_enabled;
  llmForm.notes = dashboard.value.llm_config.notes ?? "";
  llmForm.clear_api_key = false;
}

async function handleSaveHero() {
  if (!session.user) {
    return;
  }
  heroSaving.value = true;
  try {
    await api.updatePortalHero({
      admin_user_id: session.user.id,
      hero_title: heroForm.hero_title.trim(),
      hero_subtitle: heroForm.hero_subtitle.trim(),
      featured_school_code: heroForm.featured_school_code || null,
    });
    ElMessage.success("门户首屏已保存");
    await loadDashboard();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    heroSaving.value = false;
  }
}

async function handleSaveSchool() {
  if (!session.user || !selectedSchool.value) {
    return;
  }
  schoolSaving.value = true;
  try {
    const response = await api.updatePortalSchool(selectedSchool.value.code, {
      admin_user_id: session.user.id,
      name: schoolForm.name.trim(),
      district: schoolForm.district.trim(),
      slogan: schoolForm.slogan.trim(),
      grade_scope: schoolForm.grade_scope.trim(),
      theme: { ...schoolForm.theme },
      features: schoolForm.features.filter((item) => item.title.trim() && item.description.trim()),
      metrics: schoolForm.metrics.filter((item) => item.title.trim() && item.value.trim()),
    });
    ElMessage.success(response.message);
    await loadDashboard();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    schoolSaving.value = false;
  }
}

async function handleSaveLlmConfig() {
  if (!session.user) {
    return;
  }
  const providerName = llmForm.provider_name.trim();
  const baseUrl = llmForm.base_url.trim();
  const modelName = llmForm.model_name.trim();
  const typedApiKey = llmForm.api_key.trim();
  const hasUsableApiKey = Boolean(typedApiKey || (llmForm.has_api_key && !llmForm.clear_api_key));

  if (!providerName || !baseUrl || !modelName) {
    ElMessage.warning("请先完整填写接口标识、Base URL 和模型名称。");
    return;
  }

  try {
    new URL(baseUrl);
  } catch {
    ElMessage.warning("请输入合法的 Base URL。");
    return;
  }

  if (llmForm.is_enabled && !hasUsableApiKey) {
    ElMessage.warning("启用大模型前请先填写 API Key。");
    return;
  }

  if (llmForm.is_enabled && llmForm.clear_api_key) {
    ElMessage.warning("启用大模型时不能同时清空 API Key。");
    return;
  }

  llmSaving.value = true;
  try {
    await api.updateLlmConfig({
      admin_user_id: session.user.id,
      provider_name: providerName,
      base_url: baseUrl,
      api_key: typedApiKey || null,
      clear_api_key: llmForm.clear_api_key,
      model_name: modelName,
      temperature: llmForm.temperature,
      max_tokens: llmForm.max_tokens,
      is_enabled: llmForm.is_enabled,
      notes: llmForm.notes.trim() || null,
    });
    ElMessage.success("大模型配置已保存");
    await loadDashboard();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    llmSaving.value = false;
  }
}

function prepareAnnouncement(item: PortalAnnouncement | null) {
  selectedAnnouncementId.value = item?.id ?? null;
  announcementForm.title = item?.title ?? "";
  announcementForm.tag = item?.tag ?? "";
  announcementForm.summary = item?.summary ?? "";
  announcementForm.published_at = item?.published_at?.slice(0, 19) ?? new Date().toISOString().slice(0, 19);
  announcementForm.is_active = item?.is_active ?? true;
}

function editAnnouncement(id: number | null) {
  const item = dashboard.value?.announcements.find((entry) => entry.id === id) ?? null;
  prepareAnnouncement(item);
}

function prepareNewAnnouncement() {
  prepareAnnouncement(null);
}

async function handleSaveAnnouncement() {
  if (!session.user) {
    return;
  }
  announcementSaving.value = true;
  try {
    if (selectedAnnouncementId.value) {
      await api.updatePortalAnnouncement(selectedAnnouncementId.value, {
        admin_user_id: session.user.id,
        title: announcementForm.title.trim(),
        tag: announcementForm.tag.trim(),
        summary: announcementForm.summary.trim(),
        published_at: announcementForm.published_at,
        is_active: announcementForm.is_active,
      });
    } else {
      await api.createPortalAnnouncement({
        admin_user_id: session.user.id,
        title: announcementForm.title.trim(),
        tag: announcementForm.tag.trim(),
        summary: announcementForm.summary.trim(),
        published_at: announcementForm.published_at,
        is_active: announcementForm.is_active,
      });
    }
    ElMessage.success("门户公告已保存");
    await loadDashboard();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    announcementSaving.value = false;
  }
}
</script>
