<template>
  <div v-if="!session.user || session.user.role !== 'student'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录学生账号进入学生中心">
        <el-button type="primary" round @click="loginDemo">使用学生演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div v-else-if="dashboard" class="workspace-page">
    <section class="workspace-hero workspace-hero--student">
      <div>
        <p class="panel-kicker">{{ dashboard.tenant_name }}</p>
        <h2>{{ dashboard.student_name }} · {{ dashboard.classroom_label }}</h2>
        <p class="hero-copy">
          这里优先展示你的整体成绩、课程目录和成长分析；进入课程后再查看作业预览、答题页面和课程智能体。
        </p>
      </div>
      <div class="hero-actions">
        <el-button round @click="generalAssistantOpen = true">通用智能体</el-button>
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
      <el-tab-pane label="学习总览" name="overview">
        <div class="workspace-grid workspace-grid--student-overview">
          <SectionCard eyebrow="总分成绩" title="学生整体状况">
            <div class="student-summary-board">
              <div class="analytics-strip">
                <div class="analytics-tile analytics-tile--accent">
                  <span>总分成绩</span>
                  <strong>{{ dashboard.total_score }}</strong>
                </div>
                <div class="analytics-tile">
                  <span>课程数量</span>
                  <strong>{{ dashboard.course_directory.length }}</strong>
                </div>
                <div class="analytics-tile">
                  <span>已完成课程</span>
                  <strong>{{ completedCourses }}</strong>
                </div>
              </div>
              <div class="student-progress-note">
                <p class="panel-kicker">成长提示</p>
                <p class="panel-note">
                  先看总分和完成情况，再从课程目录进入具体作业。课程智能体只在课程内弹出，不会打断首页浏览。
                </p>
              </div>
            </div>

            <div class="course-overview-grid">
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
                <p class="panel-note">{{ course.next_task_title ?? "等待任务" }}</p>
                <div class="metric-inline">
                  <span>最近成绩 {{ course.latest_score ?? "--" }}</span>
                  <span>完成率 {{ course.completion_rate }}%</span>
                </div>
              </button>
            </div>
          </SectionCard>

          <SectionCard eyebrow="图表分析" title="学习成长图表">
            <div class="chart-grid">
              <ChartPanelCard
                v-for="panel in dashboard.charts"
                :key="panel.key"
                :panel="panel"
              />
            </div>
          </SectionCard>

          <SectionCard eyebrow="课程目录" title="最近反馈">
            <div class="info-list">
              <div
                v-for="item in dashboard.recent_feedback"
                :key="item.title"
                class="info-list-item"
              >
                <div>
                  <strong>{{ item.title }}</strong>
                  <p class="panel-note">{{ item.content }}</p>
                </div>
              </div>
            </div>
          </SectionCard>
        </div>
      </el-tab-pane>

      <el-tab-pane label="课程目录" name="courses">
        <div class="directory-layout directory-layout--student">
          <aside class="directory-sidebar">
            <div class="sidebar-head">
              <div>
                <p class="panel-kicker">我的课程</p>
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
                <p class="panel-note">{{ course.lesson_no }} · 最近成绩 {{ course.latest_score ?? "--" }}</p>
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
                    {{ courseDetail.assignment_preview?.instructions ?? "当前课程暂无作业说明。" }}
                  </p>
                </div>
                <div class="hero-actions">
                  <el-button round @click="courseAssistantOpen = true">课程智能体</el-button>
                </div>
              </div>

              <el-tabs v-model="courseTab">
                <el-tab-pane label="作业预览" name="preview">
                  <div class="detail-stack">
                    <SectionCard eyebrow="作业预览" title="课程作业">
                      <template v-if="courseDetail.assignment_preview">
                        <div class="preview-summary">
                          <div>
                            <strong>{{ courseDetail.assignment_preview.title }}</strong>
                            <p class="panel-note">{{ courseDetail.assignment_preview.instructions }}</p>
                          </div>
                          <el-space wrap>
                            <el-tag round>题目 {{ courseDetail.assignment_preview.question_count }}</el-tag>
                            <el-tag round effect="plain">
                              最近成绩 {{ courseDetail.course.latest_score ?? "--" }}
                            </el-tag>
                          </el-space>
                        </div>
                        <div class="tag-row">
                          <el-tag
                            v-for="component in courseDetail.assignment_preview.component_whitelist"
                            :key="component"
                            round
                            effect="plain"
                          >
                            {{ component }}
                          </el-tag>
                        </div>
                      </template>
                      <p v-else class="panel-note">当前课程还没有发布作业。</p>
                    </SectionCard>

                    <SectionCard eyebrow="成长反馈" title="课程反馈">
                      <div class="info-list">
                        <div
                          v-for="item in courseDetail.recent_feedback"
                          :key="`${item.title}-${item.content}`"
                          class="info-list-item"
                        >
                          <div>
                            <strong>{{ item.title }}</strong>
                            <p class="panel-note">{{ item.content }}</p>
                          </div>
                        </div>
                      </div>
                    </SectionCard>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="开始作答" name="assignment">
                  <div class="detail-stack">
                    <SectionCard eyebrow="在线作答" title="答题页面">
                      <template v-if="courseDetail.latest_spec && courseDetail.current_publication_id">
                        <el-form class="assignment-form" @submit.prevent="handleSubmitAssignment">
                          <QuestionRenderer
                            v-for="(question, index) in courseDetail.latest_spec.questions"
                            :key="question.key"
                            v-model="answers[question.key]"
                            :index="index"
                            :question="question"
                          />
                          <div class="hero-actions">
                            <el-button type="primary" :loading="submitting" @click="handleSubmitAssignment">
                              提交作答
                            </el-button>
                          </div>
                        </el-form>
                      </template>
                      <p v-else class="panel-note">当前课程暂无可作答内容。</p>
                      <p v-if="submissionMessage" class="status-text">{{ submissionMessage }}</p>
                      <p v-if="submissionError" class="status-text status-text--error">{{ submissionError }}</p>
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
      @suggest="submissionMessage = $event"
    />
    <AssistantDrawer
      v-if="courseDetail"
      v-model="courseAssistantOpen"
      :assistant="courseDetail.course_assistant"
      @suggest="submissionMessage = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { api } from "../api/client";
