<template>
  <div v-if="!session.user || session.user.role !== 'teacher'" class="empty-page">
    <el-card class="panel-card empty-card" shadow="hover">
      <el-empty description="请先登录教师账号进入工作台">
        <el-button type="primary" round @click="loginDemo">使用教师演示账号</el-button>
      </el-empty>
    </el-card>
  </div>

  <div v-else-if="dashboard" class="workspace-page workspace-page--immersive">
    <section class="workspace-hero workspace-hero--teacher">
      <div>
        <p class="panel-kicker">{{ dashboard.tenant_name }}</p>
        <h2>{{ courseDetail?.course.title ?? `${dashboard.teacher_name} · ${dashboard.classroom_label}` }}</h2>
        <p class="hero-copy">{{ featuredActivity?.instructions ?? "以当前课程为主舞台，集中处理活动任务、作品讲评和课堂分析。" }}</p>
      </div>
      <div class="workspace-hero__panel">
        <div class="theme-switcher theme-switcher--wide">
          <span class="theme-switcher__label">当前聚焦班级</span>
          <strong>{{ selectedClassroom?.name ?? dashboard.classroom_label }}</strong>
        </div>
        <div class="hero-actions">
          <el-button round @click="router.push('/teacher/settings')">教师设置</el-button>
          <el-button round @click="openShowcase" :disabled="!courseDetail">作品大屏</el-button>
          <el-button type="primary" round @click="createCourseDialog = true">生成课程</el-button>
        </div>
      </div>
    </section>

    <el-tabs v-model="activeTab" class="workspace-tabs">
      <el-tab-pane label="课堂总览" name="overview">
        <div class="workspace-grid workspace-grid--teacher-overview">
          <SectionCard eyebrow="开课控制" title="按班级开启上课">
            <template #icon>
              <el-icon><School /></el-icon>
            </template>
            <div class="classroom-control-grid">
              <div class="control-panel">
                <div class="theme-switcher theme-switcher--wide">
                  <span class="theme-switcher__label">查看班级</span>
                  <el-select
                    v-model="selectedClassroomId"
                    class="theme-switcher__select"
                    @change="handleClassroomChange"
                  >
                    <el-option
                      v-for="item in dashboard.classroom_options"
                      :key="item.id"
                      :label="`${item.name} · ${item.student_count}人`"
                      :value="item.id"
                    />
                  </el-select>
                </div>

                <div class="control-panel__meta">
                  <div class="mini-stat-card">
                    <span>学年</span>
                    <strong>{{ selectedClassroom?.school_year ?? '--' }}</strong>
                  </div>
                  <div class="mini-stat-card">
                    <span>年级/班号</span>
                    <strong>{{ selectedClassroom ? `${selectedClassroom.grade} ${selectedClassroom.class_no}班` : '--' }}</strong>
                  </div>
                  <div class="mini-stat-card">
                    <span>班级人数</span>
                    <strong>{{ selectedClassroom?.student_count ?? 0 }}</strong>
                  </div>
                </div>

                <div class="live-session-card">
                  <div class="live-session-card__head">
                    <div>
                      <p class="panel-kicker">当前课堂</p>
                      <strong>{{ dashboard.active_session?.course_title ?? '尚未开启课堂' }}</strong>
                    </div>
                    <el-tag round :type="dashboard.active_session ? 'success' : 'info'">
                      {{ dashboard.active_session?.status ?? 'idle' }}
                    </el-tag>
                  </div>
                  <div class="metric-inline metric-inline--strong">
                    <span>展示视图 {{ displayModeLabel(dashboard.active_session?.view_mode ?? 'lab-grid') }}</span>
                    <span>IP 锁定 {{ dashboard.active_session?.ip_lock_enabled ? '已启用' : '未启用' }}</span>
                    <span>开始时间 {{ formatDateTime(dashboard.active_session?.started_at ?? null) }}</span>
                  </div>
                </div>
              </div>

              <div class="control-panel">
                <p class="panel-kicker">开课设置</p>
                <el-form label-position="top" class="class-start-form">
                  <el-form-item label="上课班级">
                    <el-select v-model="startClassForm.classroom_id" class="fill-button">
                      <el-option
                        v-for="item in dashboard.classroom_options"
                        :key="item.id"
                        :label="item.name"
                        :value="item.id"
                      />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="关联课程">
                    <el-select v-model="startClassForm.course_id" class="fill-button">
                      <el-option
                        v-for="course in dashboard.course_directory"
                        :key="course.id"
                        :label="`${course.lesson_no} · ${course.title}`"
                        :value="course.id"
                      />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="课堂视图">
                    <el-radio-group v-model="startClassForm.view_mode" class="class-view-group">
                      <el-radio-button v-for="item in classViewModes" :key="item.value" :label="item.value">
                        {{ item.label }}
                      </el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item label="班级密码">
                    <el-input
                      v-model="startClassForm.class_password"
                      placeholder="选填，可用于机房统一入场"
                    />
                  </el-form-item>
                  <div class="class-start-form__footer">
                    <el-switch v-model="startClassForm.ip_lock_enabled" active-text="开启 IP 锁定" />
                    <el-button
                      type="primary"
                      :loading="startClassLoading"
                      :disabled="!startClassForm.classroom_id || !startClassForm.course_id"
                      @click="handleStartClass"
                    >
                      选择班级并开启上课
                    </el-button>
                  </div>
                </el-form>
              </div>
            </div>

            <div class="lab-board">
              <div class="lab-summary-column">
                <div class="lab-summary-grid">
                  <div class="status-tile">
                    <span>课堂视图</span>
                    <strong>{{ displayModeLabel(dashboard.lab_snapshot.view_mode) }}</strong>
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
                    <strong>{{ dashboard.lab_snapshot.ip_lock_enabled ? '已启用' : '未启用' }}</strong>
                  </div>
                  <div class="status-tile">
                    <span>班级密码</span>
                    <strong>{{ dashboard.lab_snapshot.class_password_enabled ? '已启用' : '未启用' }}</strong>
                  </div>
                </div>
                <div class="lab-brief">
                  <p class="panel-kicker">机房说明</p>
                  <p class="panel-note">
                    这里保留旧站的机房特性，包括 IP 锁定、班级密码、机房视图与课堂实时状态，同时把 AI 作业、作品上传、
                    互评和教师点评汇总进同一课堂闭环。
                  </p>
                </div>
              </div>

              <div class="seat-grid">
                <div v-for="seat in dashboard.lab_snapshot.seats" :key="seat.seat_no" class="seat-card">
                  <span class="seat-card__index">#{{ seat.seat_no.toString().padStart(2, '0') }}</span>
                  <strong>{{ seat.student_name }}</strong>
                  <el-tag size="small" round>{{ seat.status }}</el-tag>
                  <p class="panel-note">{{ seat.score != null ? `${seat.score} 分` : '等待课堂任务推进' }}</p>
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard eyebrow="课程目录" title="当前班级课程列表">
            <template #icon>
              <el-icon><Reading /></el-icon>
            </template>
            <div class="course-list">
              <button
                v-for="course in dashboard.course_directory"
                :key="course.id"
                type="button"
                class="course-list-card"
                :class="{ 'course-list-card--active': selectedCourseId === course.id }"
                @click="handleSelectCourse(course.id)"
              >
                <div class="course-list-card__head">
                  <strong>{{ course.title }}</strong>
                  <el-tag size="small" effect="plain">{{ course.lesson_no }}</el-tag>
                </div>
                <p class="panel-note">{{ course.subject }} · {{ course.term }}</p>
                <div class="metric-inline">
                  <span>均分 {{ course.average_score }}</span>
                  <span>提交率 {{ course.submission_rate }}%</span>
                  <span>{{ course.agent_enabled ? '已绑定课程智能体' : '未绑定课程智能体' }}</span>
                </div>
              </button>
            </div>
          </SectionCard>

          <SectionCard eyebrow="图表分析" title="教师首页图表">
            <template #icon>
              <el-icon><DataAnalysis /></el-icon>
            </template>
            <div class="chart-grid">
              <ChartPanelCard v-for="panel in dashboard.charts" :key="panel.key" :panel="panel" />
            </div>
          </SectionCard>

          <SectionCard eyebrow="待处理" title="今日关注事项">
            <template #icon>
              <el-icon><Bell /></el-icon>
            </template>
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

      <el-tab-pane label="当前课程" name="courses">
        <div class="directory-layout directory-layout--teacher directory-layout--immersive">
          <aside class="directory-sidebar">
            <div class="sidebar-head">
              <div>
                <p class="panel-kicker">课程列表</p>
                <h3>课程目录</h3>
              </div>
              <el-tag round effect="plain">{{ selectedClassroom?.name ?? dashboard.classroom_label }}</el-tag>
            </div>
            <div class="course-list">
              <button
                v-for="course in dashboard.course_directory"
                :key="course.id"
                type="button"
                class="course-list-card"
                :class="{ 'course-list-card--active': selectedCourseId === course.id }"
                @click="handleSelectCourse(course.id)"
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
                    {{ courseDetail.course.subject }} · {{ courseDetail.course.term }} · {{ courseDetail.classroom_label ?? dashboard.classroom_label }}
                    · 最近更新 {{ formatDateTime(courseDetail.course.last_updated) }}
                  </p>
                </div>
                <div class="hero-actions">
                  <el-button round @click="openShowcase">作品大屏</el-button>
                  <el-button round @click="courseTab = 'studio'">AI 发布</el-button>
                </div>
              </div>

              <SectionCard v-if="featuredActivity" eyebrow="活动焦点" title="当前课程任务焦点">
                <template #icon>
                  <el-icon><Flag /></el-icon>
                </template>
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
                    <span>完成 {{ featuredActivity.submission_count }}/{{ featuredActivity.submission_target || '--' }}</span>
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
                      <template #icon>
                        <el-icon><Reading /></el-icon>
                      </template>
                      <div class="activity-pill-row">
                        <button
                          v-for="activity in courseDetail.activities"
                          :key="`switch-${activity.id}`"
                          type="button"
                          class="activity-pill-button"
                          :class="{ 'activity-pill-button--active': featuredActivity?.id === activity.id }"
                          @click="handleSelectActivity(activity.id)"
                        >
                          <span>{{ activity.stage_label }}</span>
                          <strong>{{ activity.title }}</strong>
                        </button>
                      </div>
                      <div class="activity-card-list">
                        <article
                          v-for="activity in courseDetail.activities"
                          :key="activity.id"
                          class="activity-card"
                          :class="{ 'activity-card--collapsed': featuredActivity?.id !== activity.id }"
                        >
                          <div class="activity-card__header">
                            <div>
                              <p class="panel-kicker">{{ activity.stage_label }}</p>
                              <div class="activity-card__title">
                                <h4>{{ activity.title }}</h4>
                                <el-tag round>{{ activity.task_type_label }}</el-tag>
                              </div>
                            </div>
                            <div class="hero-actions">
                              <el-button
                                size="small"
                                round
                                :loading="documentLoadingKey === `briefing-${activity.id}`"
                                @click="handleGenerateDocument(activity, 'briefing')"
                              >
                                按活动导出讲评摘要
                              </el-button>
                              <el-button
                                size="small"
                                type="primary"
                                round
                                :loading="documentLoadingKey === `lesson-${activity.id}`"
                                @click="handleGenerateDocument(activity, 'lesson')"
                              >
                                优秀作品一键生成课堂讲评稿
                              </el-button>
                              <el-tag round effect="plain">{{ activity.status }}</el-tag>
                            </div>
                          </div>

                          <p class="panel-note">{{ activity.instructions }}</p>

                          <div class="tag-row" v-if="activity.deliverable || activity.due_at">
                            <el-tag v-if="activity.deliverable" round effect="plain">{{ `成果：${activity.deliverable}` }}</el-tag>
                            <el-tag v-if="activity.due_at" round effect="plain">{{ `截止：${formatDateTime(activity.due_at)}` }}</el-tag>
                            <el-tag round effect="plain">{{ `完成 ${activity.submission_count}/${activity.submission_target || '--'}` }}</el-tag>
                            <el-tag v-if="activity.review_enabled" round effect="plain">{{ `互评 ${activity.review_count}` }}</el-tag>
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
                              <strong>{{ activity.average_score ?? '--' }}</strong>
                            </div>
                            <div class="mini-stat-card">
                              <span>评价均分</span>
                              <strong>{{ activity.average_review_score ?? '--' }}</strong>
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
                                <el-tag type="warning" effect="plain" round>{{ `${question.points} 分` }}</el-tag>
                              </div>
                              <p class="panel-note">
                                {{ question.type }} · {{ question.options.length ? question.options.join(' / ') : '开放回答' }}
                              </p>
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
                              <el-tag round effect="plain">{{ `待教师点评 ${activity.pending_teacher_review_count}` }}</el-tag>
                            </div>

                            <div v-if="activity.recent_submissions.length" class="submission-grid">
                              <article v-for="submission in activity.recent_submissions" :key="submission.id" class="submission-card">
                                <div class="submission-card__head">
                                  <div>
                                    <strong>{{ submission.headline || '学生作品' }}</strong>
                                    <p class="panel-note">{{ submission.student_name }} · {{ formatDateTime(submission.submitted_at) }}</p>
                                  </div>
                                  <el-tag round effect="plain">
                                    {{
                                      submission.average_review_score != null
                                        ? `${submission.average_review_score} 分`
                                        : `${submission.review_count} 条评价`
                                    }}
                                  </el-tag>
                                </div>

                                <div v-if="submission.preview_asset_url" class="submission-preview-frame">
                                  <img
                                    class="submission-preview-image"
                                    :src="submission.preview_asset_url"
                                    :alt="submission.headline || '学生作品预览'"
                                  />
                                </div>

                                <p class="panel-note">{{ submission.summary || '学生已提交作品，等待进一步评价。' }}</p>

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
                                    {{ submission.teacher_reviewed ? '已完成教师点评' : '待教师点评' }}
                                  </el-tag>
                                  <el-tag round effect="plain">{{ `同伴互评 ${submission.peer_review_count}` }}</el-tag>
                                </div>

                                <div v-if="submission.teacher_review" class="review-note review-note--teacher">
                                  <strong>{{ `教师点评 · ${submission.teacher_review.score} 分` }}</strong>
                                  <p>{{ submission.teacher_review.comment }}</p>
                                </div>

                                <div v-if="submission.reviews.length" class="review-note-list">
                                  <div v-for="review in submission.reviews" :key="review.id" class="review-note">
                                    <strong>{{ `${review.reviewer_name} · ${review.score} 分` }}</strong>
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
                                      placeholder="补充教师点评，帮助学生复盘并沉淀展示案例"
                                    />
                                  </el-form-item>
                                  <el-form-item label="点评标签">
                                    <el-checkbox-group v-model="ensureTeacherReviewForm(submission).tags">
                                      <el-checkbox v-for="item in activity.rubric_items" :key="item" :label="item">
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
                                      {{ submission.teacher_reviewed ? '更新教师点评' : '提交教师点评' }}
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
                      <template #icon>
                        <el-icon><DataAnalysis /></el-icon>
                      </template>
                      <div class="analytics-strip">
                        <div class="analytics-tile">
                          <span>活动数量</span>
                          <strong>{{ courseDetail.activities.length }}</strong>
                        </div>
                        <div class="analytics-tile">
                          <span>最新交互作业均分</span>
                          <strong>{{ courseDetail.analytics?.average_score ?? '--' }}</strong>
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
                              <strong>{{ submission.headline || '学生作品' }}</strong>
                              <p class="panel-note">{{ submission.student_name }} · {{ formatDateTime(submission.submitted_at) }}</p>
                            </div>
                            <el-tag round :type="submission.teacher_reviewed ? 'success' : 'warning'">
                              {{ submission.teacher_reviewed ? '已点评' : '待点评' }}
                            </el-tag>
                          </div>
                          <div
                            v-if="submission.preview_asset_url"
                            class="submission-preview-frame submission-preview-frame--showcase"
                          >
                            <img
                              class="submission-preview-image"
                              :src="submission.preview_asset_url"
                              :alt="submission.headline || '作品展示'"
                            />
                          </div>
                          <p class="panel-note">{{ submission.summary || '课程作品展示' }}</p>
                        </article>
                      </div>
                    </SectionCard>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="AI 活动工坊" name="studio">
                  <div class="detail-stack">
                    <SectionCard eyebrow="AI 活动工坊" title="分步骤发布课程活动">
                      <template #icon>
                        <el-icon><MagicStick /></el-icon>
                      </template>
                      <div class="workflow-shell">
                        <el-steps :active="publishFlowStep" simple class="workflow-steps">
                          <el-step
                            v-for="item in publishFlowSteps"
                            :key="item.title"
                            :title="item.title"
                            :description="item.description"
                          />
                        </el-steps>

                        <div class="workflow-grid">
                          <div class="workflow-panel">
                            <template v-if="publishFlowStep === 0">
                              <div class="workflow-panel__head">
                                <div>
                                  <p class="panel-kicker">步骤一</p>
                                  <h4>明确主题、目标和资源</h4>
                                </div>
                                <el-tag round effect="plain">教师发布前置设计</el-tag>
                              </div>
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
                                    placeholder="教材页、PPT、案例截图，使用逗号分隔"
                                  />
                                </el-form-item>
                              </el-form>
                            </template>

                            <template v-else-if="publishFlowStep === 1">
                              <div class="workflow-panel__head">
                                <div>
                                  <p class="panel-kicker">步骤二</p>
                                  <h4>配置题型、班级和时限</h4>
                                </div>
                                <el-tag round effect="plain">发布策略</el-tag>
                              </div>
                              <el-form label-position="top">
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
                                <el-form-item label="发布到班级">
                                  <el-tag round effect="plain">{{ selectedClassroom?.name ?? dashboard.classroom_label }}</el-tag>
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
                              </el-form>
                            </template>

                            <template v-else>
                              <div class="workflow-panel__head">
                                <div>
                                  <p class="panel-kicker">步骤三</p>
                                  <h4>生成草稿并确认发布</h4>
                                </div>
                                <el-tag round type="success">{{ generatedDraft ? "草稿已生成" : "等待生成" }}</el-tag>
                              </div>
                              <div class="hero-actions">
                                <el-button type="primary" :loading="draftLoading" @click="handleGenerateDraft">
                                  生成 AI 活动
                                </el-button>
                                <el-button :disabled="!generatedDraft" :loading="publishLoading" @click="handlePublishDraft">
                                  发布到当前班级
                                </el-button>
                              </div>
                              <p class="panel-note">
                                平台会先生成结构化活动草稿，再由教师决定是否发布到当前班级，避免一次性堆满所有配置项。
                              </p>
                            </template>

                            <div class="workflow-actions">
                              <el-button :disabled="publishFlowStep === 0" @click="prevPublishFlowStep">上一步</el-button>
                              <el-button
                                type="primary"
                                plain
                                :disabled="publishFlowStep === publishFlowSteps.length - 1"
                                @click="nextPublishFlowStep"
                              >
                                下一步
                              </el-button>
                            </div>
                            <p v-if="draftHint" class="status-text">{{ draftHint }}</p>
                          </div>

                          <div class="workflow-panel workflow-panel--aside">
                            <div class="workflow-panel__head">
                              <div>
                                <p class="panel-kicker">发布预览</p>
                                <h4>{{ generatedDraft?.spec.title ?? "等待生成活动草稿" }}</h4>
                              </div>
                              <el-tag round effect="plain">{{ selectedClassroom?.name ?? dashboard.classroom_label }}</el-tag>
                            </div>
                            <template v-if="generatedDraft">
                              <p class="panel-note">{{ generatedDraft.draft_summary }}</p>
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
                                <div
                                  v-for="question in generatedDraft.spec.questions.slice(0, 3)"
                                  :key="question.key"
                                  class="question-preview-item"
                                >
                                  <div class="question-preview-item__head">
                                    <strong>{{ question.stem }}</strong>
                                    <el-tag type="warning" effect="plain" round>{{ `${question.points} 分` }}</el-tag>
                                  </div>
                                  <p class="panel-note">
                                    {{ question.type }} · {{ question.options.length ? question.options.join(" / ") : "开放回答" }}
                                  </p>
                                </div>
                              </div>
                            </template>
                            <div v-else class="step-note">
                              <p>建议先完成前两步，再在这里生成草稿。</p>
                              <p>生成后会展示标题、题型白名单和前几道示例题，方便快速确认。</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </SectionCard>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </template>

            <el-empty v-else description="请选择课程查看详情" />
          </section>
        </div>
      </el-tab-pane>
    </el-tabs>

    <AssistantDrawer
      v-if="activeAssistant"
      v-model="assistantPinned"
      :assistant="activeAssistant"
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

    <el-dialog v-model="documentPreview.visible" :title="documentPreview.title" width="760px">
      <div class="document-preview">
        <div class="document-preview__meta">
          <el-tag round effect="plain">{{ documentPreview.activityTitle || '活动讲评文档' }}</el-tag>
          <el-tag round>{{ documentPreview.filename }}</el-tag>
        </div>
        <pre class="document-preview__content">{{ documentPreview.content }}</pre>
      </div>
      <template #footer>
        <div class="dialog-actions">
          <el-button @click="documentPreview.visible = false">关闭</el-button>
          <el-button type="primary" @click="downloadGeneratedDocument">下载 Markdown</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  Bell,
  DataAnalysis,
  Flag,
  MagicStick,
  Monitor,
  Reading,
  School,
  Stopwatch,
} from "@element-plus/icons-vue";

