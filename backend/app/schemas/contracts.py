from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, Field, StringConstraints, model_validator
from typing import Annotated


class ThemePalette(BaseModel):
    primary: str
    secondary: str
    accent: str


class QuickStat(BaseModel):
    title: str
    value: str
    hint: str


class PendingItem(BaseModel):
    title: str
    status: str
    meta: str


class ChartDatum(BaseModel):
    label: str
    value: float


class ChartPanel(BaseModel):
    key: str
    title: str
    subtitle: str
    chart_type: str
    unit: str | None = None
    points: list[ChartDatum] = Field(default_factory=list)


class PortalFeature(BaseModel):
    title: str
    description: str


class PortalAnnouncement(BaseModel):
    id: int | None = None
    title: str
    tag: str
    summary: str
    published_at: datetime
    is_active: bool = True


class PortalSchool(BaseModel):
    id: int
    code: str
    name: str
    district: str
    slogan: str
    grade_scope: str
    theme: ThemePalette
    features: list[PortalFeature] = Field(default_factory=list)
    metrics: list[QuickStat] = Field(default_factory=list)


class PortalResponse(BaseModel):
    hero_title: str
    hero_subtitle: str
    featured_school_code: str | None = None
    schools: list[PortalSchool] = Field(default_factory=list)
    announcements: list[PortalAnnouncement] = Field(default_factory=list)
    platform_highlights: list[PortalFeature] = Field(default_factory=list)


class LoginRequest(BaseModel):
    username: str
    password: str
    school_code: str | None = None


class SessionUser(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    tenant_id: int
    tenant_code: str | None = None
    tenant_name: str
    classroom_label: str | None = None
    current_course_id: int | None = None
    avatar: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    user: SessionUser


class ZodiacAvatarOption(BaseModel):
    key: str
    label: str
    animal: str
    description: str


class StudentSettingsResponse(BaseModel):
    user: SessionUser
    student_no: str
    grade: str
    classroom_label: str
    seat_no: int | None = None
    zodiac_options: list[ZodiacAvatarOption] = Field(default_factory=list)


class StudentSettingsUpdateRequest(BaseModel):
    user_id: int
    display_name: str
    avatar: str | None = None


class TeacherSettingsResponse(BaseModel):
    user: SessionUser
    teacher_no: str
    subject: str
    title: str | None = None
    zodiac_options: list[ZodiacAvatarOption] = Field(default_factory=list)


class TeacherSettingsUpdateRequest(BaseModel):
    user_id: int
    display_name: str
    subject: str
    title: str | None = None
    avatar: str | None = None


class PortalHeroSettings(BaseModel):
    hero_title: str
    hero_subtitle: str
    featured_school_code: str | None = None


class PortalSchoolAdminItem(BaseModel):
    id: int
    code: str
    name: str
    district: str
    slogan: str
    grade_scope: str
    theme: ThemePalette
    features: list[PortalFeature] = Field(default_factory=list)
    metrics: list[QuickStat] = Field(default_factory=list)


class LLMModelOption(BaseModel):
    label: str
    value: str
    provider_hint: str | None = None


class LLMConfigResponse(BaseModel):
    provider_name: str
    base_url: str
    api_key_masked: str | None = None
    has_api_key: bool = False
    model_name: str
    model_options: list[LLMModelOption] = Field(default_factory=list)
    temperature: float = 0.4
    max_tokens: int = 4096
    is_enabled: bool = False
    notes: str | None = None


class PortalAdminDashboardResponse(BaseModel):
    admin_name: str
    hero: PortalHeroSettings
    schools: list[PortalSchoolAdminItem] = Field(default_factory=list)
    announcements: list[PortalAnnouncement] = Field(default_factory=list)
    quick_stats: list[QuickStat] = Field(default_factory=list)
    llm_config: LLMConfigResponse


class PortalHeroUpdateRequest(BaseModel):
    admin_user_id: int
    hero_title: str
    hero_subtitle: str
    featured_school_code: str | None = None


class PortalSchoolUpdateRequest(BaseModel):
    admin_user_id: int
    name: str
    district: str
    slogan: str
    grade_scope: str
    theme: ThemePalette
    features: list[PortalFeature] = Field(default_factory=list)
    metrics: list[QuickStat] = Field(default_factory=list)


class PortalAnnouncementUpsertRequest(BaseModel):
    admin_user_id: int
    title: str
    tag: str
    summary: str
    published_at: datetime
    is_active: bool = True


class LLMConfigUpdateRequest(BaseModel):
    admin_user_id: int
    provider_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    base_url: AnyHttpUrl
    api_key: str | None = None
    clear_api_key: bool = False
    model_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=256, le=32768)
    is_enabled: bool = False
    notes: str | None = None

    @model_validator(mode="after")
    def validate_enabled_state(self):
        if self.is_enabled and self.clear_api_key:
            raise ValueError("启用大模型时不能同时清空 API Key。")
        return self


class AgentCard(BaseModel):
    id: int
    name: str
    role: str
    status: str
    scope_label: str


