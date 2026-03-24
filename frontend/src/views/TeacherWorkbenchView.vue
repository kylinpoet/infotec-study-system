<template>
  <div v-if="!session.user || session.user.role !== 'teacher'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录教师账号进入工作台">
        <el-button type="primary" round @click="loginDemo">使用教师演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div v-else-if="dashboard" class="workspace-page">
    <section class="workspace-hero workspace-hero--teacher">
      <div>
        <p class="panel-kicker">{{ dashboard.tenant_name }}</p>
        <h2>{{ dashboard.teacher_name }} · {{ dashboard.classroom_label }}</h2>
        <p class="hero-copy">
          机房课堂态势、课程列表、课程生成和图表分析都集中在这里；作业预览、作业分析和 AI 作业工坊进入课程目录查看。
        </p>
      </div>
      <div class="hero-actions">
        <el-button round @click="generalAssistantOpen = true">通用智能体</el-button>
        <el-button type="primary" round @click="createCourseDialog = true">生成课程</el-button>
      </div>
    </section>

    <div class="stats-grid">
      <StatCard
        v-for="item in dashboard.quick_stats"
        :key="item.title"
        :title="item.title"
        :value="item.value"
        :hint="item.hint"
      />
    </div>

    <el-tabs v-model="activeTab" class="workspace-tabs">
      <el-tab-pane label="工作台总览" name="overview">
        <div class="workspace-grid workspace-grid--teacher-overview">
          <SectionCard eyebrow="机房态势" title="当前机房状态">
            <div class="lab-board">
              <div class="lab-summary-column">
                <div class="lab-summary-grid">
                  <div class="status-tile">
                    <span>课堂视图</span>
                    <strong>{{ dashboard.lab_snapshot.view_mode }}</strong>
                  </div>
                  <div class="status-tile">
                    <span>签到人数</span>
                    <strong>{{ dashboard.lab_snapshot.signed_in_count }}/{{ dashboard.lab_snapshot.student_count }}</strong>
                  </div>
                  <div class="status-tile">
                    <span>已提交</span>
                    <strong>{{ dashboard.lab_snapshot.submitted_count }}</strong>
                  </div>
                  <div class="status-tile">
                    <span>待复核</span>
                    <strong>{{ dashboard.lab_snapshot.pending_review_count }}</strong>
                  </div>
                  <div class="status-tile">
                    <span>IP 锁定</span>
                    <strong>{{ dashboard.lab_snapshot.ip_lock_enabled ? "已开启" : "未开启" }}</strong>
                  </div>
                  <div class="status-tile">
                    <span>班级密码</span>
                    <strong>{{ dashboard.lab_snapshot.class_password_enabled ? "已启用" : "未启用" }}</strong>
                  </div>
                </div>
                <div class="lab-brief">
                  <p class="panel-kicker">课堂控制</p>
                  <p class="panel-note">
                    当前机房继续保留 IP 锁定、班级密码和座位视图，保证真实课堂里的签到、作答和复核闭环。
                  </p>
                </div>
              </div>
              <div class="seat-grid">
                <div v-for="seat in dashboard.lab_snapshot.seats" :key="seat.seat_no" class="seat-card">
                  <span class="seat-card__index">#{{
                    seat.seat_no.toString().padStart(2, "0")
                  }}</span>
                  <strong>{{ seat.student_name }}</strong>
                  <el-tag size="small" round>{{ seat.status }}</el-tag>
                  <p class="panel-note">{{ seat.score != null ? `${seat.score} 分` : "等待作答" }}</p>
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard eyebrow="课程目录" title="当前课程列表">
            <div class="course-list">
              <button
                v-for="course in dashboard.course_directory"
                :key="course.id"
                type="button"
                class="course-list-card"
                :class="{ 'course-list-card--active': selectedCourseId === course.id }"
                @click="selectCourse(course.id)"
              >
                <div class="course-list-card__head">
                  <strong>{{ course.title }}</strong>
                  <el-tag size="small" effect="plain">{{ course.lesson_no }}</el-tag>
                </div>
                <p class="panel-note">{{ course.subject }} · {{ course.term }}</p>
                <div class="metric-inline">
                  <span>均分 {{ course.average_score }}</span>
                  <span>提交率 {{ course.submission_rate }}%</span>
                  <span>{{ course.agent_enabled ? "已绑定课程智能体" : "未绑定课程智能体" }}</span>
                </div>
              </button>
            </div>
          </SectionCard>

          <SectionCard eyebrow="图表分析" title="教师首页图表">
            <div class="chart-grid">
              <ChartPanelCard
                v-for="panel in dashboard.charts"
                :key="panel.key"
                :panel="panel"
              />
            </div>
          </SectionCard>

          <SectionCard eyebrow="待处理" title="课堂待处理事项">
            <div class="info-list">
              <div v-for="item in dashboard.pending_items" :key="item.title" class="info-list-item">
                <div>
                  <strong>{{ item.title }}</strong>
                  <p class="panel-note">{{ item.meta }}</p>
                </div>
                <el-tag round>{{ item.status }}</el-tag>
              </div>
            </div>
          </SectionCard>
        </div>
      </el-tab-pane>

      <el-tab-pane label="课程目录" name="courses">
        <div class="directory-layout directory-layout--teacher">
          <aside class="directory-sidebar">
            <div class="sidebar-head">
              <div>
                <p class="panel-kicker">课程列表</p>
                <h3>课程目录</h3>
              </div>
            </div>
            <div class="course-list">
              <button
                v-for="course in dashboard.course_directory"
                :key="course.id"
                type="button"
                class="course-list-card"
                :class="{ 'course-list-card--active': selectedCourseId === course.id }"
                @click="selectCourse(course.id)"
              >
                <div class="course-list-card__head">
                  <strong>{{ course.title }}</strong>
                  <el-tag size="small" effect="plain">{{ course.status }}</el-tag>
                </div>
                <p class="panel-note">{{ course.lesson_no }} · 提交率 {{ course.submission_rate }}%</p>
              </button>
            </div>
          </aside>

          <section class="directory-content" v-loading="courseLoading">
            <template v-if="courseDetail">
              <div class="directory-content__head">
                <div>
                  <p class="panel-kicker">{{ courseDetail.course.lesson_no }}</p>
                  <h3>{{ courseDetail.course.title }}</h3>
                  <p class="panel-note">
                    {{ courseDetail.course.subject }} · {{ courseDetail.course.term }} · 最近更新 {{ formatDateTime(courseDetail.course.last_updated) }}
                  </p>
                </div>
                <div class="hero-actions">
                  <el-button round @click="courseAssistantOpen = true">课程智能体</el-button>
                </div>
              </div>

              <el-tabs v-model="courseTab">
                <el-tab-pane label="作业预览" name="preview">
                  <div class="detail-stack">
                    <SectionCard eyebrow="作业概览" title="当前作业预览">
                      <template v-if="currentPreview">
                        <div class="preview-summary">
                          <div>
                            <strong>{{ currentPreview.title }}</strong>
                            <p class="panel-note">{{ currentPreview.instructions }}</p>
                          </div>
                          <el-space wrap>
                            <el-tag round>题目 {{ currentPreview.question_count }}</el-tag>
                            <el-tag round effect="plain">提交 {{ currentPreview.submission_count }}</el-tag>
                            <el-tag round effect="plain">均分 {{ currentPreview.average_score }}</el-tag>
                          </el-space>
                        </div>

                        <div class="tag-row">
                          <el-tag
                            v-for="component in currentPreview.component_whitelist"
                            :key="component"
                            round
                            effect="plain"
                          >
                            {{ component }}
                          </el-tag>
                        </div>

                        <div class="question-preview-list" v-if="currentSpec">
                          <div v-for="question in currentSpec.questions" :key="question.key" class="question-preview-item">
                            <div class="question-preview-item__head">
                              <strong>{{ question.stem }}</strong>
                              <el-tag type="warning" effect="plain" round>{{ question.points }} 分</el-tag>
                            </div>
                            <p class="panel-note">{{ question.type }} · {{ question.options.join(" / ") }}</p>
                          </div>
                        </div>
                      </template>
                      <p v-else class="panel-note">该课程还没有生成作业，可以直接切到「AI 作业工坊」生成第一份作业。</p>
                    </SectionCard>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="作业分析" name="analytics">
                  <div class="detail-stack">
                    <SectionCard eyebrow="分析概览" title="作业分析">
                      <template v-if="courseDetail.analytics">
                        <div class="analytics-strip">
                          <div class="analytics-tile">
                            <span>提交人数</span>
                            <strong>{{ courseDetail.analytics.submission_count }}</strong>
                          </div>
                          <div class="analytics-tile">
                            <span>平均成绩</span>
                            <strong>{{ courseDetail.analytics.average_score }}</strong>
                          </div>
                          <div class="analytics-tile">
                            <span>平均用时</span>
                            <strong>{{ courseDetail.analytics.average_duration_min ?? "--" }} 分钟</strong>
                          </div>
                        </div>
                        <div class="chart-grid">
                          <ChartPanelCard
                            v-for="panel in courseDetail.charts"
                            :key="panel.key"
                            :panel="panel"
                          />
                        </div>
                      </template>
                      <p v-else class="panel-note">该课程暂无发布中的作业分析数据。</p>
                    </SectionCard>

                    <SectionCard eyebrow="提交回流" title="最近提交">
                      <div class="info-list">
                        <div
                          v-for="item in courseDetail.recent_submissions"
                          :key="`${item.title}-${item.meta}`"
                          class="info-list-item"
                        >
                          <div>
                            <strong>{{ item.title }}</strong>
                            <p class="panel-note">{{ item.meta }}</p>
                          </div>
                          <el-tag round>{{ item.status }}</el-tag>
                        </div>
                      </div>
                    </SectionCard>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="AI 作业工坊" name="studio">
                  <div class="detail-stack">
                    <SectionCard eyebrow="AI 作业工坊" title="生成交互式作业">
                      <el-form label-position="top">
                        <el-form-item label="作业标题">
                          <el-input v-model="draftTitle" placeholder="请输入作业标题" />
                        </el-form-item>
                        <el-form-item label="教学目标">
                          <el-input v-model="learningGoal" type="textarea" :rows="4" />
                        </el-form-item>
                        <el-form-item label="参考资料">
                          <el-input
                            v-model="resourceNames"
                            placeholder="教材页、PPT、示例截图，使用中文逗号分隔"
                          />
                        </el-form-item>
                        <el-form-item label="题型白名单">
                          <el-checkbox-group v-model="selectedComponents">
                            <el-checkbox
                              v-for="component in courseDetail.allowed_components"
                              :key="component"
                              :label="component"
                            >
                              {{ component }}
                            </el-checkbox>
                          </el-checkbox-group>
                        </el-form-item>
                        <el-form-item label="截止时间">
                          <el-date-picker
                            v-model="publishDueAt"
                            type="datetime"
                            value-format="YYYY-MM-DDTHH:mm:ss"
                            placeholder="不填则使用默认截止时间"
                            class="fill-picker"
                          />
                        </el-form-item>
                        <div class="hero-actions">
                          <el-button type="primary" :loading="draftLoading" @click="handleGenerateDraft">
                            生成 AI 作业
                          </el-button>
                          <el-button
                            :disabled="!generatedDraft"
                            :loading="publishLoading"
                            @click="handlePublishDraft"
                          >
                            发布到当前班级
                          </el-button>
                        </div>
                      </el-form>
                      <p v-if="draftHint" class="status-text">{{ draftHint }}</p>
                    </SectionCard>

                    <SectionCard eyebrow="草案预览" title="最新生成草案">
                      <template v-if="generatedDraft">
                        <div class="preview-summary">
                          <div>
                            <strong>{{ generatedDraft.spec.title }}</strong>
                            <p class="panel-note">{{ generatedDraft.draft_summary }}</p>
                          </div>
                          <el-tag type="success" round>待教师审核</el-tag>
                        </div>
                        <div class="question-preview-list">
                          <div v-for="question in generatedDraft.spec.questions" :key="question.key" class="question-preview-item">
                            <div class="question-preview-item__head">
                              <strong>{{ question.stem }}</strong>
                              <el-tag type="warning" effect="plain" round>{{ question.points }} 分</el-tag>
                            </div>
                            <p class="panel-note">{{ question.type }} · {{ question.options.join(" / ") }}</p>
                          </div>
                        </div>
                      </template>
                      <p v-else class="panel-note">生成后会在这里显示结构化作业草案，教师确认后再发布。</p>
                    </SectionCard>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </template>
          </section>
        </div>
      </el-tab-pane>
    </el-tabs>

    <AssistantDrawer
      v-if="dashboard"
      v-model="generalAssistantOpen"
      :assistant="dashboard.general_assistant"
      @suggest="applySuggestion"
    />
    <AssistantDrawer
      v-if="courseDetail"
      v-model="courseAssistantOpen"
      :assistant="courseDetail.course_assistant"
      @suggest="applySuggestion"
    />

    <el-dialog v-model="createCourseDialog" title="生成课程" width="520px">
      <el-form label-position="top">
        <el-form-item label="课程标题">
          <el-input v-model="createCourseForm.title" />
        </el-form-item>
        <el-form-item label="学科">
          <el-input v-model="createCourseForm.subject" />
        </el-form-item>
        <el-form-item label="年级范围">
          <el-input v-model="createCourseForm.grade_scope" />
        </el-form-item>
        <el-form-item label="学期">
          <el-input v-model="createCourseForm.term" />
        </el-form-item>
        <el-form-item label="课次编号">
          <el-input v-model="createCourseForm.lesson_no" />
        </el-form-item>
        <el-form-item label="课程摘要">
          <el-input v-model="createCourseForm.summary" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item>
          <el-switch
            v-model="createCourseForm.create_course_agent"
            active-text="同时创建课程专属智能体"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-actions">
          <el-button @click="createCourseDialog = false">取消</el-button>
          <el-button type="primary" :loading="createCourseLoading" @click="handleCreateCourse">
            创建课程
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { api } from "../api/client";
import AssistantDrawer from "../components/AssistantDrawer.vue";
import ChartPanelCard from "../components/ChartPanelCard.vue";
import SectionCard from "../components/SectionCard.vue";
import StatCard from "../components/StatCard.vue";
import { useSessionStore } from "../stores/session";
import type { ActivityDraftResponse, TeacherCourseDetailResponse, TeacherDashboardResponse } from "../types/contracts";

