<template>
  <div v-if="!session.user || session.user.role !== 'school_admin'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录学校管理员账号进入学校后台">
        <el-button type="primary" round @click="loginDemo">使用学校管理员演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div v-else-if="dashboard" class="workspace-page workspace-page--immersive portal-admin-page">
    <section class="workspace-hero workspace-hero--teacher workspace-hero--admin">
      <div>
        <p class="panel-kicker">School Admin</p>
        <h2>{{ dashboard.admin_name }} · {{ dashboard.tenant_name }}</h2>
        <p class="hero-copy">在这里维护本校门户资料、学校主题和教师成员。首位入驻申请人默认成为学校管理员，后续可在成员列表中继续设置管理员。</p>
      </div>
      <div class="workspace-hero__panel">
        <div class="hero-actions">
          <el-button round @click="router.push('/')">查看门户首页</el-button>
          <el-button type="primary" round :loading="schoolSaving" @click="handleSaveProfile">保存学校资料</el-button>
        </div>
      </div>
    </section>

    <div class="stats-grid">
      <StatCard v-for="item in dashboard.quick_stats" :key="item.title" :title="item.title" :value="item.value" :hint="item.hint">
        <template #icon><el-icon><component :is="schoolStatIcon(item.title)" /></el-icon></template>
      </StatCard>
    </div>

    <div class="portal-admin-layout">
      <div class="detail-stack">
        <SectionCard eyebrow="学校资料" title="本校门户配置">
          <template #icon><el-icon><School /></el-icon></template>
          <div class="workflow-panel">
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
                  <strong>学校亮点</strong>
                  <el-button text @click="schoolForm.features.push({ title: '', description: '' })">新增亮点</el-button>
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
                <strong>学校指标</strong>
                <el-button text @click="schoolForm.metrics.push({ title: '', value: '', hint: '' })">新增指标</el-button>
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
        </SectionCard>

        <SectionCard eyebrow="成员管理" title="教师与管理员">
          <template #icon><el-icon><UserFilled /></el-icon></template>
          <div class="workflow-grid">
            <div class="workflow-panel">
              <div class="workflow-panel__head">
                <div>
                  <p class="panel-kicker">新增教师</p>
                  <h4>创建本校教师账号</h4>
                </div>
                <el-button type="primary" :loading="staffSaving" @click="handleCreateTeacher">添加教师</el-button>
              </div>
              <el-form label-position="top">
                <el-form-item label="教师姓名">
                  <el-input v-model="teacherForm.display_name" />
                </el-form-item>
                <el-form-item label="登录账号">
                  <el-input v-model="teacherForm.username" />
                </el-form-item>
                <el-form-item label="初始密码">
                  <el-input v-model="teacherForm.password" show-password />
                </el-form-item>
                <el-form-item label="任教学科">
                  <el-input v-model="teacherForm.subject" />
                </el-form-item>
                <el-form-item label="职称">
                  <el-input v-model="teacherForm.title" />
                </el-form-item>
                <el-form-item label="教师编号">
                  <el-input v-model="teacherForm.teacher_no" placeholder="留空则自动生成" />
                </el-form-item>
              </el-form>
            </div>

            <div class="workflow-panel workflow-panel--aside">
              <div class="workflow-panel__head">
                <div>
                  <p class="panel-kicker">成员列表</p>
                  <h4>{{ dashboard.staff_members.length }} 位本校成员</h4>
                </div>
              </div>
              <div class="info-list">
                <div v-for="item in dashboard.staff_members" :key="item.id" class="info-list-item">
                  <div>
                    <strong>{{ item.display_name }}</strong>
                    <p class="panel-note">
                      {{ item.username }} · {{ item.subject || "学校管理" }} · {{ item.teacher_no || "未设置编号" }}
                    </p>
                  </div>
                  <div class="hero-actions">
                    <el-tag round :type="item.role === 'school_admin' ? 'success' : 'info'">
                      {{ item.role === "school_admin" ? "学校管理员" : "教师" }}
                    </el-tag>
                    <el-button
                      size="small"
                      round
                      :loading="roleSavingUserId === item.id"
                      @click="handleToggleRole(item)"
                    >
                      {{ item.role === "school_admin" ? "设为教师" : "设为管理员" }}
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </SectionCard>
      </div>

      <div class="portal-admin-side">
        <SectionCard eyebrow="即时预览" title="学校门户预览">
          <template #icon><el-icon><View /></el-icon></template>
          <div class="portal-preview" :style="previewVars">
            <p class="panel-kicker">School Preview</p>
            <h3>{{ schoolForm.name }}</h3>
            <p class="panel-note">{{ schoolForm.slogan }}</p>
            <div class="portal-preview__school">
              <h4>{{ schoolForm.district }}</h4>
              <p>{{ schoolForm.grade_scope }}</p>
              <div class="tag-row">
                <el-tag round>{{ dashboard.school.code }}</el-tag>
                <el-tag round effect="plain">{{ schoolForm.grade_scope }}</el-tag>
              </div>
            </div>
          </div>
        </SectionCard>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { DataBoard, School, UserFilled, View } from "@element-plus/icons-vue";

