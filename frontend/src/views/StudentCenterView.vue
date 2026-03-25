<template>
  <div v-if="!session.user || session.user.role !== 'student'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录学生账号进入学生中心">
        <el-button type="primary" round @click="loginDemo">使用学生演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div v-else-if="dashboard" class="workspace-page workspace-page--immersive">
    <section class="workspace-hero workspace-hero--student workspace-hero--student-refined">
      <div>
        <p class="panel-kicker">{{ dashboard.tenant_name }}</p>
        <h2>{{ heroTitle }}</h2>
        <p class="hero-copy">{{ heroCopy }}</p>
        <div class="tag-row hero-meta-row">
          <span class="school-code-pill">{{ dashboard.classroom_label }}</span>
          <span class="school-code-pill">总分 {{ dashboard.total_score }}</span>
          <span class="school-code-pill">{{ completedCourses }}/{{ dashboard.course_directory.length }} 门已完成</span>
        </div>
      </div>
      <div class="student-hero-panel">
        <div class="student-hero-panel__score">
          <span>学习总分</span>
          <strong>{{ dashboard.total_score }}</strong>
          <small>{{ selectedCourseCard?.lesson_no ?? "当前学期" }} · {{ selectedCourseCard?.status ?? "持续更新" }}</small>
        </div>
        <div class="hero-actions">
          <el-button round @click="openSelectedCourse">进入当前课程</el-button>
          <el-button round @click="router.push('/student/settings')">学生设置</el-button>
        </div>
      </div>
    </section>

    <el-tabs v-model="activeTab" class="workspace-tabs">
      <el-tab-pane label="我的概况" name="overview">
        <div class="student-overview-shell">
          <section class="student-cockpit">
            <div class="student-cockpit__main">
              <div class="student-cockpit__head">
                <div>
                  <p class="panel-kicker">学习驾驶舱</p>
                  <h3>{{ dashboard.student_name }} · {{ dashboard.classroom_label }}</h3>
                  <p class="panel-note">先看总分、课程状态和成长曲线，再进入课程目录继续推进具体活动。</p>
                </div>
                <el-tag round effect="dark">{{ overviewStatusLabel }}</el-tag>
              </div>

              <div class="student-kpi-grid">
                <article
                  v-for="(item, index) in dashboard.quick_stats"
                  :key="item.title"
                  class="student-kpi-card"
                  :class="{ 'student-kpi-card--accent': index === 0 }"
                >
                  <span>{{ item.title }}</span>
                  <strong>{{ item.value }}</strong>
                  <p>{{ item.hint }}</p>
                </article>
              </div>
            </div>

            <aside class="student-cockpit__side">
              <div class="student-progress-note student-progress-note--student-refined">
                <p class="panel-kicker">当前推荐课程</p>
                <h4>{{ selectedCourseCard?.title ?? "等待课程同步" }}</h4>
                <p class="panel-note">{{ selectedCourseSummary }}</p>
                <div class="metric-inline metric-inline--strong">
                  <span>{{ selectedCourseCard?.lesson_no ?? "--" }}</span>
                  <span>最近成绩 {{ selectedCourseCard?.latest_score ?? "--" }}</span>
                  <span>完成率 {{ selectedCourseCard?.completion_rate ?? 0 }}%</span>
                </div>
                <div class="tag-row">
                  <el-tag v-if="selectedCourseCard?.next_task_title" round effect="plain">
                    下一项：{{ selectedCourseCard.next_task_title }}
                  </el-tag>
                  <el-tag v-if="featuredActivity?.task_type_label" round effect="plain">
                    当前活动：{{ featuredActivity.task_type_label }}
                  </el-tag>
                </div>
                <el-button type="primary" round class="fill-button" @click="openSelectedCourse">
                  进入当前课程任务
                </el-button>
              </div>
            </aside>
          </section>

          <SectionCard eyebrow="课程目录" title="继续推进课程">
            <template #icon>
              <el-icon><Trophy /></el-icon>
            </template>
            <div class="course-overview-grid course-overview-grid--student">
              <button
                v-for="course in dashboard.course_directory"
                :key="course.id"
                type="button"
                class="course-list-card student-course-card"
                :class="{ 'course-list-card--active': selectedCourseId === course.id }"
                @click="selectCourse(course.id)"
              >
                <div class="course-list-card__head">
                  <div>
                    <p class="panel-kicker">{{ course.lesson_no }}</p>
                    <strong>{{ course.title }}</strong>
                  </div>
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

          <div class="student-overview-grid">
            <SectionCard eyebrow="图表分析" title="学习成长图表" class="student-overview-grid__charts">
              <template #icon>
                <el-icon><DataAnalysis /></el-icon>
              </template>
              <div class="chart-grid chart-grid--student">
                <ChartPanelCard v-for="panel in dashboard.charts" :key="panel.key" :panel="panel" />
              </div>
            </SectionCard>

            <SectionCard eyebrow="最近反馈" title="课程反馈回流" class="student-overview-grid__feedback">
              <template #icon>
                <el-icon><Collection /></el-icon>
              </template>
              <div class="student-feedback-list">
                <article
                  v-for="(item, index) in dashboard.recent_feedback.slice(0, 4)"
                  :key="`${item.title}-${index}`"
                  class="student-feedback-item"
                >
                  <span class="student-feedback-item__index">{{ index + 1 }}</span>
                  <div>
                    <strong>{{ item.title }}</strong>
                    <p class="panel-note">{{ item.content }}</p>
                  </div>
                </article>
              </div>
            </SectionCard>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="当前课程" name="courses">
        <div class="directory-layout directory-layout--student directory-layout--immersive">
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
                <el-tag round effect="plain">{{ dashboard.total_score }} 分</el-tag>
              </div>

              <SectionCard v-if="featuredActivity" eyebrow="当前任务" title="本节课活动焦点">
                <template #icon>
                  <el-icon><Compass /></el-icon>
                </template>
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
                    <SectionCard eyebrow="活动任务流" title="按步骤推进课程">
                      <template #icon>
                        <el-icon><Compass /></el-icon>
                      </template>
                      <div class="course-activity-layout">
                        <aside class="activity-outline">
                          <button
                            v-for="activity in courseDetail.activities"
                            :key="activity.id"
                            type="button"
                            class="activity-outline-card"
                            :class="{ 'activity-outline-card--active': selectedActivityId === activity.id }"
                            @click="selectActivity(activity.id)"
                          >
                            <div class="activity-card__header">
                              <div>
                                <p class="panel-kicker">{{ activity.stage_label }}</p>
                                <strong>{{ activity.title }}</strong>
                              </div>
                              <el-tag round effect="plain">{{ activity.status }}</el-tag>
                            </div>
                            <p class="panel-note">{{ activity.task_type_label }} · {{ activity.instructions }}</p>
                          </button>
                        </aside>

                        <div v-if="selectedActivity" class="workflow-shell">
                          <div class="workflow-panel">
                            <div class="workflow-panel__head">
                              <div>
                                <p class="panel-kicker">{{ selectedActivity.stage_label }}</p>
                                <h4>{{ selectedActivity.title }}</h4>
                              </div>
                              <div class="hero-actions">
                                <el-tag round>{{ selectedActivity.task_type_label }}</el-tag>
                                <el-tag round effect="plain">{{ selectedActivity.status }}</el-tag>
                              </div>
                            </div>

                            <el-steps :active="studentWorkflowStep" simple class="workflow-steps">
                              <el-step
                                v-for="item in studentWorkflowSteps"
                                :key="item.key"
                                :title="item.title"
                                :description="item.description"
                              />
                            </el-steps>

                            <div v-if="currentStudentWorkflowStep?.key === 'guide'" class="activity-step-panel">
                              <div class="activity-step-panel__head">
                                <strong>先理解这一步要完成什么</strong>
                                <el-tag round effect="plain">{{ selectedActivity.deliverable || "按要求完成活动" }}</el-tag>
                              </div>
                              <p class="panel-note">{{ selectedActivity.instructions }}</p>
                              <div class="tag-row">
                                <el-tag v-if="selectedActivity.due_at" round effect="plain">截止：{{ formatDateTime(selectedActivity.due_at) }}</el-tag>
                                <el-tag v-if="selectedActivity.review_enabled" round effect="plain">互评开启</el-tag>
                                <el-tag round effect="plain">完成 {{ selectedActivity.submission_count }}/{{ selectedActivity.submission_target || "--" }}</el-tag>
                              </div>
                              <div v-if="selectedActivity.prompt_starters.length" class="activity-prompt-list">
                                <el-button
                                  v-for="prompt in selectedActivity.prompt_starters"
                                  :key="prompt"
                                  text
                                  class="assistant-suggestion"
                                  @click="submissionMessage = prompt"
                                >
                                  {{ prompt }}
                                </el-button>
                              </div>
                            </div>

                            <div v-else-if="currentStudentWorkflowStep?.key === 'assignment'" class="activity-step-panel">
                              <div class="assignment-stage">
                                <div class="assignment-stage__head">
                                  <strong>交互作业</strong>
                                  <el-tag round effect="plain">{{ selectedActivity.question_count }} 题</el-tag>
                                </div>
                                <el-form class="assignment-form" @submit.prevent="handleSubmitAssignment(selectedActivity)">
                                  <QuestionRenderer
                                    v-for="(question, index) in selectedActivity.spec?.questions ?? []"
                                    :key="question.key"
                                    v-model="ensureAnswers(selectedActivity.id)[question.key]"
                                    :index="index"
                                    :question="question"
                                  />
                                  <div class="hero-actions">
                                    <el-button
                                      type="primary"
                                      :loading="submittingAssignmentId === selectedActivity.id"
                                      @click="handleSubmitAssignment(selectedActivity)"
                                    >
                                      提交作答
                                    </el-button>
                                  </div>
                                </el-form>
                              </div>
                            </div>

                            <div v-else-if="currentStudentWorkflowStep?.key === 'submission'" class="activity-step-panel">
                              <div class="artifact-block">
                                <div class="artifact-block__head">
                                  <strong>作品提交</strong>
                                  <div class="tag-row">
                                    <el-tag
                                      v-for="fileType in selectedActivity.accepted_file_types"
                                      :key="fileType"
                                      round
                                      effect="plain"
                                    >
                                      {{ fileType }}
                                    </el-tag>
                                  </div>
                                </div>

                                <div class="upload-shell">
                                  <el-form label-position="top">
                                    <el-form-item label="作品标题">
                                      <el-input v-model="ensureUploadForm(selectedActivity.id).headline" placeholder="例如：智能海报设计" />
                                    </el-form-item>
                                    <el-form-item label="作品说明">
                                      <el-input
                                        v-model="ensureUploadForm(selectedActivity.id).summary"
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
                                        :on-change="createUploadHandler(selectedActivity.id)"
                                        :on-remove="createUploadHandler(selectedActivity.id)"
                                      >
                                        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                                        <div class="el-upload__text">将图片或文档拖到此处，或点击上传</div>
                                      </el-upload>
                                    </el-form-item>
                                    <div class="hero-actions">
                                      <el-button
                                        type="primary"
                                        :loading="submittingWorkId === selectedActivity.id"
                                        @click="handleSubmitWork(selectedActivity)"
                                      >
                                        提交作品
                                      </el-button>
                                    </div>
                                  </el-form>
                                </div>

                                <div v-if="selectedActivity.my_submission" class="submission-card submission-card--mine">
                                  <div class="submission-card__head">
                                    <div>
                                      <strong>{{ selectedActivity.my_submission.headline || "我的作品" }}</strong>
                                      <p class="panel-note">
                                        {{ formatDateTime(selectedActivity.my_submission.submitted_at) }} · {{ selectedActivity.my_submission.review_count }} 条评价
                                      </p>
                                    </div>
                                    <el-tag round effect="plain">
                                      {{ selectedActivity.my_submission.average_review_score != null ? `${selectedActivity.my_submission.average_review_score} 分` : "等待评价" }}
                                    </el-tag>
                                  </div>
                                  <p class="panel-note">{{ selectedActivity.my_submission.summary || "作品已提交。" }}</p>
                                  <div class="submission-asset-list">
                                    <a
                                      v-for="asset in selectedActivity.my_submission.assets"
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
                                </div>
                              </div>
                            </div>

                            <div v-else-if="currentStudentWorkflowStep?.key === 'review'" class="activity-step-panel">
                              <div v-if="selectedActivity.my_submission?.reviews.length" class="review-note-list">
                                <div
                                  v-for="review in selectedActivity.my_submission.reviews"
                                  :key="review.id"
                                  class="review-note"
                                >
                                  <strong>{{ review.reviewer_name }} · {{ review.score }} 分</strong>
                                  <p>{{ review.comment }}</p>
                                </div>
                              </div>

                              <div v-if="selectedActivity.review_enabled && selectedActivity.my_review_queue.length" class="review-queue">
                                <article
                                  v-for="submission in selectedActivity.my_review_queue"
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
                                          v-for="item in selectedActivity.rubric_items"
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

                              <div v-else class="step-note">
                                <p>当前这一步暂时没有待完成互评。</p>
                                <p>可以先返回前一步检查自己的作品说明，或等待同学作品进入互评队列。</p>
                              </div>
                            </div>

                            <div class="workflow-actions">
                              <el-button :disabled="studentWorkflowStep === 0" @click="prevStudentWorkflowStep">上一步</el-button>
                              <el-button
                                type="primary"
                                plain
                                :disabled="studentWorkflowStep >= studentWorkflowSteps.length - 1"
                                @click="nextStudentWorkflowStep"
                              >
                                下一步
                              </el-button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </SectionCard>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="课程反馈" name="feedback">
                  <div class="detail-stack">
                    <SectionCard eyebrow="成长反馈" title="最近回流">
                      <template #icon>
                        <el-icon><Collection /></el-icon>
                      </template>
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
      v-if="activeAssistant"
      v-model="assistantPinned"
      :assistant="activeAssistant"
      @suggest="submissionMessage = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  Collection,
  Compass,
  DataAnalysis,
  Trophy,
  UploadFilled,
} from "@element-plus/icons-vue";