const router = useRouter();
const session = useSessionStore();

const dashboard = ref<TeacherDashboardResponse | null>(null);
const courseDetail = ref<TeacherCourseDetailResponse | null>(null);
const selectedCourseId = ref<number | null>(null);
const activeTab = ref("overview");
const courseTab = ref("preview");
const generalAssistantOpen = ref(false);
const courseAssistantOpen = ref(false);
const courseLoading = ref(false);
const draftLoading = ref(false);
const publishLoading = ref(false);
const createCourseDialog = ref(false);
const createCourseLoading = ref(false);
const generatedDraft = ref<ActivityDraftResponse | null>(null);
const generatedDraftCourseId = ref<number | null>(null);
const publishDueAt = ref<string | null>(null);
const draftHint = ref("");

const draftTitle = ref("AI 交互作业：人工智能应用判断");
const learningGoal = ref("理解人工智能在课堂任务中的合理应用边界，并能判断何时需要人工复核。");
const resourceNames = ref("教材页、课堂 PPT、案例截图");
const selectedComponents = ref<string[]>(["single_choice", "sequence", "hotspot"]);

const createCourseForm = reactive({
  title: "八下第二单元 第1课 数据与可视化表达",
  subject: "信息科技",
  grade_scope: "八年级",
  term: "2025-2026 下",
  lesson_no: "L04",
  summary: "围绕数据采集、图表阅读与表达设计课程。",
  create_course_agent: true
});

