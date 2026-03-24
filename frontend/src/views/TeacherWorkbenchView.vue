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
          教师首页聚合机房状态、课程目录、生成课程和图表分析。进入课程目录后，再按活动任务查看交互作业、作品提交、互评回流和 AI 活动工坊。
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
                    平台保留机房视图、IP 锁定和班级密码等老站特性，同时把作答、作品上传、互评和教师复核汇总到同一个教学闭环。
                  </p>
                </div>
              </div>
              <div class="seat-grid">
                <div v-for="seat in dashboard.lab_snapshot.seats" :key="seat.seat_no" class="seat-card">
                  <span class="seat-card__index">#{{ seat.seat_no.toString().padStart(2, "0") }}</span>
                  <strong>{{ seat.student_name }}</strong>
                  <el-tag size="small" round>{{ seat.status }}</el-tag>
                  <p class="panel-note">{{ seat.score != null ? `${seat.score} 分` : "等待课堂任务" }}</p>
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
              <ChartPanelCard v-for="panel in dashboard.charts" :key="panel.key" :panel="panel" />
            </div>
          </SectionCard>

          <SectionCard eyebrow="待处理" title="今日关注事项">
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

              <SectionCard v-if="featuredActivity" eyebrow="活动焦点" title="当前课程任务焦点">
                <div class="activity-focus-card">
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
                    <span>评价 {{ featuredActivity.review_count }}</span>
                    <span v-if="featuredActivity.average_score != null">自动均分 {{ featuredActivity.average_score }}</span>
                    <span v-if="featuredActivity.average_review_score != null">互评均分 {{ featuredActivity.average_review_score }}</span>
                    <span>截止 {{ formatDateTime(featuredActivity.due_at) }}</span>
                  </div>
                </div>
              </SectionCard>

              <el-tabs v-model="courseTab">
                <el-tab-pane label="活动任务" name="activities">
                  <div class="detail-stack">
                    <SectionCard eyebrow="活动任务流" title="课程按活动任务展开">
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

                          <div class="tag-row" v-if="activity.deliverable || activity.due_at">
                            <el-tag v-if="activity.deliverable" round effect="plain">成果：{{ activity.deliverable }}</el-tag>
                            <el-tag v-if="activity.due_at" round effect="plain">截止：{{ formatDateTime(activity.due_at) }}</el-tag>
                            <el-tag round effect="plain">完成 {{ activity.submission_count }}/{{ activity.submission_target || "--" }}</el-tag>
                            <el-tag v-if="activity.review_enabled" round effect="plain">互评 {{ activity.review_count }}</el-tag>
                          </div>

                          <div class="activity-metric-grid">
                            <div class="mini-stat-card">
                              <span>活动状态</span>
                              <strong>{{ activity.status }}</strong>
                            </div>
                            <div class="mini-stat-card">
                              <span>交互题量</span>
                              <strong>{{ activity.question_count }}</strong>
                            </div>
                            <div class="mini-stat-card">
                              <span>自动均分</span>
                              <strong>{{ activity.average_score ?? "--" }}</strong>
                            </div>
                            <div class="mini-stat-card">
                              <span>评价均分</span>
                              <strong>{{ activity.average_review_score ?? "--" }}</strong>
                            </div>
                          </div>

                          <div v-if="activity.prompt_starters.length" class="activity-prompt-list">
                            <el-button
                              v-for="prompt in activity.prompt_starters"
                              :key="prompt"
                              text
                              class="assistant-suggestion"
                              @click="applySuggestion(prompt)"
                            >
                              {{ prompt }}
                            </el-button>
                          </div>

                          <div v-if="activity.spec?.questions?.length" class="question-preview-list">
                            <div v-for="question in activity.spec.questions" :key="question.key" class="question-preview-item">
                              <div class="question-preview-item__head">
                                <strong>{{ question.stem }}</strong>
                                <el-tag type="warning" effect="plain" round>{{ question.points }} 分</el-tag>
                              </div>
                              <p class="panel-note">{{ question.type }} · {{ question.options.join(" / ") || "开放回答" }}</p>
                            </div>
                          </div>

                          <div v-if="activity.accepted_file_types.length" class="artifact-block">
                            <div class="artifact-block__head">
                              <strong>作品提交与评价</strong>
                              <div class="tag-row">
                                <el-tag v-for="item in activity.accepted_file_types" :key="item" round effect="plain">{{ item }}</el-tag>
                              </div>
                            </div>

                            <div v-if="activity.rubric_items.length" class="tag-row">
                              <el-tag v-for="item in activity.rubric_items" :key="item" round>{{ item }}</el-tag>
                              <el-tag round effect="plain">待教师点评 {{ activity.pending_teacher_review_count }}</el-tag>
                            </div>

                            <div class="submission-grid" v-if="activity.recent_submissions.length">
                              <article v-for="submission in activity.recent_submissions" :key="submission.id" class="submission-card">
                                <div class="submission-card__head">
                                  <div>
                                    <strong>{{ submission.headline || "学生作品" }}</strong>
                                    <p class="panel-note">{{ submission.student_name }} · {{ formatDateTime(submission.submitted_at) }}</p>
                                  </div>
                                  <el-tag round effect="plain">
                                    {{ submission.average_review_score != null ? `${submission.average_review_score} 分` : `${submission.review_count} 条评价` }}
                                  </el-tag>
                                </div>
                                <div v-if="submission.preview_asset_url" class="submission-preview-frame">
                                  <img class="submission-preview-image" :src="submission.preview_asset_url" :alt="submission.headline || '学生作品预览'" />
                                </div>
                                <p class="panel-note">{{ submission.summary || "学生已提交作品，等待进一步评价。" }}</p>
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
                                <div class="tag-row">
                                  <el-tag round :type="submission.teacher_reviewed ? 'success' : 'warning'">
                                    {{ submission.teacher_reviewed ? "已完成教师点评" : "待教师点评" }}
                                  </el-tag>
                                  <el-tag round effect="plain">同伴互评 {{ submission.peer_review_count }}</el-tag>
                                </div>
                                <div v-if="submission.teacher_review" class="review-note review-note--teacher">
                                  <strong>教师点评 · {{ submission.teacher_review.score }} 分</strong>
                                  <p>{{ submission.teacher_review.comment }}</p>
                                </div>
                                <div v-if="submission.reviews.length" class="review-note-list">
                                  <div v-for="review in submission.reviews" :key="review.id" class="review-note">
                                    <strong>{{ review.reviewer_name }} · {{ review.score }} 分</strong>
                                    <p>{{ review.comment }}</p>
                                  </div>
                                </div>
                                <el-form label-position="top" class="review-form review-form--teacher">
                                  <el-form-item label="教师评分">
                                    <el-slider
                                      v-model="ensureTeacherReviewForm(submission).score"
                                      :min="60"
                                      :max="100"
                                      :step="1"
                                      show-input
                                    />
                                  </el-form-item>
                                  <el-form-item label="教师点评">
                                    <el-input
                                      v-model="ensureTeacherReviewForm(submission).comment"
                                      type="textarea"
                                      :rows="3"
                                      placeholder="补充教师点评，帮助学生复盘和展示优秀案例"
                                    />
                                  </el-form-item>
                                  <el-form-item label="点评标签">
                                    <el-checkbox-group v-model="ensureTeacherReviewForm(submission).tags">
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
                                      @click="handleSubmitTeacherReview(submission.id)"
                                    >
                                      {{ submission.teacher_reviewed ? "更新教师点评" : "提交教师点评" }}
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

                <el-tab-pane label="课程分析" name="analytics">
                  <div class="detail-stack">
                    <SectionCard eyebrow="分析概览" title="活动与作业分析">
                      <div class="analytics-strip">
                        <div class="analytics-tile">
                          <span>活动数量</span>
                          <strong>{{ courseDetail.activities.length }}</strong>
                        </div>
                        <div class="analytics-tile">
                          <span>最新交互作业均分</span>
                          <strong>{{ courseDetail.analytics?.average_score ?? "--" }}</strong>
                        </div>
                        <div class="analytics-tile">
                          <span>最近提交回流</span>
                          <strong>{{ courseDetail.recent_submissions.length }}</strong>
                        </div>
                      </div>
                      <div class="chart-grid">
                        <ChartPanelCard v-for="panel in courseDetail.charts" :key="panel.key" :panel="panel" />
                      </div>
                    </SectionCard>

                    <SectionCard eyebrow="最近回流" title="作业与作品最近提交">
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

                    <SectionCard v-if="showcaseSubmissions.length" eyebrow="作品展示墙" title="优秀作品与待点评作品">
                      <div class="submission-grid submission-grid--showcase">
                        <article v-for="submission in showcaseSubmissions" :key="submission.id" class="submission-card">
                          <div class="submission-card__head">
                            <div>
                              <strong>{{ submission.headline || "学生作品" }}</strong>
                              <p class="panel-note">{{ submission.student_name }} · {{ formatDateTime(submission.submitted_at) }}</p>
                            </div>
                            <el-tag round :type="submission.teacher_reviewed ? 'success' : 'warning'">
                              {{ submission.teacher_reviewed ? "已点评" : "待点评" }}
                            </el-tag>
                          </div>
                          <div v-if="submission.preview_asset_url" class="submission-preview-frame submission-preview-frame--showcase">
                            <img class="submission-preview-image" :src="submission.preview_asset_url" :alt="submission.headline || '作品展示'" />
                          </div>
                          <p class="panel-note">{{ submission.summary || "课程作品展示" }}</p>
                        </article>
                      </div>
                    </SectionCard>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="AI 活动工坊" name="studio">
                  <div class="detail-stack">
                    <SectionCard eyebrow="AI 活动工坊" title="生成交互作业任务">
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
                            placeholder="教材页、PPT、案例截图，使用中文逗号分隔"
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
                            生成 AI 活动
                          </el-button>
                          <el-button :disabled="!generatedDraft" :loading="publishLoading" @click="handlePublishDraft">
                            发布到当前班级
                          </el-button>
                        </div>
                      </el-form>
                      <p v-if="draftHint" class="status-text">{{ draftHint }}</p>
                    </SectionCard>

                    <SectionCard eyebrow="草案预览" title="最新生成结果">
                      <template v-if="generatedDraft">
                        <div class="preview-summary">
                          <div>
                            <strong>{{ generatedDraft.spec.title }}</strong>
                            <p class="panel-note">{{ generatedDraft.draft_summary }}</p>
                          </div>
                          <el-tag type="success" round>待教师审核</el-tag>
                        </div>
                        <div class="tag-row">
                          <el-tag
                            v-for="component in generatedDraft.spec.component_whitelist"
                            :key="component"
                            round
                            effect="plain"
                          >
                            {{ component }}
                          </el-tag>
                        </div>
                        <div class="question-preview-list">
                          <div v-for="question in generatedDraft.spec.questions" :key="question.key" class="question-preview-item">
                            <div class="question-preview-item__head">
                              <strong>{{ question.stem }}</strong>
                              <el-tag type="warning" effect="plain" round>{{ question.points }} 分</el-tag>
                            </div>
                            <p class="panel-note">{{ question.type }} · {{ question.options.join(" / ") || "开放回答" }}</p>
                          </div>
                        </div>
                      </template>
                      <p v-else class="panel-note">
                        生成后会在这里展示结构化活动草案，教师确认后再发布到课程活动流中。
                      </p>
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
          <el-switch v-model="createCourseForm.create_course_agent" active-text="同时创建课程专属智能体" />
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
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { api } from "../api/client";
import AssistantDrawer from "../components/AssistantDrawer.vue";
import ChartPanelCard from "../components/ChartPanelCard.vue";
import SectionCard from "../components/SectionCard.vue";
import StatCard from "../components/StatCard.vue";
import { useSessionStore } from "../stores/session";
import type {
  ActivityDraftResponse,
  ActivityTaskDescriptor,
  SubmissionDescriptor,
  TeacherCourseDetailResponse,
  TeacherDashboardResponse,
} from "../types/contracts";

