export interface ThemePalette {
  primary: string;
  secondary: string;
  accent: string;
}

export interface QuickStat {
  title: string;
  value: string;
  hint: string;
}

export interface PendingItem {
  title: string;
  status: string;
  meta: string;
}

export interface ChartDatum {
  label: string;
  value: number;
}

export interface ChartPanel {
  key: string;
  title: string;
  subtitle: string;
  chart_type: "bar" | "line" | "pie";
  unit: string | null;
  points: ChartDatum[];
}

export interface PortalFeature {
  title: string;
  description: string;
}

export interface PortalAnnouncement {
  title: string;
  tag: string;
  summary: string;
  published_at: string;
}

export interface PortalSchool {
  id: number;
  code: string;
  name: string;
  district: string;
  slogan: string;
  grade_scope: string;
  theme: ThemePalette;
  features: PortalFeature[];
  metrics: QuickStat[];
}

export interface PortalResponse {
  hero_title: string;
  hero_subtitle: string;
  featured_school_code: string | null;
  schools: PortalSchool[];
  announcements: PortalAnnouncement[];
  platform_highlights: PortalFeature[];
}

export interface SessionUser {
  id: number;
  username: string;
  display_name: string;
  role: "teacher" | "student";
  tenant_id: number;
  tenant_code: string | null;
  tenant_name: string;
  classroom_label: string | null;
  current_course_id: number | null;
}

export interface LoginResponse {
  access_token: string;
  user: SessionUser;
}

export interface AgentCard {
  id: number;
  name: string;
  role: string;
  status: string;
  scope_label: string;
}

export interface AssistantDescriptor {
  title: string;
  subtitle: string;
  suggestions: string[];
  agents: AgentCard[];
  allow_external_sources: boolean;
  external_sources_note: string | null;
}

export interface QuestionSpec {
  key: string;
  type: string;
  stem: string;
  options: string[];
  correct_answer: unknown;
  points: number;
}

export interface ActivitySpec {
  title: string;
  instructions: string;
  teacher_tip: string;
  stage_label: string | null;
  activity_type: string | null;
  deliverable: string | null;
  accepted_file_types: string[];
  review_enabled: boolean;
  rubric_items: string[];
  prompt_starters: string[];
  component_whitelist: string[];
  questions: QuestionSpec[];
}

export interface AnalyticsQuestionMetric {
  key: string;
  stem: string;
  accuracy: number;
  submissions: number;
}

export interface AnalyticsResponse {
  publication_id: number;
  submission_count: number;
  average_score: number;
  average_duration_min: number | null;
  score_distribution: Record<string, number>;
  question_metrics: AnalyticsQuestionMetric[];
}

export interface ClassroomSeat {
  seat_no: number;
  student_name: string;
  status: string;
  score: number | null;
}

export interface LabSnapshot {
  classroom_id: number;
  classroom_label: string;
  view_mode: string;
  signed_in_count: number;
  student_count: number;
  submitted_count: number;
  pending_review_count: number;
  ip_lock_enabled: boolean;
  class_password_enabled: boolean;
  seats: ClassroomSeat[];
}

export interface ClassroomOption {
  id: number;
  name: string;
  school_year: string;
  grade: string;
  class_no: string;
  student_count: number;
}

export interface LiveSessionDescriptor {
  id: number | null;
  classroom_id: number;
  classroom_label: string;
  course_id: number | null;
  course_title: string | null;
  status: string;
  view_mode: string;
  ip_lock_enabled: boolean;
  started_at: string | null;
}

export interface TeacherCourseCard {
  id: number;
  title: string;
  subject: string;
  grade_scope: string;
  term: string;
  lesson_no: string;
  status: string;
  assignment_count: number;
  published_assignment_count: number;
  average_score: number;
  submission_rate: number;
  agent_enabled: boolean;
  last_updated: string | null;
}

export interface AssignmentPreview {
  activity_id: number;
  publication_id: number | null;
  title: string;
  instructions: string;
  question_count: number;
  component_whitelist: string[];
  published_at: string | null;
  due_at: string | null;
  submission_count: number;
  average_score: number;
  auto_generated: boolean;
}

export interface ReviewDescriptor {
  id: number;
  reviewer_name: string;
  reviewer_role: string;
  score: number;
  comment: string;
  reviewed_at: string | null;
  tags: string[];
}

export interface SubmissionAssetDescriptor {
  id: number;
  file_name: string;
  file_type: string;
  media_kind: string;
  file_url: string;
  preview_url: string | null;
  size_kb: number | null;
}