const currentPreview = computed(() => {
  if (generatedDraft.value && generatedDraftCourseId.value === selectedCourseId.value) {
    return {
      activity_id: generatedDraft.value.activity_id,
      publication_id: null,
      title: generatedDraft.value.spec.title,
      instructions: generatedDraft.value.spec.instructions,
      question_count: generatedDraft.value.spec.questions.length,
      component_whitelist: generatedDraft.value.spec.component_whitelist,
      published_at: null,
      due_at: null,
      submission_count: 0,
      average_score: 0,
      auto_generated: true
    };
  }
  return courseDetail.value?.assignment_preview ?? null;
});

const currentSpec = computed(() => {
  if (generatedDraft.value && generatedDraftCourseId.value === selectedCourseId.value) {
    return generatedDraft.value.spec;
  }
  return courseDetail.value?.latest_spec ?? null;
});

onMounted(async () => {
  if (session.user?.role === "teacher") {
    await loadDashboard();
  }
});

watch(
  () => session.user?.id,
  async (value) => {
    if (value && session.user?.role === "teacher") {
      await loadDashboard();
    }
  }
);

watch(selectedCourseId, async (courseId) => {
  if (!courseId) {
    return;
  }
  await loadCourseDetail(courseId);
});

async function loginDemo() {
  await session.login("kylin", "222221", "xingzhi-school");
  await router.replace("/teacher");
  await loadDashboard();
}