import AssistantDrawer from "../components/AssistantDrawer.vue";
import ChartPanelCard from "../components/ChartPanelCard.vue";
import QuestionRenderer from "../components/QuestionRenderer.vue";
import SectionCard from "../components/SectionCard.vue";
import StatCard from "../components/StatCard.vue";
import { useSessionStore } from "../stores/session";
import type { QuestionSpec, StudentCourseDetailResponse, StudentDashboardResponse } from "../types/contracts";

const router = useRouter();
const session = useSessionStore();

const dashboard = ref<StudentDashboardResponse | null>(null);
const courseDetail = ref<StudentCourseDetailResponse | null>(null);
const selectedCourseId = ref<number | null>(null);
const activeTab = ref("overview");
const courseTab = ref("preview");
const generalAssistantOpen = ref(false);
const courseAssistantOpen = ref(false);
const courseLoading = ref(false);
const submitting = ref(false);
const submissionMessage = ref("");
const submissionError = ref("");
const answers = reactive<Record<string, unknown>>({});

const completedCourses = computed(
  () => dashboard.value?.course_directory.filter((course) => course.status === "已完成").length ?? 0
);

onMounted(async () => {
  if (session.user?.role === "student") {
    await loadDashboard();
  }
});

watch(
  () => session.user?.id,
  async (value) => {
    if (value && session.user?.role === "student") {
      await loadDashboard();
    }
  }
);

watch(selectedCourseId, async (courseId) => {
  if (!courseId || !session.user) {
    return;
  }
  await loadCourseDetail(courseId);
});

async function loginDemo() {
  await session.login("240101", "12345", "xingzhi-school");
  await router.replace("/student");
  await loadDashboard();
}

async function loadDashboard() {
  if (!session.user) {
    return;
  }
  dashboard.value = await api.getStudentDashboard(session.user.id);
  if (!selectedCourseId.value || !dashboard.value.course_directory.some((course) => course.id === selectedCourseId.value)) {
    selectedCourseId.value = dashboard.value.course_directory[0]?.id ?? null;
  }
}

async function loadCourseDetail(courseId: number) {
  if (!session.user) {
    return;
  }
  courseLoading.value = true;
  submissionError.value = "";
  try {
    courseDetail.value = await api.getStudentCourseDetail(courseId, session.user.id);
    Object.keys(answers).forEach((key) => delete answers[key]);
  } finally {
    courseLoading.value = false;
  }
}

function selectCourse(courseId: number) {
  selectedCourseId.value = courseId;
  activeTab.value = "courses";
}

function normalizeAnswer(question: QuestionSpec, rawValue: unknown) {
  if (question.type === "sequence" && typeof rawValue === "string") {
    return rawValue.split(">").map((item) => item.trim()).filter(Boolean);
  }
  return rawValue;
}

async function handleSubmitAssignment() {
  if (!session.user || !courseDetail.value?.current_publication_id || !courseDetail.value.latest_spec) {
    return;
  }
  submissionError.value = "";
  submissionMessage.value = "";
  submitting.value = true;
  try {
    const attempt = await api.startAttempt(courseDetail.value.current_publication_id, {
      student_user_id: session.user.id,
      idempotency_key: `student-${session.user.id}-publication-${courseDetail.value.current_publication_id}`,
      device_info: "vite-demo-browser"
    });
    const result = await api.submitAttempt(attempt.attempt_id, {
      answers: courseDetail.value.latest_spec.questions.map((question) => ({
        question_key: question.key,
        value: normalizeAnswer(question, answers[question.key] ?? "")
      })),
      total_time_sec: 480
    });
    submissionMessage.value = `提交成功，自动评分 ${result.auto_score} 分，答对 ${result.correct_count}/${result.total_questions} 题。`;
    ElMessage.success("作答已提交");
    await loadDashboard();
    if (selectedCourseId.value) {
      await loadCourseDetail(selectedCourseId.value);
    }
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : "提交失败";
    ElMessage.error(submissionError.value);
  } finally {
    submitting.value = false;
  }
}
</script>