class AssistantDescriptor(BaseModel):
    title: str
    subtitle: str
    suggestions: list[str] = Field(default_factory=list)
    agents: list[AgentCard] = Field(default_factory=list)
    allow_external_sources: bool = False
    external_sources_note: str | None = None


class QuestionSpec(BaseModel):
    key: str
    type: str
    stem: str
    options: list[str] = Field(default_factory=list)
    correct_answer: str | list[str] | int | float | bool | dict | None = None
    points: int


class ActivitySpec(BaseModel):
    title: str
    instructions: str
    teacher_tip: str
    stage_label: str | None = None
    activity_type: str | None = None
    deliverable: str | None = None
    accepted_file_types: list[str] = Field(default_factory=list)
    review_enabled: bool = False
    rubric_items: list[str] = Field(default_factory=list)
    prompt_starters: list[str] = Field(default_factory=list)
    component_whitelist: list[str] = Field(default_factory=list)
    questions: list[QuestionSpec] = Field(default_factory=list)


class AnalyticsQuestionMetric(BaseModel):
    key: str
    stem: str
    accuracy: float
    submissions: int


class AnalyticsResponse(BaseModel):
    publication_id: int
    submission_count: int
    average_score: float
    average_duration_min: float | None = None
    score_distribution: dict[str, int] = Field(default_factory=dict)
    question_metrics: list[AnalyticsQuestionMetric] = Field(default_factory=list)


class ClassroomSeat(BaseModel):
    seat_no: int
    student_name: str
    status: str
    score: float | None = None


class LabSnapshot(BaseModel):
    classroom_id: int
    classroom_label: str
    view_mode: str
    signed_in_count: int
    student_count: int
    submitted_count: int
    pending_review_count: int
    ip_lock_enabled: bool
    class_password_enabled: bool
    seats: list[ClassroomSeat] = Field(default_factory=list)


class ClassroomOption(BaseModel):
    id: int
    name: str
    school_year: str
    grade: str
    class_no: str
    student_count: int


class LiveSessionDescriptor(BaseModel):
    id: int | None = None
    classroom_id: int
    classroom_label: str
    course_id: int | None = None
    course_title: str | None = None
    status: str
    view_mode: str
    ip_lock_enabled: bool
    started_at: datetime | None = None


class TeacherCourseCard(BaseModel):
    id: int
    title: str
    subject: str
    grade_scope: str
    term: str
    lesson_no: str
    status: str
    assignment_count: int
    published_assignment_count: int
    average_score: float
    submission_rate: float
    agent_enabled: bool
    last_updated: datetime | None = None


class AssignmentPreview(BaseModel):
    activity_id: int
    publication_id: int | None = None
    title: str
    instructions: str
    question_count: int
    component_whitelist: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    due_at: datetime | None = None
    submission_count: int = 0
    average_score: float = 0.0
    auto_generated: bool = True


class ReviewDescriptor(BaseModel):
    id: int
    reviewer_name: str
    reviewer_role: str
    score: float
    comment: str
    reviewed_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class SubmissionAssetDescriptor(BaseModel):
    id: int
    file_name: str
    file_type: str
    media_kind: str
    file_url: str
    preview_url: str | None = None
    size_kb: int | None = None


class SubmissionDescriptor(BaseModel):
    id: int
    student_id: int
    student_name: str
    status: str
    headline: str | None = None
    summary: str | None = None
    submitted_at: datetime | None = None
    preview_asset_url: str | None = None
    average_review_score: float | None = None
    review_count: int = 0
    peer_review_count: int = 0
    teacher_reviewed: bool = False
    teacher_review: ReviewDescriptor | None = None
    assets: list[SubmissionAssetDescriptor] = Field(default_factory=list)
    reviews: list[ReviewDescriptor] = Field(default_factory=list)


class ActivityTaskDescriptor(BaseModel):
    id: int
    title: str
    task_type: str
    task_type_label: str
    status: str
    stage_label: str
    instructions: str
    teacher_tip: str | None = None
    deliverable: str | None = None
    publication_id: int | None = None
    published_at: datetime | None = None
    due_at: datetime | None = None
    question_count: int = 0
    component_whitelist: list[str] = Field(default_factory=list)
    accepted_file_types: list[str] = Field(default_factory=list)
    review_enabled: bool = False
    rubric_items: list[str] = Field(default_factory=list)
    prompt_starters: list[str] = Field(default_factory=list)
    submission_count: int = 0
    submission_target: int = 0
    review_count: int = 0
    pending_teacher_review_count: int = 0
    average_score: float | None = None
    average_review_score: float | None = None
    spec: ActivitySpec | None = None
    recent_submissions: list[SubmissionDescriptor] = Field(default_factory=list)
    recent_reviews: list[ReviewDescriptor] = Field(default_factory=list)
    my_submission: SubmissionDescriptor | None = None
    my_review_queue: list[SubmissionDescriptor] = Field(default_factory=list)


class TeacherDashboardResponse(BaseModel):
    teacher_name: str
    tenant_name: str
    subject: str
    classroom_label: str
    current_classroom_id: int | None = None
    classroom_options: list[ClassroomOption] = Field(default_factory=list)
    quick_stats: list[QuickStat] = Field(default_factory=list)
    lab_snapshot: LabSnapshot
    active_session: LiveSessionDescriptor | None = None
    course_directory: list[TeacherCourseCard] = Field(default_factory=list)
    pending_items: list[PendingItem] = Field(default_factory=list)
    charts: list[ChartPanel] = Field(default_factory=list)
    general_assistant: AssistantDescriptor