async function loadDashboard() {
  if (!session.user) {
    return;
  }
  dashboard.value = await api.getTeacherDashboard(session.user.id);
  if (!selectedCourseId.value || !dashboard.value.course_directory.some((course) => course.id === selectedCourseId.value)) {
    selectedCourseId.value = dashboard.value.course_directory[0]?.id ?? null;
  }
}

async function loadCourseDetail(courseId: number) {
  courseLoading.value = true;
  try {
    courseDetail.value = await api.getTeacherCourseDetail(courseId);
    if (!generatedDraftCourseId.value || generatedDraftCourseId.value !== courseId) {
      draftHint.value = "";
    }
  } finally {
    courseLoading.value = false;
  }
}

function selectCourse(courseId: number) {
  selectedCourseId.value = courseId;
  activeTab.value = "courses";
}

async function handleCreateCourse() {
  if (!session.user) {
    return;
  }
  createCourseLoading.value = true;
  try {
    const response = await api.createCourse({
      teacher_user_id: session.user.id,
      ...createCourseForm
    });
    ElMessage.success(response.message);
    createCourseDialog.value = false;
    await loadDashboard();
    selectedCourseId.value = response.course.id;
    activeTab.value = "courses";
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "创建课程失败");
  } finally {
    createCourseLoading.value = false;
  }
}