import { api } from "../api/client";
import AssistantDrawer from "../components/AssistantDrawer.vue";
import ChartPanelCard from "../components/ChartPanelCard.vue";
import SectionCard from "../components/SectionCard.vue";
import { useSessionStore } from "../stores/session";
import type {
  ActivityDraftResponse,
  ActivityTaskDescriptor,
  GeneratedDocumentResponse,
  SubmissionDescriptor,
  TeacherCourseDetailResponse,
  TeacherDashboardResponse,
} from "../types/contracts";

const classViewModes = [
  { value: "lab-grid", label: "机房视图" },
  { value: "activity-focus", label: "活动聚焦" },
  { value: "showcase", label: "作品展示" },
];

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
let isSyncingWorkbenchRoute = false;

const dashboard = ref<TeacherDashboardResponse | null>(null);
const courseDetail = ref<TeacherCourseDetailResponse | null>(null);
const selectedCourseId = ref<number | null>(null);
const selectedClassroomId = ref<number | null>(null);
const selectedActivityId = ref<number | null>(null);
const activeTab = ref("courses");
const courseTab = ref("activities");
const assistantPinned = ref(false);
const courseLoading = ref(false);
const draftLoading = ref(false);
const publishLoading = ref(false);
const startClassLoading = ref(false);
const submittingReviewId = ref<number | null>(null);
const documentLoadingKey = ref<string | null>(null);
const createCourseDialog = ref(false);
const createCourseLoading = ref(false);
const generatedDraft = ref<ActivityDraftResponse | null>(null);
const generatedDraftCourseId = ref<number | null>(null);
const publishDueAt = ref<string | null>(null);
const draftHint = ref("");
const publishFlowStep = ref(0);
const teacherReviewForms = reactive<Record<number, { score: number; comment: string; tags: string[] }>>({});
const documentPreview = reactive({
  visible: false,
  title: "",
  filename: "",
  mimeType: "text/markdown",
  content: "",
  activityTitle: "",
});