import { api } from "../api/client";
import AssistantDrawer from "../components/AssistantDrawer.vue";
import ChartPanelCard from "../components/ChartPanelCard.vue";
import QuestionRenderer from "../components/QuestionRenderer.vue";
import SectionCard from "../components/SectionCard.vue";
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
const assistantPinned = ref(false);
const courseLoading = ref(false);
const submittingAssignmentId = ref<number | null>(null);
const submittingWorkId = ref<number | null>(null);
const submittingReviewId = ref<number | null>(null);
const selectedActivityId = ref<number | null>(null);
const studentWorkflowStep = ref(0);
const submissionMessage = ref("");
const submissionError = ref("");

const activityAnswers = reactive<Record<number, Record<string, unknown>>>({});
const uploadForms = reactive<Record<number, { headline: string; summary: string }>>({});
const uploadFiles = reactive<Record<number, File[]>>({});
const reviewForms = reactive<Record<number, { score: number; comment: string; tags: string[] }>>({});

const completedCourses = computed(
  () => dashboard.value?.course_directory.filter((course) => course.completion_rate >= 100).length ?? 0
);

const selectedCourseCard = computed(() => {
  if (!dashboard.value) {
    return null;
  }
  return (
    dashboard.value.course_directory.find((course) => course.id === selectedCourseId.value) ??
    dashboard.value.course_directory[0] ??
    null
  );
});