class TeacherCourseDetailResponse(BaseModel):
    course: TeacherCourseCard
    classroom_id: int | None = None
    classroom_label: str | None = None
    featured_activity_id: int | None = None
    assignment_preview: AssignmentPreview | None = None
    latest_spec: ActivitySpec | None = None
    analytics: AnalyticsResponse | None = None
    activities: list[ActivityTaskDescriptor] = Field(default_factory=list)
    charts: list[ChartPanel] = Field(default_factory=list)
    recent_submissions: list[PendingItem] = Field(default_factory=list)
    allowed_components: list[str] = Field(default_factory=list)
    course_assistant: AssistantDescriptor


class CourseCreateRequest(BaseModel):
    teacher_user_id: int
    title: str
    subject: str
    grade_scope: str
    term: str
    lesson_no: str
    summary: str | None = None
    create_course_agent: bool = False


class CourseCreateResponse(BaseModel):
    course: TeacherCourseCard
    agent: AgentCard | None = None
    message: str


class ActivityDraftRequest(BaseModel):
    course_id: int
    teacher_user_id: int
    title: str | None = None
    learning_goal: str
    resource_names: list[str] = Field(default_factory=list)
    component_whitelist: list[str] = Field(default_factory=list)


class ActivityDraftResponse(BaseModel):
    activity_id: int
    revision_id: int
    draft_summary: str
    spec: ActivitySpec


class PublishRequest(BaseModel):
    revision_id: int
    classroom_id: int
    published_by_user_id: int
    starts_at: datetime | None = None
    due_at: datetime | None = None


class PublishResponse(BaseModel):
    publication_id: int
    revision_id: int
    classroom_id: int
    status: str


class StartClassRequest(BaseModel):
    teacher_user_id: int
    classroom_id: int
    course_id: int
    view_mode: str = "lab-grid"
    ip_lock_enabled: bool = True
    class_password: str | None = None


class StartClassResponse(BaseModel):
    session: LiveSessionDescriptor
    message: str


class ActivityDocumentRequest(BaseModel):
    teacher_user_id: int
    classroom_id: int | None = None


class GeneratedDocumentResponse(BaseModel):
    activity_id: int
    title: str
    suggested_filename: str
    mime_type: str = "text/markdown"
    content: str


class FeedbackItem(BaseModel):
    title: str
    content: str


class StudentCourseCard(BaseModel):
    id: int
    title: str
    subject: str
    term: str
    lesson_no: str
    status: str
    latest_score: float | None = None
    completion_rate: float
    next_task_title: str | None = None
    next_task_due_at: datetime | None = None


class StudentDashboardResponse(BaseModel):
    student_name: str
    tenant_name: str
    classroom_label: str
    total_score: float
    quick_stats: list[QuickStat] = Field(default_factory=list)
    charts: list[ChartPanel] = Field(default_factory=list)
    course_directory: list[StudentCourseCard] = Field(default_factory=list)
    recent_feedback: list[FeedbackItem] = Field(default_factory=list)
    general_assistant: AssistantDescriptor


class StudentCourseDetailResponse(BaseModel):
    course: StudentCourseCard
    featured_activity_id: int | None = None
    assignment_preview: AssignmentPreview | None = None
    latest_spec: ActivitySpec | None = None
    current_publication_id: int | None = None
    activities: list[ActivityTaskDescriptor] = Field(default_factory=list)
    recent_feedback: list[FeedbackItem] = Field(default_factory=list)
    course_assistant: AssistantDescriptor


class AttemptStartRequest(BaseModel):
    student_user_id: int
    idempotency_key: str
    device_info: str


class AttemptStartResponse(BaseModel):
    attempt_id: int
    status: str
    message: str


class ActivityAnswerPayload(BaseModel):
    question_key: str
    value: str | list[str] | int | float | bool | dict | None = None


class AttemptSubmitRequest(BaseModel):
    answers: list[ActivityAnswerPayload] = Field(default_factory=list)
    total_time_sec: int


class AttemptSubmitResponse(BaseModel):
    attempt_id: int
    auto_score: float
    correct_count: int
    total_questions: int
    feedback: str


class SubmissionAssetUploadPayload(BaseModel):
    file_name: str
    file_type: str
    data_url: str


class WorkSubmissionCreateRequest(BaseModel):
    student_user_id: int
    headline: str | None = None
    summary: str | None = None
    assets: list[SubmissionAssetUploadPayload] = Field(default_factory=list)


class WorkSubmissionResponse(BaseModel):
    submission: SubmissionDescriptor
    message: str


class SubmissionReviewRequest(BaseModel):
    reviewer_user_id: int
    score: float = Field(ge=0, le=100)
    comment: str
    tags: list[str] = Field(default_factory=list)


class SubmissionReviewResponse(BaseModel):
    review: ReviewDescriptor
    message: str