const startClassForm = reactive({
  classroom_id: 0,
  course_id: 0,
  view_mode: "lab-grid",
  ip_lock_enabled: true,
  class_password: "",
});

const draftTitle = ref("AI 交互作业：信息科技场景判断");
const learningGoal = ref("理解人工智能在信息科技课堂中的合理应用边界，并能根据活动目标设计交互作业。");
const resourceNames = ref("教材页, 课堂 PPT, 示例截图");
const selectedComponents = ref<string[]>(["single_choice", "sequence", "hotspot"]);

const createCourseForm = reactive({
  title: "八下第二单元 第4课 数据与可视化表达",
  subject: "信息科技",
  grade_scope: "八年级",
  term: "2025-2026 下",
  lesson_no: "L04",
  summary: "围绕数据采集、图表阅读与表达设计课程。",
  create_course_agent: true,
});

const selectedClassroom = computed(() => {
  return dashboard.value?.classroom_options.find((item) => item.id === selectedClassroomId.value) ?? null;
});

const featuredActivity = computed<ActivityTaskDescriptor | null>(() => {
  if (!courseDetail.value) {
    return null;
  }
  return (
    courseDetail.value.activities.find((item) => item.id === selectedActivityId.value) ??
    courseDetail.value.activities.find((item) => item.id === courseDetail.value?.featured_activity_id) ??
    courseDetail.value.activities[0] ??
    null
  );
});