const pendingCourses = computed(
  () => dashboard.value?.course_directory.filter((course) => course.completion_rate < 100).length ?? 0
);

const heroTitle = computed(() => {
  if (!dashboard.value) {
    return "";
  }
  if (activeTab.value === "overview") {
    return `${dashboard.value.student_name} · 学习总览`;
  }
  return courseDetail.value?.course.title ?? `${dashboard.value.student_name} · ${dashboard.value.classroom_label}`;
});

const heroCopy = computed(() => {
  if (!dashboard.value) {
    return "";
  }
  if (activeTab.value === "overview") {
    return "先浏览整体表现、课程目录和成长图表，再进入当前课程按活动步骤推进作答、作品上传和互评复盘。";
  }
  return featuredActivity.value?.instructions ?? "进入当前课程后，沿着活动步骤完成作答、作品上传、互评和复盘。";
});

const overviewStatusLabel = computed(() => {
  if (!dashboard.value) {
    return "";
  }
  if (pendingCourses.value > 0) {
    return `待推进 ${pendingCourses.value} 门`;
  }
  return "进度稳定";
});

const selectedCourseSummary = computed(() => {
  const course = selectedCourseCard.value;
  if (!course) {
    return "课程数据同步后，会在这里推荐当前最值得优先推进的一门课程。";
  }
  return `${course.lesson_no} · ${course.subject} · ${course.next_task_title ?? "可直接进入课程目录继续学习"}`;
});

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

