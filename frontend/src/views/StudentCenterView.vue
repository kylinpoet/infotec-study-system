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
          学生首页优先展示整体成绩、课程目录和成长图表。进入课程后，再沿着活动任务完成交互作业、作品上传、互评和复盘。
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
          <SectionCard eyebrow="整体表现" title="学生整体状况">
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
                <p class="panel-kicker">学习提示</p>
                <p class="panel-note">
                  先看总分、课程完成度和成长图表，再进入课程目录继续推进具体活动。课程智能体只会在课程内的侧边抽屉中出现，不占用主要学习空间。
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
                <p class="panel-note">{{ course.next_task_title ?? "等待下一项任务" }}</p>
                <div class="metric-inline">
                  <span>最近成绩 {{ course.latest_score ?? "--" }}</span>
                  <span>完成率 {{ course.completion_rate }}%</span>
                </div>
              </button>
            </div>
          </SectionCard>

          <SectionCard eyebrow="图表分析" title="学习成长图表">
            <div class="chart-grid">
              <ChartPanelCard v-for="panel in dashboard.charts" :key="panel.key" :panel="panel" />
            </div>
          </SectionCard>

          <SectionCard eyebrow="最近反馈" title="课程反馈回流">
            <div class="info-list">
              <div v-for="item in dashboard.recent_feedback" :key="item.title" class="info-list-item">
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
                  <p class="panel-note">{{ featuredActivity?.instructions ?? "当前课程暂无活动说明。" }}</p>
                </div>
                <div class="hero-actions">
                  <el-button round @click="courseAssistantOpen = true">课程智能体</el-button>
                </div>
              </div>

              <SectionCard v-if="featuredActivity" eyebrow="当前任务" title="本节课活动焦点">
                <div class="activity-focus-card activity-focus-card--student">
                  <div class="activity-focus-card__head">
                    <div>
                      <p class="panel-kicker">{{ featuredActivity.stage_label }}</p>
                      <h4>{{ featuredActivity.title }}</h4>
                    </div>
                    <div class="hero-actions">
                      <el-tag round>{{ featuredActivity.task_type_label }}</el-tag>
                      <el-tag round effect="plain">{{ featuredActivity.status }}</el-tag>
                    </div>
                  </div>
                  <p class="panel-note">{{ featuredActivity.instructions }}</p>
                  <div class="metric-inline metric-inline--strong">
                    <span>完成 {{ featuredActivity.submission_count }}/{{ featuredActivity.submission_target || "--" }}</span>
                    <span v-if="featuredActivity.average_score != null">自动均分 {{ featuredActivity.average_score }}</span>
                    <span v-if="featuredActivity.average_review_score != null">互评均分 {{ featuredActivity.average_review_score }}</span>
                    <span>截止 {{ formatDateTime(featuredActivity.due_at) }}</span>
                  </div>
                </div>
              </SectionCard>

              <el-tabs v-model="courseTab">
                <el-tab-pane label="活动任务" name="activities">
                  <div class="detail-stack">
                    <SectionCard eyebrow="活动任务流" title="按活动推进课程">
                      <div class="activity-card-list">
                        <article v-for="activity in courseDetail.activities" :key="activity.id" class="activity-card">
                          <div class="activity-card__header">
                            <div>
                              <p class="panel-kicker">{{ activity.stage_label }}</p>
                              <div class="activity-card__title">
                                <h4>{{ activity.title }}</h4>
                                <el-tag round>{{ activity.task_type_label }}</el-tag>
                              </div>
                            </div>
                            <el-tag round effect="plain">{{ activity.status }}</el-tag>
                          </div>

                          <p class="panel-note">{{ activity.instructions }}</p>

                          <div class="tag-row">
                            <el-tag v-if="activity.deliverable" round effect="plain">成果：{{ activity.deliverable }}</el-tag>
                            <el-tag v-if="activity.due_at" round effect="plain">截止：{{ formatDateTime(activity.due_at) }}</el-tag>
                            <el-tag v-if="activity.review_enabled" round effect="plain">互评开启</el-tag>
                          </div>

                          <div v-if="activity.prompt_starters.length" class="activity-prompt-list">
                            <el-button
                              v-for="prompt in activity.prompt_starters"
                              :key="prompt"
                              text
                              class="assistant-suggestion"
                              @click="submissionMessage = prompt"
                            >
                              {{ prompt }}
                            </el-button>
                          </div>

                          <div v-if="activity.spec?.questions?.length" class="assignment-stage">
                            <div class="assignment-stage__head">
                              <strong>交互作业</strong>
                              <el-tag round effect="plain">{{ activity.question_count }} 题</el-tag>
                            </div>
                            <el-form class="assignment-form" @submit.prevent="handleSubmitAssignment(activity)">
                              <QuestionRenderer
                                v-for="(question, index) in activity.spec.questions"
                                :key="question.key"
                                v-model="ensureAnswers(activity.id)[question.key]"
                                :index="index"
                                :question="question"
                              />
                              <div class="hero-actions">
                                <el-button
                                  type="primary"
                                  :loading="submittingAssignmentId === activity.id"
                                  @click="handleSubmitAssignment(activity)"
                                >
                                  提交作答
                                </el-button>
                              </div>
                            </el-form>
                          </div>

                          <div v-if="activity.accepted_file_types.length" class="artifact-block">
                            <div class="artifact-block__head">
                              <strong>作品提交</strong>
                              <div class="tag-row">
                                <el-tag v-for="fileType in activity.accepted_file_types" :key="fileType" round effect="plain">
                                  {{ fileType }}
                                </el-tag>
                              </div>
                            </div>

                            <div class="upload-shell">
                              <el-form label-position="top">
                                <el-form-item label="作品标题">
                                  <el-input v-model="ensureUploadForm(activity.id).headline" placeholder="例如：智能海报设计" />
                                </el-form-item>
                                <el-form-item label="作品说明">
                                  <el-input
                                    v-model="ensureUploadForm(activity.id).summary"
                                    type="textarea"
                                    :rows="3"
                                    placeholder="简要说明你的设计思路和实现方式"
                                  />
                                </el-form-item>
                                <el-form-item label="上传附件">
                                  <el-upload
                                    drag
                                    multiple
                                    :auto-upload="false"
                                    :show-file-list="true"
                                    :limit="6"
                                    :on-change="createUploadHandler(activity.id)"
                                    :on-remove="createUploadHandler(activity.id)"
                                  >
                                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                                    <div class="el-upload__text">将图片或文档拖到此处，或点击上传</div>
                                  </el-upload>
                                </el-form-item>
                                <div class="hero-actions">
                                  <el-button
                                    type="primary"
                                    :loading="submittingWorkId === activity.id"
                                    @click="handleSubmitWork(activity)"
                                  >
                                    提交作品
                                  </el-button>
                                </div>
                              </el-form>
                            </div>

                            <div v-if="activity.my_submission" class="submission-card submission-card--mine">
                              <div class="submission-card__head">
                                <div>
                                  <strong>{{ activity.my_submission.headline || "我的作品" }}</strong>
                                  <p class="panel-note">
                                    {{ formatDateTime(activity.my_submission.submitted_at) }} · {{ activity.my_submission.review_count }} 条评价
                                  </p>
                                </div>
                                <el-tag round effect="plain">
                                  {{ activity.my_submission.average_review_score != null ? `${activity.my_submission.average_review_score} 分` : "等待评价" }}
                                </el-tag>
                              </div>
                              <p class="panel-note">{{ activity.my_submission.summary || "作品已提交。" }}</p>
                              <div class="submission-asset-list">
                                <a
                                  v-for="asset in activity.my_submission.assets"
                                  :key="asset.id"
                                  class="submission-asset"
                                  :href="asset.file_url"
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  <span>{{ asset.file_name }}</span>
                                  <small>{{ asset.media_kind }}</small>
                                </a>
                              </div>
                              <div v-if="activity.my_submission.reviews.length" class="review-note-list">
                                <div v-for="review in activity.my_submission.reviews" :key="review.id" class="review-note">
                                  <strong>{{ review.reviewer_name }} · {{ review.score }} 分</strong>
                                  <p>{{ review.comment }}</p>
                                </div>
                              </div>
                            </div>

                            <div v-if="activity.review_enabled && activity.my_review_queue.length" class="review-queue">
                              <div class="artifact-block__head">
                                <strong>待完成互评</strong>
                              </div>
                              <article
                                v-for="submission in activity.my_review_queue"
                                :key="submission.id"
                                class="submission-card"
                              >
                                <div class="submission-card__head">
                                  <div>
                                    <strong>{{ submission.headline || "同学作品" }}</strong>
                                    <p class="panel-note">{{ submission.student_name }}</p>
                                  </div>
                                  <el-tag round effect="plain">{{ submission.review_count }} 条已有评价</el-tag>
                                </div>
                                <p class="panel-note">{{ submission.summary || "请围绕作品结构、表达和实现完成评价。" }}</p>
                                <div class="submission-asset-list">
                                  <a
                                    v-for="asset in submission.assets"
                                    :key="asset.id"
                                    class="submission-asset"
                                    :href="asset.file_url"
                                    target="_blank"
                                    rel="noreferrer"
                                  >
                                    <span>{{ asset.file_name }}</span>
                                    <small>{{ asset.media_kind }}</small>
                                  </a>
                                </div>
                                <el-form label-position="top" class="review-form">
                                  <el-form-item label="评分">
                                    <el-slider
                                      v-model="ensureReviewForm(submission.id).score"
                                      :min="60"
                                      :max="100"
                                      :step="1"
                                      show-input
                                    />
                                  </el-form-item>
                                  <el-form-item label="评价意见">
                                    <el-input
                                      v-model="ensureReviewForm(submission.id).comment"
                                      type="textarea"
                                      :rows="3"
                                      placeholder="请给出具体、友善、可执行的建议"
                                    />
                                  </el-form-item>
                                  <el-form-item label="评价标签">
                                    <el-checkbox-group v-model="ensureReviewForm(submission.id).tags">
                                      <el-checkbox
                                        v-for="item in activity.rubric_items"
                                        :key="item"
                                        :label="item"
                                      >
                                        {{ item }}
                                      </el-checkbox>
                                    </el-checkbox-group>
                                  </el-form-item>
                                  <div class="hero-actions">
                                    <el-button
                                      type="primary"
                                      :loading="submittingReviewId === submission.id"
                                      @click="handleSubmitReview(submission.id)"
                                    >
                                      提交评价
                                    </el-button>
                                  </div>
                                </el-form>
                              </article>
                            </div>
                          </div>
                        </article>
                      </div>
                    </SectionCard>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="课程反馈" name="feedback">
                  <div class="detail-stack">
                    <SectionCard eyebrow="成长反馈" title="最近回流">
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
              </el-tabs>

              <p v-if="submissionMessage" class="status-text">{{ submissionMessage }}</p>
              <p v-if="submissionError" class="status-text status-text--error">{{ submissionError }}</p>
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
import { UploadFilled } from "@element-plus/icons-vue";