const activeAssistant = computed(() => {
  if (activeTab.value === "courses" && courseDetail.value) {
    return courseDetail.value.course_assistant;
  }
  return dashboard.value?.general_assistant ?? null;
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

const publishFlowSteps = [
  { title: "教学目标", description: "设定主题与资源" },
  { title: "题型配置", description: "选择班级与题型" },
  { title: "生成发布", description: "生成草稿并投放" },
];

onMounted(async () => {
  if (session.user?.role === "teacher") {
    await initializeTeacherWorkbench();
  }
});

watch(
  () => session.user?.id,
  async (value) => {
    if (value && session.user?.role === "teacher") {
      await initializeTeacherWorkbench();
      return;
    }
    dashboard.value = null;
    courseDetail.value = null;
  },
);

async function loginDemo() {
  await session.login("kylin", "222221", "xingzhi-school");
  await router.replace({ name: "teacher" });
  await initializeTeacherWorkbench();
}

async function initializeTeacherWorkbench() {
  activeTab.value = parseWorkbenchTab(route.query.tab) ?? "courses";
  await loadDashboard(parsePositiveInt(route.query.classroomId), parsePositiveInt(route.query.courseId));
}

async function loadDashboard(
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

  syncStartClassForm(nextDashboard);

  const preferredCourseId =
    nextDashboard.course_directory.find((course) => course.id === targetCourseId)?.id ??
    nextDashboard.active_session?.course_id ??
    nextDashboard.course_directory[0]?.id ??
    null;

  selectedCourseId.value = preferredCourseId;
  await syncWorkbenchRoute();
  if (preferredCourseId) {
    await loadCourseDetail(preferredCourseId);
  } else {
    courseDetail.value = null;
  }
}

function syncStartClassForm(nextDashboard: TeacherDashboardResponse) {
  startClassForm.classroom_id =
    selectedClassroomId.value ?? nextDashboard.current_classroom_id ?? nextDashboard.classroom_options[0]?.id ?? 0;
  startClassForm.course_id =
    nextDashboard.active_session?.course_id ??
    selectedCourseId.value ??
    nextDashboard.course_directory[0]?.id ??
    0;
  startClassForm.view_mode = nextDashboard.active_session?.view_mode ?? startClassForm.view_mode;
  startClassForm.ip_lock_enabled = nextDashboard.active_session?.ip_lock_enabled ?? true;
}

async function loadCourseDetail(courseId: number) {
  courseLoading.value = true;
  try {
    courseDetail.value = await api.getTeacherCourseDetail(courseId, selectedClassroomId.value);
    selectedActivityId.value =
      courseDetail.value.activities.find((item) => item.id === selectedActivityId.value)?.id ??
      courseDetail.value.activities.find((item) => item.id === courseDetail.value?.featured_activity_id)?.id ??
      courseDetail.value.activities[0]?.id ??
      null;
    if (generatedDraftCourseId.value !== courseId) {
      generatedDraft.value = null;
      draftHint.value = "";
      publishDueAt.value = null;
    }
  } finally {
    courseLoading.value = false;
  }
}

async function handleClassroomChange(classroomId: number) {
  selectedClassroomId.value = classroomId;
  startClassForm.classroom_id = classroomId;
  await loadDashboard(classroomId, selectedCourseId.value);
}

async function handleSelectCourse(courseId: number) {
  selectedCourseId.value = courseId;
  startClassForm.course_id = courseId;
  activeTab.value = "courses";
  assistantPinned.value = false;
  await syncWorkbenchRoute();
  await loadCourseDetail(courseId);
}

function handleSelectActivity(activityId: number) {
  selectedActivityId.value = activityId;
}

async function handleStartClass() {
  if (!session.user || !startClassForm.classroom_id || !startClassForm.course_id) {
    ElMessage.warning("请先选择班级与课程。");
    return;
  }
  startClassLoading.value = true;
  try {
    const response = await api.startClass({
      teacher_user_id: session.user.id,
      classroom_id: startClassForm.classroom_id,
      course_id: startClassForm.course_id,
      view_mode: startClassForm.view_mode,
      ip_lock_enabled: startClassForm.ip_lock_enabled,
      class_password: startClassForm.class_password.trim() || null,
    });
    selectedClassroomId.value = startClassForm.classroom_id;
    selectedCourseId.value = startClassForm.course_id;
    activeTab.value = "courses";
    ElMessage.success(response.message);
    await loadDashboard(startClassForm.classroom_id, startClassForm.course_id);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "开启课堂失败");
  } finally {
    startClassLoading.value = false;
  }
}

function openShowcase() {
  if (!courseDetail.value) {
    return;
  }
  router.push({
    name: "teacher-showcase",
    params: { courseId: courseDetail.value.course.id },
    query: selectedClassroomId.value ? { classroomId: String(selectedClassroomId.value) } : undefined,
  });
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
    draftHint.value = "AI 已生成结构化活动草稿，你可以继续调整后再发布。";
    ElMessage.success("AI 活动草稿已生成");
  } catch (error) {
    draftHint.value = error instanceof Error ? error.message : "生成失败";
    ElMessage.error(draftHint.value);
  } finally {
    draftLoading.value = false;
  }
}