const selectedActivity = computed<ActivityTaskDescriptor | null>(() => {
  if (!courseDetail.value) {
    return null;
  }
  return (
    courseDetail.value.activities.find((item) => item.id === selectedActivityId.value) ??
    featuredActivity.value ??
    courseDetail.value.activities[0] ??
    null
  );
});

const studentWorkflowSteps = computed(() => {
  const activity = selectedActivity.value;
  if (!activity) {
    return [];
  }

  const steps = [{ key: "guide", title: "任务导览", description: "先看要求与目标" }];
  if (activity.spec?.questions?.length) {
    steps.push({ key: "assignment", title: "交互作答", description: "完成课堂练习" });
  }
  if (activity.accepted_file_types.length) {
    steps.push({ key: "submission", title: "作品提交", description: "上传图片或文档" });
  }
  if (activity.review_enabled || activity.my_submission || activity.my_review_queue.length) {
    steps.push({ key: "review", title: "互评复盘", description: "完成评价与回看" });
  }
  return steps;
});

const currentStudentWorkflowStep = computed(() => {
  return studentWorkflowSteps.value[studentWorkflowStep.value] ?? studentWorkflowSteps.value[0] ?? null;
});

const activeAssistant = computed(() => {
  if (activeTab.value === "courses" && courseDetail.value) {
    return courseDetail.value.course_assistant;
  }
  return dashboard.value?.general_assistant ?? null;
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
    const preservedActivityId = courseDetail.value.activities.find((item) => item.id === selectedActivityId.value)?.id;
    selectedActivityId.value =
      preservedActivityId ??
      courseDetail.value.activities.find((item) => item.id === courseDetail.value?.featured_activity_id)?.id ??
      courseDetail.value.activities[0]?.id ??
      null;
    studentWorkflowStep.value = Math.min(studentWorkflowStep.value, Math.max(studentWorkflowSteps.value.length - 1, 0));
  } finally {
    courseLoading.value = false;
  }
}

function selectCourse(courseId: number) {
  selectedCourseId.value = courseId;
  activeTab.value = "courses";
  assistantPinned.value = false;
}

function openSelectedCourse() {
  if (!selectedCourseCard.value) {
    return;
  }
  selectCourse(selectedCourseCard.value.id);
}

function selectActivity(activityId: number) {
  selectedActivityId.value = activityId;
  studentWorkflowStep.value = 0;
}

function nextStudentWorkflowStep() {
  studentWorkflowStep.value = Math.min(studentWorkflowStep.value + 1, studentWorkflowSteps.value.length - 1);
}

function prevStudentWorkflowStep() {
  studentWorkflowStep.value = Math.max(studentWorkflowStep.value - 1, 0);
}

watch(activeTab, () => {
  assistantPinned.value = false;
});

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
