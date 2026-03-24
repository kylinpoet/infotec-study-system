import type {
  ActivityDraftResponse,
  AnalyticsResponse,
  AttemptStartResponse,
  AttemptSubmitResponse,
  CourseCreateResponse,
  LoginResponse,
  PortalResponse,
  PublishResponse,
  StudentCourseDetailResponse,
  StudentDashboardResponse,
  TeacherCourseDetailResponse,
  TeacherDashboardResponse
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
  login(username: string, password: string, schoolCode?: string | null) {
    return request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password, school_code: schoolCode ?? null })
    });
  },
  getTeacherDashboard(userId: number) {
    return request<TeacherDashboardResponse>(`/teacher/dashboard/${userId}`);
  },
  getTeacherCourseDetail(courseId: number) {
    return request<TeacherCourseDetailResponse>(`/teacher/courses/${courseId}`);
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
  getAnalytics(publicationId: number) {
    return request<AnalyticsResponse>(`/teacher/analytics/publications/${publicationId}`);
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
  }
};
