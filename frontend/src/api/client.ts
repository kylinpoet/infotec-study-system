import type {
  ActivityDraftResponse,
  AnalyticsResponse,
  AttemptStartResponse,
  AttemptSubmitResponse,
  CourseCreateResponse,
  GeneratedDocumentResponse,
  LoginResponse,
  LLMConfigResponse,
  PortalResponse,
  PortalAdminDashboardResponse,
  PortalAnnouncement,
  PortalHeroSettings,
  SchoolAdminDashboardResponse,
  SchoolApplication,
  SchoolStaffMember,
  PublishResponse,
  StartClassResponse,
  StudentSettingsResponse,
  SubmissionReviewResponse,
  StudentCourseDetailResponse,
  StudentDashboardResponse,
  TeacherSettingsResponse,
  TeacherCourseDetailResponse,
  TeacherDashboardResponse,
  WorkSubmissionResponse
} from "../types/contracts";

const API_BASE = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(payload.detail ?? "请求失败");
  }

  return response.json() as Promise<T>;
}

export const api = {
  getPortal() {
    return request<PortalResponse>("/public/portal");
  },
  createSchoolApplication(payload: {
    school_name: string;
    school_code: string;
    district: string;
    grade_scope: string;
    slogan: string;
    contact_name: string;
    contact_phone: string;
    applicant_display_name: string;
    applicant_username: string;
    applicant_password: string;
    note?: string | null;
  }) {
    return request<{ message: string; application: SchoolApplication }>("/public/school-applications", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  login(username: string, password: string, schoolCode?: string | null) {
    return request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password, school_code: schoolCode ?? null })
    });
  },
  getStudentSettings(userId: number) {
    return request<StudentSettingsResponse>(`/settings/student/${userId}`);
  },
  updateStudentSettings(payload: { user_id: number; display_name: string; avatar?: string | null }) {
    return request<StudentSettingsResponse>("/settings/student", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  getTeacherSettings(userId: number) {
    return request<TeacherSettingsResponse>(`/settings/teacher/${userId}`);
  },
  updateTeacherSettings(payload: {
    user_id: number;
    display_name: string;
    subject: string;
    title?: string | null;
    avatar?: string | null;
  }) {
    return request<TeacherSettingsResponse>("/settings/teacher", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  getPortalAdminDashboard(userId: number) {
    return request<PortalAdminDashboardResponse>(`/admin/portal/dashboard/${userId}`);
  },
  updatePortalHero(payload: {
    admin_user_id: number;
    hero_title: string;
    hero_subtitle: string;
    featured_school_code?: string | null;
  }) {
    return request<PortalHeroSettings>("/admin/portal/hero", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  updatePortalSchool(
    schoolCode: string,
    payload: {
      admin_user_id: number;
      name: string;
      district: string;
      slogan: string;
      grade_scope: string;
      theme: { primary: string; secondary: string; accent: string };
      features: Array<{ title: string; description: string }>;
      metrics: Array<{ title: string; value: string; hint: string }>;
    }
  ) {
    return request<{ message: string }>(`/admin/portal/schools/${schoolCode}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  createPortalAnnouncement(payload: {
    admin_user_id: number;
    title: string;
    tag: string;
    summary: string;
    published_at: string;
    is_active: boolean;
  }) {
    return request<PortalAnnouncement>(`/admin/portal/announcements`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updatePortalAnnouncement(
    announcementId: number,
    payload: {
      admin_user_id: number;
      title: string;
      tag: string;
      summary: string;
      published_at: string;
      is_active: boolean;
    }
  ) {
    return request<PortalAnnouncement>(`/admin/portal/announcements/${announcementId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  reviewSchoolApplication(
    applicationId: number,
    payload: { admin_user_id: number; decision: "approve" | "reject"; review_note?: string | null }
  ) {
    return request<SchoolApplication>(`/admin/portal/school-applications/${applicationId}/review`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updateLlmConfig(payload: {
    admin_user_id: number;
    provider_name: string;
    base_url: string;
    api_key?: string | null;
    clear_api_key: boolean;
    model_name: string;
    temperature: number;
    max_tokens: number;
    is_enabled: boolean;
    notes?: string | null;
  }) {
    return request<LLMConfigResponse>("/admin/llm/config", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  getTeacherDashboard(userId: number, classroomId?: number | null) {
    const query = classroomId ? `?classroom_id=${classroomId}` : "";
    return request<TeacherDashboardResponse>(`/teacher/dashboard/${userId}${query}`);
  },
  getTeacherCourseDetail(courseId: number, classroomId?: number | null) {
    const query = classroomId ? `?classroom_id=${classroomId}` : "";
    return request<TeacherCourseDetailResponse>(`/teacher/courses/${courseId}${query}`);
  },
  createCourse(payload: {
    teacher_user_id: number;
    title: string;
    subject: string;
    grade_scope: string;
    term: string;
    lesson_no: string;
    summary?: string;
    create_course_agent: boolean;
  }) {
    return request<CourseCreateResponse>("/teacher/courses", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  generateDraft(payload: {
    course_id: number;
    teacher_user_id: number;
    title?: string;
    learning_goal: string;
    resource_names: string[];
    component_whitelist: string[];
  }) {
    return request<ActivityDraftResponse>("/teacher/activity-drafts/generate", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  publishDraft(payload: {
    revision_id: number;
    classroom_id: number;
    published_by_user_id: number;
    starts_at?: string | null;
    due_at?: string | null;
  }) {
    return request<PublishResponse>("/teacher/publications", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  startClass(payload: {
    teacher_user_id: number;
    classroom_id: number;
    course_id: number;
    view_mode: string;
    ip_lock_enabled: boolean;
    class_password?: string | null;
  }) {
    return request<StartClassResponse>("/teacher/live-sessions/start", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  getAnalytics(publicationId: number) {
    return request<AnalyticsResponse>(`/teacher/analytics/publications/${publicationId}`);
  },
  exportActivityBriefingSummary(
    activityId: number,
    payload: { teacher_user_id: number; classroom_id?: number | null }
  ) {
    return request<GeneratedDocumentResponse>(`/teacher/activities/${activityId}/briefing-summary`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  generateLessonScript(
    activityId: number,
    payload: { teacher_user_id: number; classroom_id?: number | null }
  ) {
    return request<GeneratedDocumentResponse>(`/teacher/activities/${activityId}/lesson-script`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  createTeacherSubmissionReview(
    submissionId: number,
    payload: { reviewer_user_id: number; score: number; comment: string; tags: string[] }
  ) {
    return request<SubmissionReviewResponse>(`/teacher/submissions/${submissionId}/reviews`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  getStudentDashboard(userId: number) {
    return request<StudentDashboardResponse>(`/student/dashboard/${userId}`);
  },
  getStudentCourseDetail(courseId: number, userId: number) {
    return request<StudentCourseDetailResponse>(`/student/courses/${courseId}?user_id=${userId}`);
  },
  startAttempt(publicationId: number, payload: { student_user_id: number; idempotency_key: string; device_info: string }) {
    return request<AttemptStartResponse>(`/student/publications/${publicationId}/attempts`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  submitAttempt(attemptId: number, payload: { answers: Array<{ question_key: string; value: unknown }>; total_time_sec: number }) {
    return request<AttemptSubmitResponse>(`/student/attempts/${attemptId}/submit`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  createWorkSubmission(
    activityId: number,
    payload: {
      student_user_id: number;
      headline?: string;
      summary?: string;
      assets: Array<{ file_name: string; file_type: string; data_url: string }>;
    }
  ) {
    return request<WorkSubmissionResponse>(`/student/activities/${activityId}/submissions`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  createSubmissionReview(
    submissionId: number,
    payload: { reviewer_user_id: number; score: number; comment: string; tags: string[] }
  ) {
    return request<SubmissionReviewResponse>(`/student/submissions/${submissionId}/reviews`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  getSchoolAdminDashboard(userId: number) {
    return request<SchoolAdminDashboardResponse>(`/school-admin/dashboard/${userId}`);
  },
  updateSchoolProfile(payload: {
    admin_user_id: number;
    name: string;
    district: string;
    slogan: string;
    grade_scope: string;
    theme: { primary: string; secondary: string; accent: string };
    features: Array<{ title: string; description: string }>;
    metrics: Array<{ title: string; value: string; hint: string }>;
  }) {
    return request<SchoolAdminDashboardResponse>("/school-admin/profile", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  createSchoolTeacher(payload: {
    admin_user_id: number;
    username: string;
    password: string;
    display_name: string;
    subject: string;
    title?: string | null;
    teacher_no?: string | null;
  }) {
    return request<{ message: string; staff_member: SchoolStaffMember }>("/school-admin/staff", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updateSchoolStaffRole(
    staffUserId: number,
    payload: { admin_user_id: number; role: "teacher" | "school_admin" }
  ) {
    return request<{ message: string; staff_member: SchoolStaffMember }>(`/school-admin/staff/${staffUserId}/role`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  }
};
