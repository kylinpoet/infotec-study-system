<template>
  <div v-if="!session.user || session.user.role !== 'teacher'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录教师账号进入作品展示页">
        <el-button type="primary" round @click="loginDemo">使用教师演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div
    v-else-if="dashboard && courseDetail"
    ref="showcaseRoot"
    class="showcase-page"
    :class="{ 'showcase-page--classroom': classroomDisplayMode }"
  >
    <section class="showcase-hero">
      <div class="showcase-hero__copy">
        <p class="panel-kicker">{{ dashboard.tenant_name }}</p>
        <h2>{{ courseDetail.course.title }}</h2>
        <p class="hero-copy">
          作品大屏服务于课堂投屏、优秀作品展示和即时讲评。教师可按班级、课程、活动切换展示范围，并在大屏模式下进行自动轮播、
          全屏演示和班级展示切换。
        </p>
        <div class="hero-actions">
          <el-button round @click="goBack">返回课程工作台</el-button>
          <el-button round @click="courseAssistantOpen = true">课程智能体</el-button>
        </div>
      </div>

      <div class="showcase-hero__panel">
        <div class="theme-switcher theme-switcher--wide">
          <span class="theme-switcher__label">展示班级</span>
          <el-select v-model="selectedClassroomId" class="theme-switcher__select" @change="handleClassroomChange">
            <el-option
              v-for="item in dashboard.classroom_options"
              :key="item.id"
              :label="`${item.name} · ${item.student_count}人`"
              :value="item.id"
            />
          </el-select>
        </div>
        <div class="theme-switcher theme-switcher--wide">
          <span class="theme-switcher__label">展示课程</span>
          <el-select v-model="selectedCourseId" class="theme-switcher__select" @change="handleCourseChange">
            <el-option
              v-for="course in dashboard.course_directory"
              :key="course.id"
              :label="`${course.lesson_no} · ${course.title}`"
              :value="course.id"
            />
          </el-select>
        </div>
        <div class="theme-switcher theme-switcher--wide">
          <span class="theme-switcher__label">活动过滤</span>
          <el-select v-model="selectedActivityId" class="theme-switcher__select" @change="handleActivityChange">
            <el-option label="全部作品活动" :value="0" />
            <el-option
              v-for="activity in showcaseActivities"
              :key="activity.id"
              :label="`${activity.stage_label} · ${activity.title}`"
              :value="activity.id"
            />
          </el-select>
        </div>
        <div class="showcase-toolbar">
          <div class="showcase-toolbar__controls">
            <span class="theme-switcher__label">自动轮播</span>
            <el-switch v-model="autoRotate" />
          </div>
          <div class="showcase-toolbar__controls">
            <span class="theme-switcher__label">班级展示模式</span>
            <el-switch v-model="classroomDisplayMode" />
          </div>
          <div class="hero-actions">
            <el-button round @click="toggleFullscreen">{{ isFullscreen ? "退出全屏" : "全屏模式" }}</el-button>
          </div>
        </div>
      </div>
    </section>

    <div class="stats-grid">
      <StatCard title="展示作品" :value="String(allSubmissions.length)" hint="当前筛选条件下可用于课堂展示的作品数量" />
      <StatCard title="待教师点评" :value="String(pendingTeacherReviews.length)" hint="建议优先补齐这些作品的教师讲评" />
      <StatCard title="已教师点评" :value="String(reviewedSubmissions.length)" hint="这些作品已具备课堂展示与讲评信息" />
      <StatCard title="平均评价分" :value="averageReviewScoreLabel" hint="综合互评与教师点评后的展示均分" />
    </div>

    <SectionCard eyebrow="课堂大屏" title="焦点作品轮播">
      <div v-if="spotlightSubmission" class="showcase-stage">
        <div class="showcase-stage__media">
          <div class="submission-preview-frame submission-preview-frame--showcase submission-preview-frame--stage">
            <img
              v-if="spotlightSubmission.preview_asset_url"
              class="submission-preview-image"
              :src="spotlightSubmission.preview_asset_url"
              :alt="spotlightSubmission.headline || '作品展示'"
            />
            <div v-else class="showcase-card__placeholder">暂无作品预览图</div>
          </div>
        </div>

        <div class="showcase-stage__body">
          <div class="showcase-stage__head">
            <div>
              <p class="panel-kicker">{{ activeClassroom?.name ?? dashboard.classroom_label }}</p>
              <h3>{{ spotlightSubmission.headline || "学生作品" }}</h3>
              <p class="panel-note">{{ spotlightSubmission.student_name }} · {{ formatDateTime(spotlightSubmission.submitted_at) }}</p>
            </div>
            <div class="hero-actions">
              <el-tag round>{{ displayModeLabel(classroomDisplayMode) }}</el-tag>
              <el-tag round :type="spotlightSubmission.teacher_reviewed ? 'success' : 'warning'">
                {{ spotlightSubmission.teacher_reviewed ? "已教师点评" : "待教师点评" }}
              </el-tag>
            </div>
          </div>

          <p class="panel-note">{{ spotlightSubmission.summary || "当前作品已进入课堂展示流程，可结合教师点评进行讲评。" }}</p>

          <div class="metric-inline metric-inline--strong">
            <span>互评 {{ spotlightSubmission.peer_review_count }}</span>
            <span>总评价 {{ spotlightSubmission.review_count }}</span>
            <span>展示序号 {{ spotlightSubmissions.length ? spotlightIndex + 1 : 0 }}/{{ spotlightSubmissions.length }}</span>
          </div>

          <div v-if="spotlightSubmission.teacher_review" class="review-note review-note--teacher">
            <strong>{{ `教师点评 · ${spotlightSubmission.teacher_review.score} 分` }}</strong>
            <p>{{ spotlightSubmission.teacher_review.comment }}</p>
          </div>

          <div class="submission-asset-list">
            <a
              v-for="asset in spotlightSubmission.assets"
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

          <div class="showcase-stage__footer">
            <div class="hero-actions">
              <el-button round @click="prevSpotlight">上一张</el-button>
              <el-button type="primary" round @click="nextSpotlight">下一张</el-button>
            </div>

            <div class="showcase-thumbnail-row">
              <button
                v-for="submission in spotlightSubmissions.slice(0, 6)"
                :key="submission.id"
                type="button"
                class="showcase-thumbnail"
                :class="{ 'showcase-thumbnail--active': spotlightSubmission.id === submission.id }"
                @click="focusSubmission(submission.id)"
              >
                <strong>{{ submission.student_name }}</strong>
                <span>{{ submission.headline || "学生作品" }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <el-empty v-else description="当前筛选下还没有可展示作品" />
    </SectionCard>

    <div class="showcase-layout" :class="{ 'showcase-layout--classroom': classroomDisplayMode }">
      <SectionCard eyebrow="作品画廊" title="课堂可展示作品">
        <div v-if="reviewedSubmissions.length" class="showcase-grid">
          <article v-for="submission in reviewedSubmissions" :key="submission.id" class="showcase-card">
            <div class="submission-preview-frame submission-preview-frame--showcase">
              <img
                v-if="submission.preview_asset_url"
                class="submission-preview-image"
                :src="submission.preview_asset_url"
                :alt="submission.headline || '作品展示'"
              />
              <div v-else class="showcase-card__placeholder">暂无作品预览</div>
            </div>
            <div class="showcase-card__body">
              <div class="submission-card__head">
                <div>
                  <strong>{{ submission.headline || "学生作品" }}</strong>
                  <p class="panel-note">{{ submission.student_name }} · {{ formatDateTime(submission.submitted_at) }}</p>
                </div>
                <el-tag type="success" round>
                  {{ submission.teacher_review ? `${submission.teacher_review.score} 分` : "已点评" }}
                </el-tag>
              </div>
              <p class="panel-note">{{ submission.summary || "适合在课堂上进行展示讲评。" }}</p>
            </div>
          </article>
        </div>
        <el-empty v-else description="当前没有已点评作品，建议先在教师工作台补齐点评" />
      </SectionCard>

      <div class="showcase-side">
        <SectionCard eyebrow="待点评队列" title="优先处理作品">
          <div v-if="pendingTeacherReviews.length" class="info-list">
            <div v-for="submission in pendingTeacherReviews" :key="submission.id" class="showcase-queue-card">
              <div class="submission-card__head">
                <div>
                  <strong>{{ submission.headline || "学生作品" }}</strong>
                  <p class="panel-note">{{ submission.student_name }} · {{ formatDateTime(submission.submitted_at) }}</p>
                </div>
                <el-tag type="warning" round>待点评</el-tag>
              </div>
              <p class="panel-note">{{ submission.summary || "建议进入课程目录补充教师点评。" }}</p>
            </div>
          </div>
          <el-empty v-else description="当前筛选下没有待点评作品" />
        </SectionCard>

        <SectionCard eyebrow="图表分析" title="作品与活动图表">
          <div class="chart-grid">
            <ChartPanelCard v-for="panel in courseDetail.charts" :key="panel.key" :panel="panel" />
          </div>
        </SectionCard>

        <SectionCard eyebrow="近期评价" title="互评与教师点评动态">
          <div v-if="recentReviews.length" class="review-note-list">
            <div v-for="review in recentReviews" :key="review.id" class="review-note">
              <strong>{{ `${review.reviewer_name} · ${review.score} 分` }}</strong>
              <p>{{ review.comment }}</p>
            </div>
          </div>
          <el-empty v-else description="暂无近期评价动态" />
        </SectionCard>
      </div>
    </div>

    <AssistantDrawer
      v-model="courseAssistantOpen"
      :assistant="courseDetail.course_assistant"
      @suggest="lastSuggestion = $event"
    />
    <p v-if="lastSuggestion" class="status-text">{{ lastSuggestion }}</p>
  </div>

  <el-skeleton v-else animated :rows="8" />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { api } from "../api/client";
import AssistantDrawer from "../components/AssistantDrawer.vue";
import ChartPanelCard from "../components/ChartPanelCard.vue";
import SectionCard from "../components/SectionCard.vue";
import StatCard from "../components/StatCard.vue";
import { useSessionStore } from "../stores/session";
import type {
  ActivityTaskDescriptor,
  ReviewDescriptor,
  SubmissionDescriptor,
  TeacherCourseDetailResponse,
  TeacherDashboardResponse,
} from "../types/contracts";

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const showcaseRoot = ref<HTMLElement | null>(null);
const dashboard = ref<TeacherDashboardResponse | null>(null);
const courseDetail = ref<TeacherCourseDetailResponse | null>(null);
const selectedCourseId = ref<number | null>(null);
const selectedClassroomId = ref<number | null>(null);
const selectedActivityId = ref(0);
const autoRotate = ref(true);
const classroomDisplayMode = ref(false);
const courseAssistantOpen = ref(false);
const lastSuggestion = ref("");
const spotlightIndex = ref(0);
const isFullscreen = ref(false);

let rotationTimer: number | null = null;

const activeClassroom = computed(() => {
  return dashboard.value?.classroom_options.find((item) => item.id === selectedClassroomId.value) ?? null;
});

const showcaseActivities = computed<ActivityTaskDescriptor[]>(() => {
  return courseDetail.value?.activities.filter((activity) => activity.accepted_file_types.length) ?? [];
});

const activeActivities = computed<ActivityTaskDescriptor[]>(() => {
  if (selectedActivityId.value === 0) {
    return showcaseActivities.value;
  }
  return showcaseActivities.value.filter((activity) => activity.id === selectedActivityId.value);
});

const allSubmissions = computed<SubmissionDescriptor[]>(() => {
  const merged = activeActivities.value.flatMap((activity) => activity.recent_submissions);
  const deduped = new Map<number, SubmissionDescriptor>();
  for (const item of merged) {
    if (!deduped.has(item.id)) {
      deduped.set(item.id, item);
    }
  }
  return Array.from(deduped.values()).sort((left, right) => {
    const leftScore = left.teacher_review?.score ?? left.average_review_score ?? 0;
    const rightScore = right.teacher_review?.score ?? right.average_review_score ?? 0;
    return rightScore - leftScore;
  });
});

const reviewedSubmissions = computed(() => allSubmissions.value.filter((item) => item.teacher_reviewed));
const pendingTeacherReviews = computed(() => allSubmissions.value.filter((item) => !item.teacher_reviewed));
const recentReviews = computed<ReviewDescriptor[]>(() => {
  const merged = activeActivities.value.flatMap((activity) => activity.recent_reviews);
  const deduped = new Map<number, ReviewDescriptor>();
  for (const item of merged) {
    if (!deduped.has(item.id)) {
      deduped.set(item.id, item);
    }
  }
  return Array.from(deduped.values()).slice(0, 8);
});

const spotlightSubmissions = computed(() => {
  return reviewedSubmissions.value.length ? reviewedSubmissions.value : allSubmissions.value;
});

const spotlightSubmission = computed(() => {
  if (!spotlightSubmissions.value.length) {
    return null;
  }
  return spotlightSubmissions.value[spotlightIndex.value % spotlightSubmissions.value.length];
});

const averageReviewScoreLabel = computed(() => {
  const scores = allSubmissions.value
    .map((item) => item.teacher_review?.score ?? item.average_review_score)
    .filter((item): item is number => typeof item === "number");
  if (!scores.length) {
    return "--";
  }
  return (scores.reduce((sum, score) => sum + score, 0) / scores.length).toFixed(1);
});

onMounted(async () => {
  document.addEventListener("fullscreenchange", handleFullscreenChange);
  if (session.user?.role === "teacher") {
    await initializeShowcase();
  }
});

onBeforeUnmount(() => {
  stopAutoRotate();
  document.removeEventListener("fullscreenchange", handleFullscreenChange);
});

watch(
  () => session.user?.id,
  async (value) => {
    if (value && session.user?.role === "teacher") {
      await initializeShowcase();
      return;
    }
    stopAutoRotate();
    dashboard.value = null;
    courseDetail.value = null;
  },
);

watch(
  spotlightSubmissions,
  () => {
    if (!spotlightSubmissions.value.length) {
      spotlightIndex.value = 0;
      stopAutoRotate();
      return;
    }
    spotlightIndex.value = Math.min(spotlightIndex.value, spotlightSubmissions.value.length - 1);
    configureAutoRotate();
  },
  { deep: true },
);

watch(autoRotate, () => {
  configureAutoRotate();
});

async function loginDemo() {
  await session.login("kylin", "222221", "xingzhi-school");
  await router.replace({ name: "teacher-showcase" });
  await initializeShowcase();
}

async function initializeShowcase() {
  const routeClassroomId = Number(route.query.classroomId ?? 0) || null;
  const routeCourseId = Number(route.params.courseId ?? 0) || null;
  await loadDashboardAndCourse(routeClassroomId, routeCourseId);
}

async function loadDashboardAndCourse(
  targetClassroomId: number | null = selectedClassroomId.value,
  targetCourseId: number | null = selectedCourseId.value,
) {
  if (!session.user) {
    return;
  }
  const nextDashboard = await api.getTeacherDashboard(session.user.id, targetClassroomId);
  dashboard.value = nextDashboard;
  selectedClassroomId.value =
    nextDashboard.current_classroom_id ?? nextDashboard.classroom_options[0]?.id ?? null;

  const nextCourseId =
    nextDashboard.course_directory.find((course) => course.id === targetCourseId)?.id ??
    nextDashboard.active_session?.course_id ??
    nextDashboard.course_directory[0]?.id ??
    null;
  selectedCourseId.value = nextCourseId;

  if (nextCourseId) {
    await loadCourseDetail(nextCourseId);
  } else {
    courseDetail.value = null;
  }

  await router.replace({
    name: "teacher-showcase",
    params: nextCourseId ? { courseId: nextCourseId } : undefined,
    query: selectedClassroomId.value ? { classroomId: String(selectedClassroomId.value) } : undefined,
  });
}

async function loadCourseDetail(courseId: number) {
  courseDetail.value = await api.getTeacherCourseDetail(courseId, selectedClassroomId.value);
  const activeIds = new Set(showcaseActivities.value.map((activity) => activity.id));
  if (!activeIds.has(selectedActivityId.value)) {
    selectedActivityId.value = 0;
  }
  if (spotlightSubmissions.value.length) {
    spotlightIndex.value = Math.min(spotlightIndex.value, spotlightSubmissions.value.length - 1);
  } else {
    spotlightIndex.value = 0;
  }
}

async function handleCourseChange(courseId: number) {
  selectedCourseId.value = courseId;
  await loadCourseDetail(courseId);
  await router.replace({
    name: "teacher-showcase",
    params: { courseId },
    query: selectedClassroomId.value ? { classroomId: String(selectedClassroomId.value) } : undefined,
  });
}

async function handleClassroomChange(classroomId: number) {
  selectedClassroomId.value = classroomId;
  await loadDashboardAndCourse(classroomId, selectedCourseId.value);
}

async function handleActivityChange(activityId: number) {
  selectedActivityId.value = activityId;
  spotlightIndex.value = 0;
  configureAutoRotate();
}

function goBack() {
  router.push({ name: "teacher", query: selectedClassroomId.value ? { classroomId: String(selectedClassroomId.value) } : undefined });
}

function prevSpotlight() {
  if (!spotlightSubmissions.value.length) {
    return;
  }
  spotlightIndex.value =
    (spotlightIndex.value - 1 + spotlightSubmissions.value.length) % spotlightSubmissions.value.length;
}

function nextSpotlight() {
  if (!spotlightSubmissions.value.length) {
    return;
  }
  spotlightIndex.value = (spotlightIndex.value + 1) % spotlightSubmissions.value.length;
}

function focusSubmission(submissionId: number) {
  const index = spotlightSubmissions.value.findIndex((item) => item.id === submissionId);
  if (index >= 0) {
    spotlightIndex.value = index;
  }
}

function stopAutoRotate() {
  if (rotationTimer != null) {
    window.clearInterval(rotationTimer);
    rotationTimer = null;
  }
}

function configureAutoRotate() {
  stopAutoRotate();
  if (!autoRotate.value || spotlightSubmissions.value.length <= 1) {
    return;
  }
  rotationTimer = window.setInterval(() => {
    nextSpotlight();
  }, 6000);
}

function handleFullscreenChange() {
  isFullscreen.value = document.fullscreenElement === showcaseRoot.value;
}

async function toggleFullscreen() {
  if (!showcaseRoot.value) {
    return;
  }
  try {
    if (document.fullscreenElement === showcaseRoot.value) {
      await document.exitFullscreen();
      return;
    }
    await showcaseRoot.value.requestFullscreen();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "切换全屏失败");
  }
}
function displayModeLabel(_value: boolean) {
  return classroomDisplayMode.value ? "班级展示模式" : "讲评工作模式";
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