const router = useRouter();
const session = useSessionStore();

const dashboard = ref<TeacherDashboardResponse | null>(null);
const courseDetail = ref<TeacherCourseDetailResponse | null>(null);
const selectedCourseId = ref<number | null>(null);
const activeTab = ref("overview");
const courseTab = ref("activities");
const generalAssistantOpen = ref(false);
const courseAssistantOpen = ref(false);
const courseLoading = ref(false);
const draftLoading = ref(false);
const publishLoading = ref(false);
const submittingReviewId = ref<number | null>(null);
const createCourseDialog = ref(false);
const createCourseLoading = ref(false);
const generatedDraft = ref<ActivityDraftResponse | null>(null);
const generatedDraftCourseId = ref<number | null>(null);
const publishDueAt = ref<string | null>(null);
const draftHint = ref("");
const teacherReviewForms = reactive<Record<number, { score: number; comment: string; tags: string[] }>>({});

const draftTitle = ref("AI 交互作业：信息科技场景判断");
const learningGoal = ref("理解人工智能在信息科技课堂中的合理应用边界，并能根据活动目标设计交互作业。");
const resourceNames = ref("教材页、课堂 PPT、示例截图");
const selectedComponents = ref<string[]>(["single_choice", "sequence", "hotspot"]);

const createCourseForm = reactive({
  title: "八下第二单元 第 4 课 数据与可视化表达",
  subject: "信息科技",
  grade_scope: "八年级",
  term: "2025-2026 下",
  lesson_no: "L04",
  summary: "围绕数据采集、图表阅读与表达设计课程。",
  create_course_agent: true,
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

const showcaseSubmissions = computed<SubmissionDescriptor[]>(() => {
  if (!courseDetail.value) {
    return [];
  }
  const merged = courseDetail.value.activities.flatMap((activity) => activity.recent_submissions);
  const deduped = new Map<number, SubmissionDescriptor>();
  for (const item of merged) {
    if (!deduped.has(item.id)) {
      deduped.set(item.id, item);
    }
  }
  return Array.from(deduped.values())
    .sort((left, right) => {
      const leftScore = left.teacher_review?.score ?? left.average_review_score ?? 0;
      const rightScore = right.teacher_review?.score ?? right.average_review_score ?? 0;
      if (left.teacher_reviewed !== right.teacher_reviewed) {
        return Number(right.teacher_reviewed) - Number(left.teacher_reviewed);
      }
      return rightScore - leftScore;
    })
    .slice(0, 6);
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
    courseTab.value = "activities";
    if (generatedDraftCourseId.value !== courseId) {
      generatedDraft.value = null;
      draftHint.value = "";
      publishDueAt.value = null;
    }
  } finally {
    courseLoading.value = false;
  }
}

function selectCourse(courseId: number) {
  selectedCourseId.value = courseId;
  activeTab.value = "courses";
}

function ensureTeacherReviewForm(submission: SubmissionDescriptor) {
  if (!teacherReviewForms[submission.id]) {
    teacherReviewForms[submission.id] = {
      score: Math.round(submission.teacher_review?.score ?? submission.average_review_score ?? 90),
      comment: submission.teacher_review?.comment ?? "",
      tags: submission.teacher_review?.tags ? [...submission.teacher_review.tags] : [],
    };
  }
  return teacherReviewForms[submission.id];
}

async function handleGenerateDraft() {
  if (!session.user || !selectedCourseId.value) {
    return;
  }
  draftLoading.value = true;
  draftHint.value = "";
  try {
    generatedDraft.value = await api.generateDraft({
      course_id: selectedCourseId.value,
      teacher_user_id: session.user.id,
      title: draftTitle.value || undefined,
      learning_goal: learningGoal.value,
      resource_names: resourceNames.value
        .split(/[，,]/)
        .map((item) => item.trim())
        .filter(Boolean),
      component_whitelist: selectedComponents.value,
    });
    generatedDraftCourseId.value = selectedCourseId.value;
    courseTab.value = "studio";
    draftHint.value = "AI 已生成活动草案，你可以继续调整后再发布。";
    ElMessage.success("AI 活动草案已生成");
  } catch (error) {
    draftHint.value = error instanceof Error ? error.message : "生成失败";
    ElMessage.error(draftHint.value);
  } finally {
    draftLoading.value = false;
  }
}

async function handlePublishDraft() {
  if (!session.user || !dashboard.value || !generatedDraft.value) {
    return;
  }
  publishLoading.value = true;
  try {
    const response = await api.publishDraft({
      revision_id: generatedDraft.value.revision_id,
      classroom_id: dashboard.value.lab_snapshot.classroom_id,
      published_by_user_id: session.user.id,
      due_at: publishDueAt.value,
    });
    draftHint.value = `活动已发布到当前班级，发布编号 ${response.publication_id}。`;
    ElMessage.success("活动已发布");
    await loadDashboard();
    if (selectedCourseId.value) {
      await loadCourseDetail(selectedCourseId.value);
    }
  } catch (error) {
    draftHint.value = error instanceof Error ? error.message : "发布失败";
    ElMessage.error(draftHint.value);
  } finally {
    publishLoading.value = false;
  }
}

async function handleCreateCourse() {
  if (!session.user) {
    return;
  }
  createCourseLoading.value = true;
  try {
    const response = await api.createCourse({
      teacher_user_id: session.user.id,
      title: createCourseForm.title,
      subject: createCourseForm.subject,
      grade_scope: createCourseForm.grade_scope,
      term: createCourseForm.term,
      lesson_no: createCourseForm.lesson_no,
      summary: createCourseForm.summary,
      create_course_agent: createCourseForm.create_course_agent,
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

async function handleSubmitTeacherReview(submissionId: number) {
  if (!session.user) {
    return;
  }
  const form = teacherReviewForms[submissionId];
  if (!form || !form.comment.trim()) {
    ElMessage.warning("请填写教师点评。");
    return;
  }
  submittingReviewId.value = submissionId;
  try {
    const response = await api.createTeacherSubmissionReview(submissionId, {
      reviewer_user_id: session.user.id,
      score: form.score,
      comment: form.comment.trim(),
      tags: form.tags,
    });
    ElMessage.success(response.message);
    await loadDashboard();
    if (selectedCourseId.value) {
      await loadCourseDetail(selectedCourseId.value);
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "教师点评提交失败");
  } finally {
    submittingReviewId.value = null;
  }
}

function applySuggestion(suggestion: string) {
  draftHint.value = suggestion;
  ElMessage.info(`智能体建议：${suggestion}`);
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
