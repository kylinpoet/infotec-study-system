<template>
  <div v-if="!session.user || session.user.role !== 'teacher'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录教师账号进入作品展示页">
        <el-button type="primary" round @click="loginDemo">使用教师演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div v-else-if="dashboard && courseDetail" class="showcase-page">
    <section class="showcase-hero">
      <div class="showcase-hero__copy">
        <p class="panel-kicker">{{ dashboard.tenant_name }}</p>
        <h2>{{ courseDetail.course.title }}</h2>
        <p class="hero-copy">
          这里用于教师课堂投屏、作品集中展示和优秀案例讲评。已点评作品优先展示，待点评作品单独排队，方便课堂里快速切换。
        </p>
        <div class="hero-actions">
          <el-button round @click="goBack">返回课程工作台</el-button>
          <el-button round @click="courseAssistantOpen = true">课程智能体</el-button>
        </div>
      </div>

      <div class="showcase-hero__panel">
        <div class="theme-switcher theme-switcher--wide">
          <span class="theme-switcher__label">选择课程</span>
          <el-select v-model="selectedCourseId" class="theme-switcher__select">
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
          <el-select v-model="selectedActivityId" class="theme-switcher__select">
            <el-option label="全部作品活动" :value="0" />
            <el-option
              v-for="activity in showcaseActivities"
              :key="activity.id"
              :label="`${activity.stage_label} · ${activity.title}`"
              :value="activity.id"
            />
          </el-select>
        </div>
      </div>
    </section>

    <div class="stats-grid">
      <StatCard title="展示作品" :value="String(showcaseSubmissions.length)" hint="当前筛选条件下可用于课堂展示的作品数量" />
      <StatCard title="待教师点评" :value="String(pendingTeacherReviews.length)" hint="建议优先点评这些作品，便于形成完整反馈" />
      <StatCard title="已教师点评" :value="String(reviewedSubmissions.length)" hint="这些作品已带教师结论，适合做课堂展示和讲评" />
      <StatCard title="平均评价分" :value="averageReviewScoreLabel" hint="综合同伴互评和教师点评的平均分" />
    </div>

    <div class="showcase-layout">
      <SectionCard eyebrow="展示墙" title="优秀作品展示">
        <div v-if="reviewedSubmissions.length" class="showcase-grid">
          <article v-for="submission in reviewedSubmissions" :key="submission.id" class="showcase-card">
            <div class="submission-preview-frame submission-preview-frame--showcase">
              <img
                v-if="submission.preview_asset_url"
                class="submission-preview-image"
                :src="submission.preview_asset_url"
                :alt="submission.headline || '作品展示'"
              />
              <div v-else class="showcase-card__placeholder">无图片预览</div>
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
              <p class="panel-note">{{ submission.summary || "课程作品展示。" }}</p>
              <div v-if="submission.teacher_review" class="review-note review-note--teacher">
                <strong>教师点评</strong>
                <p>{{ submission.teacher_review.comment }}</p>
              </div>
              <div class="tag-row">
                <el-tag v-for="tag in submission.teacher_review?.tags ?? []" :key="tag" round effect="plain">{{ tag }}</el-tag>
                <el-tag round effect="plain">同伴互评 {{ submission.peer_review_count }}</el-tag>
              </div>
            </div>
          </article>
        </div>
        <el-empty v-else description="当前没有已点评作品，可先在课程工作台完成教师点评。" />
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
              <p class="panel-note">{{ submission.summary || "建议进入课程工作台补充教师点评。" }}</p>
              <div class="tag-row">
                <el-tag round effect="plain">互评 {{ submission.peer_review_count }}</el-tag>
                <el-tag round effect="plain">附件 {{ submission.assets.length }}</el-tag>
              </div>
            </div>
          </div>
          <el-empty v-else description="当前筛选下没有待点评作品。" />
        </SectionCard>

        <SectionCard eyebrow="图表分析" title="作品与活动图表">
          <div class="chart-grid">
            <ChartPanelCard v-for="panel in courseDetail.charts" :key="panel.key" :panel="panel" />
          </div>
        </SectionCard>

        <SectionCard eyebrow="近期评价" title="互评与教师点评动态">
          <div v-if="recentReviews.length" class="review-note-list">
            <div v-for="review in recentReviews" :key="review.id" class="review-note">
              <strong>{{ review.reviewer_name }} · {{ review.score }} 分</strong>
              <p>{{ review.comment }}</p>
            </div>
          </div>
          <el-empty v-else description="暂无近期评价动态。" />
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
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

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

const dashboard = ref<TeacherDashboardResponse | null>(null);
const courseDetail = ref<TeacherCourseDetailResponse | null>(null);
const selectedCourseId = ref<number | null>(null);
const selectedActivityId = ref(0);
const courseAssistantOpen = ref(false);
const lastSuggestion = ref("");

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
  if (session.user?.role === "teacher") {
    await loadDashboardAndCourse();
  }
});

watch(
  () => session.user?.id,
  async (value) => {
    if (value && session.user?.role === "teacher") {
      await loadDashboardAndCourse();
    }
  }
);

watch(
  () => route.params.courseId,
  async (value) => {
    if (!dashboard.value) {
      return;
    }
    const parsed = typeof value === "string" ? Number(value) : Number(value?.[0] ?? 0);
    if (parsed && parsed !== selectedCourseId.value) {
      selectedCourseId.value = parsed;
      await loadCourseDetail(parsed);
    }
  }
);

watch(selectedCourseId, async (value) => {
  if (!value || !dashboard.value) {
    return;
  }
  const currentParam = Number(route.params.courseId ?? 0);
  if (currentParam !== value) {
    await router.replace({ name: "teacher-showcase", params: { courseId: value } });
  }
  if (courseDetail.value?.course.id !== value) {
    await loadCourseDetail(value);
  }
});

async function loginDemo() {
  await session.login("kylin", "222221", "xingzhi-school");
  await router.replace({ name: "teacher-showcase" });
  await loadDashboardAndCourse();
}

async function loadDashboardAndCourse() {
  if (!session.user) {
    return;
  }
  dashboard.value = await api.getTeacherDashboard(session.user.id);
  const routeCourseId = Number(route.params.courseId ?? 0);
  selectedCourseId.value =
    dashboard.value.course_directory.find((course) => course.id === routeCourseId)?.id ??
    dashboard.value.course_directory[0]?.id ??
    null;
  if (selectedCourseId.value) {
    await loadCourseDetail(selectedCourseId.value);
  }
}

async function loadCourseDetail(courseId: number) {
  courseDetail.value = await api.getTeacherCourseDetail(courseId);
  const currentShowcaseActivityIds = new Set(showcaseActivities.value.map((activity) => activity.id));
  if (!currentShowcaseActivityIds.has(selectedActivityId.value)) {
    selectedActivityId.value = 0;
  }
}

function goBack() {
  router.push({ name: "teacher" });
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