export interface SubmissionDescriptor {
  id: number;
  student_id: number;
  student_name: string;
  status: string;
  headline: string | null;
  summary: string | null;
  submitted_at: string | null;
  preview_asset_url: string | null;
  average_review_score: number | null;
  review_count: number;
  peer_review_count: number;
  teacher_reviewed: boolean;
  teacher_review: ReviewDescriptor | null;
  assets: SubmissionAssetDescriptor[];
  reviews: ReviewDescriptor[];
}

export interface ActivityTaskDescriptor {
  id: number;
  title: string;
  task_type: string;
  task_type_label: string;
  status: string;
  stage_label: string;
  instructions: string;
  teacher_tip: string | null;
  deliverable: string | null;
  publication_id: number | null;
  published_at: string | null;
  due_at: string | null;
  question_count: number;
  component_whitelist: string[];
  accepted_file_types: string[];
  review_enabled: boolean;
  rubric_items: string[];
  prompt_starters: string[];
  submission_count: number;
  submission_target: number;
  review_count: number;
  pending_teacher_review_count: number;
  average_score: number | null;
  average_review_score: number | null;
  spec: ActivitySpec | null;
  recent_submissions: SubmissionDescriptor[];
  recent_reviews: ReviewDescriptor[];
  my_submission: SubmissionDescriptor | null;
  my_review_queue: SubmissionDescriptor[];
}

export interface TeacherDashboardResponse {
  teacher_name: string;
  tenant_name: string;
  subject: string;
  classroom_label: string;
  current_classroom_id: number | null;
  classroom_options: ClassroomOption[];
  quick_stats: QuickStat[];
  lab_snapshot: LabSnapshot;
  active_session: LiveSessionDescriptor | null;
  course_directory: TeacherCourseCard[];
  pending_items: PendingItem[];
  charts: ChartPanel[];
  general_assistant: AssistantDescriptor;
}

export interface TeacherCourseDetailResponse {
  course: TeacherCourseCard;
  classroom_id: number | null;
  classroom_label: string | null;
  featured_activity_id: number | null;
  assignment_preview: AssignmentPreview | null;
  latest_spec: ActivitySpec | null;
  analytics: AnalyticsResponse | null;
  activities: ActivityTaskDescriptor[];
  charts: ChartPanel[];
  recent_submissions: PendingItem[];
  allowed_components: string[];
  course_assistant: AssistantDescriptor;
}

export interface CourseCreateResponse {
  course: TeacherCourseCard;
  agent: AgentCard | null;
  message: string;
}

export interface ActivityDraftResponse {
  activity_id: number;
  revision_id: number;
  draft_summary: string;
  spec: ActivitySpec;
}

export interface PublishResponse {
  publication_id: number;
  revision_id: number;
  classroom_id: number;
  status: string;
}

export interface StartClassResponse {
  session: LiveSessionDescriptor;
  message: string;
}

export interface GeneratedDocumentResponse {
  activity_id: number;
  title: string;
  suggested_filename: string;
  mime_type: string;
  content: string;
}

export interface FeedbackItem {
  title: string;
  content: string;
}

export interface StudentCourseCard {
  id: number;
  title: string;
  subject: string;
  term: string;
  lesson_no: string;
  status: string;
  latest_score: number | null;
  completion_rate: number;
  next_task_title: string | null;
  next_task_due_at: string | null;
}

export interface StudentDashboardResponse {
  student_name: string;
  tenant_name: string;
  classroom_label: string;
  total_score: number;
  quick_stats: QuickStat[];
  charts: ChartPanel[];
  course_directory: StudentCourseCard[];
  recent_feedback: FeedbackItem[];
  general_assistant: AssistantDescriptor;
}

export interface StudentCourseDetailResponse {
  course: StudentCourseCard;
  featured_activity_id: number | null;
  assignment_preview: AssignmentPreview | null;
  latest_spec: ActivitySpec | null;
  current_publication_id: number | null;
  activities: ActivityTaskDescriptor[];
  recent_feedback: FeedbackItem[];
  course_assistant: AssistantDescriptor;
}

export interface AttemptStartResponse {
  attempt_id: number;
  status: string;
  message: string;
}

export interface AttemptSubmitResponse {
  attempt_id: number;
  auto_score: number;
  correct_count: number;
  total_questions: number;
  feedback: string;
}

export interface WorkSubmissionResponse {
  submission: SubmissionDescriptor;
  message: string;
}

export interface SubmissionReviewResponse {
  review: ReviewDescriptor;
  message: string;
}