async function handlePublishDraft() {
  if (!session.user || !generatedDraft.value || !selectedClassroomId.value) {
    ElMessage.warning("请先选择班级后再发布。");
    return;
  }
  publishLoading.value = true;
  try {
    const response = await api.publishDraft({
      revision_id: generatedDraft.value.revision_id,
      classroom_id: selectedClassroomId.value,
      published_by_user_id: session.user.id,
      due_at: publishDueAt.value,
    });
    draftHint.value = `活动已发布到当前班级，发布编号 ${response.publication_id}。`;
    ElMessage.success("活动已发布");
    await loadDashboard(selectedClassroomId.value);
    activeTab.value = "courses";
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
    createCourseDialog.value = false;
    ElMessage.success(response.message);
    await loadDashboard(selectedClassroomId.value);
    selectedCourseId.value = response.course.id;
    startClassForm.course_id = response.course.id;
    activeTab.value = "courses";
    await syncWorkbenchRoute();
    await loadCourseDetail(response.course.id);
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
    ElMessage.warning("请先填写教师点评。");
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
    await loadDashboard(selectedClassroomId.value);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "教师点评提交失败");
  } finally {
    submittingReviewId.value = null;
  }
}

async function handleGenerateDocument(activity: ActivityTaskDescriptor, kind: "briefing" | "lesson") {
  if (!session.user) {
    return;
  }
  documentLoadingKey.value = `${kind}-${activity.id}`;
  try {
    const response =
      kind === "briefing"
        ? await api.exportActivityBriefingSummary(activity.id, {
            teacher_user_id: session.user.id,
            classroom_id: selectedClassroomId.value,
          })
        : await api.generateLessonScript(activity.id, {
            teacher_user_id: session.user.id,
            classroom_id: selectedClassroomId.value,
          });
    openGeneratedDocument(response, activity.title);
    ElMessage.success(kind === "briefing" ? "讲评摘要已生成" : "课堂讲评稿已生成");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "文档生成失败");
  } finally {
    documentLoadingKey.value = null;
  }
}