import { api } from "../api/client";
import SectionCard from "../components/SectionCard.vue";
import StatCard from "../components/StatCard.vue";
import type { SchoolAdminDashboardResponse, SchoolStaffMember } from "../types/contracts";
import { useSessionStore } from "../stores/session";

const router = useRouter();
const session = useSessionStore();

const dashboard = ref<SchoolAdminDashboardResponse | null>(null);
const schoolSaving = ref(false);
const staffSaving = ref(false);
const roleSavingUserId = ref<number | null>(null);

const schoolForm = reactive({
  name: "",
  district: "",
  slogan: "",
  grade_scope: "",
  theme: { primary: "#2F6FED", secondary: "#14B8A6", accent: "#F59E0B" },
  features: [] as Array<{ title: string; description: string }>,
  metrics: [] as Array<{ title: string; value: string; hint: string }>
});

const teacherForm = reactive({
  display_name: "",
  username: "",
  password: "",
  subject: "信息科技",
  title: "",
  teacher_no: ""
});

const previewVars = computed(() => ({
  "--preview-primary": schoolForm.theme.primary,
  "--preview-secondary": schoolForm.theme.secondary,
  "--preview-accent": schoolForm.theme.accent
}));

onMounted(async () => {
  if (session.user?.role === "school_admin") {
    await loadDashboard();
  }
});

watch(
  () => session.user?.id,
  async (value) => {
    if (value && session.user?.role === "school_admin") {
      await loadDashboard();
    }
  }
);

function schoolStatIcon(title: string) {
  if (title.includes("学校") || title.includes("编码")) {
    return School;
  }
  return DataBoard;
}

async function loginDemo() {
  await session.login("xingzhiadmin", "444444", "xingzhi-school");
  await router.replace("/school-admin");
  await loadDashboard();
}

async function loadDashboard() {
  if (!session.user) {
    return;
  }
  dashboard.value = await api.getSchoolAdminDashboard(session.user.id);
  schoolForm.name = dashboard.value.school.name;
  schoolForm.district = dashboard.value.school.district;
  schoolForm.slogan = dashboard.value.school.slogan;
  schoolForm.grade_scope = dashboard.value.school.grade_scope;
  schoolForm.theme = { ...dashboard.value.school.theme };
  schoolForm.features = dashboard.value.school.features.map((item) => ({ ...item }));
  schoolForm.metrics = dashboard.value.school.metrics.map((item) => ({ ...item }));
}

async function handleSaveProfile() {
  if (!session.user) {
    return;
  }
  schoolSaving.value = true;
  try {
    await api.updateSchoolProfile({
      admin_user_id: session.user.id,
      name: schoolForm.name.trim(),
      district: schoolForm.district.trim(),
      slogan: schoolForm.slogan.trim(),
      grade_scope: schoolForm.grade_scope.trim(),
      theme: { ...schoolForm.theme },
      features: schoolForm.features.filter((item) => item.title.trim() && item.description.trim()),
      metrics: schoolForm.metrics.filter((item) => item.title.trim() && item.value.trim())
    });
    ElMessage.success("学校资料已保存");
    await loadDashboard();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    schoolSaving.value = false;
  }
}

async function handleCreateTeacher() {
  if (!session.user) {
    return;
  }
  staffSaving.value = true;
  try {
    await api.createSchoolTeacher({
      admin_user_id: session.user.id,
      username: teacherForm.username.trim(),
      password: teacherForm.password,
      display_name: teacherForm.display_name.trim(),
      subject: teacherForm.subject.trim(),
      title: teacherForm.title.trim() || null,
      teacher_no: teacherForm.teacher_no.trim() || null
    });
    ElMessage.success("教师账号已创建");
    teacherForm.display_name = "";
    teacherForm.username = "";
    teacherForm.password = "";
    teacherForm.subject = "信息科技";
    teacherForm.title = "";
    teacherForm.teacher_no = "";
    await loadDashboard();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "创建失败");
  } finally {
    staffSaving.value = false;
  }
}

async function handleToggleRole(item: SchoolStaffMember) {
  if (!session.user) {
    return;
  }
  roleSavingUserId.value = item.id;
  try {
    await api.updateSchoolStaffRole(item.id, {
      admin_user_id: session.user.id,
      role: item.role === "school_admin" ? "teacher" : "school_admin"
    });
    ElMessage.success("成员权限已更新");
    await loadDashboard();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "更新失败");
  } finally {
    roleSavingUserId.value = null;
  }
}
</script>
