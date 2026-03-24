from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active")
    theme_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    ai_quota_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="active")


class Classroom(TimestampMixin, Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    school_year: Mapped[str] = mapped_column(String(20), nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    class_no: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    homeroom_teacher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    student_count: Mapped[int] = mapped_column(Integer, default=49)


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    student_no: Mapped[str] = mapped_column(String(30), nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), nullable=False)
    classroom_label: Mapped[str] = mapped_column(String(40), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(10))
    seat_no: Mapped[int | None] = mapped_column(Integer)


class TeacherProfile(TimestampMixin, Base):
    __tablename__ = "teacher_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    teacher_no: Mapped[str] = mapped_column(String(30), nullable=False)
    subject: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str | None] = mapped_column(String(40))


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    subject: Mapped[str] = mapped_column(String(40), nullable=False)
    grade_scope: Mapped[str] = mapped_column(String(40), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)
    lesson_no: Mapped[str] = mapped_column(String(20), nullable=False)
    cover_image: Mapped[str | None] = mapped_column(String(255))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)


class Activity(TimestampMixin, Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    latest_revision_id: Mapped[int | None] = mapped_column(Integer)
    rubric_id: Mapped[int | None] = mapped_column(Integer)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ActivityRevision(TimestampMixin, Base):
    __tablename__ = "activity_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    spec_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    render_mode: Mapped[str] = mapped_column(String(40), default="activity_renderer")
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, default=True)
    prompt_version: Mapped[str | None] = mapped_column(String(40))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="draft")


class ActivityPublication(TimestampMixin, Base):
    __tablename__ = "activity_publications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    revision_id: Mapped[int] = mapped_column(ForeignKey("activity_revisions.id"), nullable=False)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), nullable=False)
    published_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="published")


class AssignmentAttempt(TimestampMixin, Base):
    __tablename__ = "assignment_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    publication_id: Mapped[int] = mapped_column(ForeignKey("activity_publications.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    auto_score: Mapped[float | None] = mapped_column()
    teacher_score: Mapped[float | None] = mapped_column()
    total_time_sec: Mapped[int | None] = mapped_column(Integer)
    device_info: Mapped[str | None] = mapped_column(String(120))


class AssignmentAnswer(TimestampMixin, Base):
    __tablename__ = "assignment_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("assignment_attempts.id"), nullable=False)
    question_key: Mapped[str] = mapped_column(String(40), nullable=False)
    answer_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(default=0.0)
    feedback: Mapped[str | None] = mapped_column(Text)


class LiveClassSession(TimestampMixin, Base):
    __tablename__ = "live_class_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")
    view_mode: Mapped[str] = mapped_column(String(20), default="lab-grid")
    ip_lock_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    class_password_hash: Mapped[str | None] = mapped_column(String(255))
    signed_in_count: Mapped[int] = mapped_column(Integer, default=42)
    submitted_count: Mapped[int] = mapped_column(Integer, default=35)
    pending_review_count: Mapped[int] = mapped_column(Integer, default=12)


class QuestionComponentRegistry(TimestampMixin, Base):
    __tablename__ = "question_component_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    component_key: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    schema_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    renderer_name: Mapped[str] = mapped_column(String(80), nullable=False)
    scoring_adapter: Mapped[str] = mapped_column(String(80), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    tenant_scope: Mapped[str] = mapped_column(String(40), default="global")


class Resource(TimestampMixin, Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    file_url: Mapped[str | None] = mapped_column(String(255))
    preview_url: Mapped[str | None] = mapped_column(String(255))
    visibility: Mapped[str] = mapped_column(String(20), default="tenant")


class WorkSubmission(TimestampMixin, Base):
    __tablename__ = "work_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), nullable=False)
    publication_id: Mapped[int | None] = mapped_column(ForeignKey("activity_publications.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    headline: Mapped[str | None] = mapped_column(String(120))
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    overall_score: Mapped[float | None] = mapped_column()


class SubmissionAsset(TimestampMixin, Base):
    __tablename__ = "submission_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("work_submissions.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(120), nullable=False)
    media_kind: Mapped[str] = mapped_column(String(40), default="file")
    file_url: Mapped[str] = mapped_column(String(255), nullable=False)
    preview_url: Mapped[str | None] = mapped_column(String(255))
    size_kb: Mapped[int | None] = mapped_column(Integer)


class SubmissionReview(TimestampMixin, Base):
    __tablename__ = "submission_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("work_submissions.id"), nullable=False)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewer_role: Mapped[str] = mapped_column(String(20), default="student")
    score: Mapped[float] = mapped_column(nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AIAgent(TimestampMixin, Base):
    __tablename__ = "ai_agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(40), default="course")
    scope_id: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