function openGeneratedDocument(document: GeneratedDocumentResponse, activityTitle: string) {
  documentPreview.visible = true;
  documentPreview.title = document.title;
  documentPreview.filename = document.suggested_filename;
  documentPreview.mimeType = document.mime_type;
  documentPreview.content = document.content;
  documentPreview.activityTitle = activityTitle;
}

function downloadGeneratedDocument() {
  if (!documentPreview.content) {
    return;
  }
  const blob = new Blob([documentPreview.content], {
    type: `${documentPreview.mimeType};charset=utf-8`,
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = documentPreview.filename || "activity-briefing.md";
  link.click();
  URL.revokeObjectURL(url);
}

function applySuggestion(suggestion: string) {
  draftHint.value = suggestion;
  ElMessage.info(`智能体建议：${suggestion}`);
}

function nextPublishFlowStep() {
  publishFlowStep.value = Math.min(publishFlowStep.value + 1, publishFlowSteps.length - 1);
}

function prevPublishFlowStep() {
  publishFlowStep.value = Math.max(publishFlowStep.value - 1, 0);
}

function parsePositiveInt(value: unknown) {
  const normalized = Array.isArray(value) ? value[0] : value;
  const parsed = Number(normalized ?? 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function parseWorkbenchTab(value: unknown) {
  const normalized = Array.isArray(value) ? value[0] : value;
  return normalized === "courses" || normalized === "overview" ? normalized : null;
}

async function syncWorkbenchRoute() {
  const query: Record<string, string> = {};
  if (selectedClassroomId.value) {
    query.classroomId = String(selectedClassroomId.value);
  }
  if (selectedCourseId.value) {
    query.courseId = String(selectedCourseId.value);
  }
  if (activeTab.value !== "courses") {
    query.tab = activeTab.value;
  }

  isSyncingWorkbenchRoute = true;
  try {
    await router.replace({ name: "teacher", query });
  } finally {
    isSyncingWorkbenchRoute = false;
  }
}

watch(activeTab, async () => {
  if (!dashboard.value) {
    return;
  }
  assistantPinned.value = false;
  await syncWorkbenchRoute();
});

watch(
  () => [route.query.classroomId, route.query.courseId, route.query.tab],
  async ([classroomValue, courseValue, tabValue]) => {
    if (isSyncingWorkbenchRoute || !dashboard.value) {
      return;
    }

    const nextTab = parseWorkbenchTab(tabValue) ?? "courses";
    if (nextTab !== activeTab.value) {
      activeTab.value = nextTab;
    }

    const nextClassroomId = parsePositiveInt(classroomValue);
    const nextCourseId = parsePositiveInt(courseValue);

    if (nextClassroomId && nextClassroomId !== selectedClassroomId.value) {
      await loadDashboard(nextClassroomId, nextCourseId);
      return;
    }

    if (nextCourseId && nextCourseId !== selectedCourseId.value) {
      selectedCourseId.value = nextCourseId;
      startClassForm.course_id = nextCourseId;
      await loadCourseDetail(nextCourseId);
    }
  },
);

function displayModeLabel(mode: string) {
  return classViewModes.find((item) => item.value === mode)?.label ?? mode;
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