import { api } from "../api/client";
import AssistantDrawer from "../components/AssistantDrawer.vue";
import ChartPanelCard from "../components/ChartPanelCard.vue";
import QuestionRenderer from "../components/QuestionRenderer.vue";
import SectionCard from "../components/SectionCard.vue";
import StatCard from "../components/StatCard.vue";
import { useSessionStore } from "../stores/session";
import type {
  ActivityTaskDescriptor,
  QuestionSpec,
  StudentCourseDetailResponse,
  StudentDashboardResponse,
} from "../types/contracts";

const router = useRouter();
const session = useSessionStore();

const dashboard = ref<StudentDashboardResponse | null>(null);
const courseDetail = ref<StudentCourseDetailResponse | null>(null);
const selectedCourseId = ref<number | null>(null);
const activeTab = ref("overview");
const courseTab = ref("activities");
const generalAssistantOpen = ref(false);
const courseAssistantOpen = ref(false);
const courseLoading = ref(false);
const submittingAssignmentId = ref<number | null>(null);
const submittingWorkId = ref<number | null>(null);
const submittingReviewId = ref<number | null>(null);
const submissionMessage = ref("");
const submissionError = ref("");

const activityAnswers = reactive<Record<number, Record<string, unknown>>>({});
const uploadForms = reactive<Record<number, { headline: string; summary: string }>>({});
const uploadFiles = reactive<Record<number, File[]>>({});
const reviewForms = reactive<Record<number, { score: number; comment: string; tags: string[] }>>({});