async function handleGenerateDraft() {
  if (!session.user || !selectedCourseId.value) {
    return;
  }
  draftLoading.value = true;
  try {
    generatedDraft.value = await api.generateDraft({
      course_id: selectedCourseId.value,
      teacher_user_id: session.user.id,
      title: draftTitle.value,
      learning_goal: learningGoal.value,
      resource_names: resourceNames.value.split(/[，,]/).map((item) => item.trim()).filter(Boolean),
      component_whitelist: selectedComponents.value
    });
    generatedDraftCourseId.value = selectedCourseId.value;
    draftHint.value = "草案已生成，可继续预览并发布到当前班级。";
    courseTab.value = "studio";
    ElMessage.success("AI 作业草案生成完成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "生成作业失败");
  } finally {
    draftLoading.value = false;
  }
}

async function handlePublishDraft() {
  if (!generatedDraft.value || !dashboard.value || !session.user) {
    return;
  }
  publishLoading.value = true;
  try {
    await api.publishDraft({
      revision_id: generatedDraft.value.revision_id,
      classroom_id: dashboard.value.lab_snapshot.classroom_id,
      published_by_user_id: session.user.id,
      due_at: publishDueAt.value
    });
    ElMessage.success("作业已发布到当前班级");
    generatedDraft.value = null;
    generatedDraftCourseId.value = null;
    publishDueAt.value = null;
    draftHint.value = "已发布成功，课程目录中的作业分析会在学生提交后自动更新。";
    await loadDashboard();
    if (selectedCourseId.value) {
      await loadCourseDetail(selectedCourseId.value);
      courseTab.value = "preview";
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "发布失败");
  } finally {
    publishLoading.value = false;
  }
}

function applySuggestion(suggestion: string) {
  if (suggestion.includes("讲评")) {
    learningGoal.value = "基于本课程最近一次作业结果，生成讲评提纲并补足易错知识点训练。";
  }
  if (suggestion.includes("基础题")) {
    selectedComponents.value = ["single_choice", "sequence", "hotspot"];
  }
  draftHint.value = suggestion;
  ElMessage.success("已把智能体建议应用到当前操作上下文");
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "--";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
</script>