const completedCourses = computed(
  () => dashboard.value?.course_directory.filter((course) => course.completion_rate >= 100).length ?? 0
);

const featuredActivity = computed<ActivityTaskDescriptor | null>(() => {
  if (!courseDetail.value) {
    return null;
  }
  return (
    courseDetail.value.activities.find((item) => item.id === courseDetail.value?.featured_activity_id) ??
    courseDetail.value.activities[0] ??
    null
  );
});

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
    courseTab.value = "activities";
  } finally {
    courseLoading.value = false;
  }
}

function selectCourse(courseId: number) {
  selectedCourseId.value = courseId;
  activeTab.value = "courses";
}

function ensureAnswers(activityId: number) {
  if (!activityAnswers[activityId]) {
    activityAnswers[activityId] = {};
  }
  return activityAnswers[activityId];
}

function ensureUploadForm(activityId: number) {
  if (!uploadForms[activityId]) {
    uploadForms[activityId] = { headline: "", summary: "" };
  }
  return uploadForms[activityId];
}

function ensureReviewForm(submissionId: number) {
  if (!reviewForms[submissionId]) {
    reviewForms[submissionId] = { score: 90, comment: "", tags: [] };
  }
  return reviewForms[submissionId];
}

function handleUploadChange(activityId: number, fileList: any[]) {
  uploadFiles[activityId] = fileList
    .map((item) => item.raw)
    .filter((file): file is File => file instanceof File);
}

function createUploadHandler(activityId: number) {
  return (_file: unknown, fileList: any[]) => {
    handleUploadChange(activityId, fileList);
  };
}

function normalizeAnswer(question: QuestionSpec, rawValue: unknown) {
  if (question.type === "sequence" && typeof rawValue === "string") {
    return rawValue
      .split(">")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return rawValue;
}

async function handleSubmitAssignment(activity: ActivityTaskDescriptor) {
  if (!session.user || !activity.publication_id || !activity.spec) {
    return;
  }
  submissionError.value = "";
  submissionMessage.value = "";
  submittingAssignmentId.value = activity.id;
  try {
    const attempt = await api.startAttempt(activity.publication_id, {
      student_user_id: session.user.id,
      idempotency_key: `student-${session.user.id}-publication-${activity.publication_id}`,
      device_info: "vite-demo-browser",
    });
    const answers = ensureAnswers(activity.id);
    const result = await api.submitAttempt(attempt.attempt_id, {
      answers: activity.spec.questions.map((question) => ({
        question_key: question.key,
        value: normalizeAnswer(question, answers[question.key] ?? ""),
      })),
      total_time_sec: 480,
    });
    submissionMessage.value = `交互作业已提交，自动评分 ${result.auto_score} 分，答对 ${result.correct_count}/${result.total_questions} 题。`;
    ElMessage.success("交互作业已提交");
    await refreshCurrentCourse();
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : "提交失败";
    ElMessage.error(submissionError.value);
  } finally {
    submittingAssignmentId.value = null;
  }
}

async function handleSubmitWork(activity: ActivityTaskDescriptor) {
  if (!session.user) {
    return;
  }
  const files = uploadFiles[activity.id] ?? [];
  if (!files.length) {
    submissionError.value = "请先选择至少一个作品文件。";
    ElMessage.warning(submissionError.value);
    return;
  }

  submittingWorkId.value = activity.id;
  submissionError.value = "";
  submissionMessage.value = "";
  try {
    const form = ensureUploadForm(activity.id);
    const assets = await Promise.all(
      files.map(async (file) => ({
        file_name: file.name,
        file_type: file.type || "application/octet-stream",
        data_url: await fileToDataUrl(file),
      }))
    );
    const response = await api.createWorkSubmission(activity.id, {
      student_user_id: session.user.id,
      headline: form.headline || undefined,
      summary: form.summary || undefined,
      assets,
    });
    submissionMessage.value = response.message;
    uploadForms[activity.id] = { headline: "", summary: "" };
    uploadFiles[activity.id] = [];
    ElMessage.success("作品已提交");
    await refreshCurrentCourse();
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : "作品提交失败";
    ElMessage.error(submissionError.value);
  } finally {
    submittingWorkId.value = null;
  }
}

async function handleSubmitReview(submissionId: number) {
  if (!session.user) {
    return;
  }
  const form = ensureReviewForm(submissionId);
  if (!form.comment.trim()) {
    submissionError.value = "请填写评价意见。";
    ElMessage.warning(submissionError.value);
    return;
  }

  submittingReviewId.value = submissionId;
  submissionError.value = "";
  submissionMessage.value = "";
  try {
    const response = await api.createSubmissionReview(submissionId, {
      reviewer_user_id: session.user.id,
      score: form.score,
      comment: form.comment.trim(),
      tags: form.tags,
    });
    submissionMessage.value = response.message;
    reviewForms[submissionId] = { score: 90, comment: "", tags: [] };
    ElMessage.success("评价已提交");
    await refreshCurrentCourse();
  } catch (error) {
    submissionError.value = error instanceof Error ? error.message : "评价提交失败";
    ElMessage.error(submissionError.value);
  } finally {
    submittingReviewId.value = null;
  }
}

async function refreshCurrentCourse() {
  await loadDashboard();
  if (selectedCourseId.value) {
    await loadCourseDetail(selectedCourseId.value);
  }
}

function fileToDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("文件读取失败"));
    reader.readAsDataURL(file);
  });
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "待定";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
</script>
