from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Activity,
    ActivityPublication,
    ActivityRevision,
    AIAgent,
    AssignmentAnswer,
    AssignmentAttempt,
    Classroom,
    Course,
    WorkSubmission,
)
from app.schemas.contracts import (
    ActivitySpec,
    AgentCard,
    AnalyticsQuestionMetric,
    AnalyticsResponse,
    AssignmentPreview,
    StudentCourseCard,
    TeacherCourseCard,
)
from app.services.activity_tasks import (
    latest_interactive_publication_for_course,
    latest_publication_for_activity,
    resolve_activity_spec,
    work_submissions_for_activity,
)


def _round_score(value: float | None) -> float:
    return round(value or 0.0, 1)


def _attempts_for_publication(publication_id: int, db: Session) -> list[AssignmentAttempt]:
    return db.scalars(
        select(AssignmentAttempt)
        .where(AssignmentAttempt.publication_id == publication_id)
        .where(AssignmentAttempt.submitted_at.is_not(None))
        .order_by(AssignmentAttempt.id.desc())
    ).all()


def course_publications(course_id: int, db: Session, classroom_id: int | None = None) -> list[ActivityPublication]:
    stmt = (
        select(ActivityPublication)
        .join(ActivityRevision, ActivityPublication.revision_id == ActivityRevision.id)
        .join(Activity, ActivityRevision.activity_id == Activity.id)
        .where(Activity.course_id == course_id)
        .order_by(ActivityPublication.published_at.desc(), ActivityPublication.id.desc())
    )
    if classroom_id is not None:
        stmt = stmt.where(ActivityPublication.classroom_id == classroom_id)
    return db.scalars(stmt).all()


def latest_publication_for_course(course_id: int, db: Session, classroom_id: int | None = None) -> ActivityPublication | None:
    publications = course_publications(course_id, db, classroom_id)
    return publications[0] if publications else None


def latest_revision_for_course(course_id: int, db: Session) -> ActivityRevision | None:
    activity = db.scalar(select(Activity).where(Activity.course_id == course_id).order_by(Activity.id.desc()).limit(1))
    if not activity:
        return None
    if activity.latest_revision_id:
        revision = db.get(ActivityRevision, activity.latest_revision_id)
        if revision:
            return revision
    return db.scalar(
        select(ActivityRevision)
        .where(ActivityRevision.activity_id == activity.id)
        .order_by(ActivityRevision.version_no.desc(), ActivityRevision.id.desc())
        .limit(1)
    )


def build_agent_cards(
    *,
    tenant_id: int,
    scope_type: str,
    scope_id: int,
    scope_label: str,
    db: Session,
) -> list[AgentCard]:
    agents = db.scalars(
        select(AIAgent)
        .where(AIAgent.tenant_id == tenant_id)
        .where(AIAgent.scope_type == scope_type)
        .where(AIAgent.scope_id == scope_id)
        .order_by(AIAgent.id.asc())
    ).all()
    return [
        AgentCard(
            id=agent.id,
            name=agent.name,
            role=agent.role,
            status=agent.status,
            scope_label=scope_label,
        )
        for agent in agents
    ]


def build_analytics(publication_id: int, db: Session) -> AnalyticsResponse:
    publication = db.get(ActivityPublication, publication_id)
    revision = db.get(ActivityRevision, publication.revision_id)
    spec = ActivitySpec.model_validate(revision.spec_json)
    attempts = _attempts_for_publication(publication_id, db)

    answers_by_attempt: dict[int, dict[str, AssignmentAnswer]] = {}
    for attempt in attempts:
        answers = db.scalars(select(AssignmentAnswer).where(AssignmentAnswer.attempt_id == attempt.id)).all()
        answers_by_attempt[attempt.id] = {answer.question_key: answer for answer in answers}

    question_metrics: list[AnalyticsQuestionMetric] = []
    for question in spec.questions:
        total = len(attempts)
        correct = 0
        for attempt in attempts:
            answer = answers_by_attempt.get(attempt.id, {}).get(question.key)
            if answer and answer.is_correct:
                correct += 1
        question_metrics.append(
            AnalyticsQuestionMetric(
                key=question.key,
                stem=question.stem,
                accuracy=round(correct / total, 2) if total else 0.0,
                submissions=total,
            )
        )

    durations = [attempt.total_time_sec for attempt in attempts if attempt.total_time_sec]
    average_duration_min = round((sum(durations) / len(durations)) / 60, 1) if durations else None
    average_score = round(sum(attempt.auto_score or 0 for attempt in attempts) / len(attempts), 1) if attempts else 0.0

    return AnalyticsResponse(
        publication_id=publication_id,
        submission_count=len(attempts),
        average_score=average_score,
        average_duration_min=average_duration_min,
        score_distribution={
            "90-100": len([attempt for attempt in attempts if (attempt.auto_score or 0) >= 90]),
            "70-89": len([attempt for attempt in attempts if 70 <= (attempt.auto_score or 0) < 90]),
            "0-69": len([attempt for attempt in attempts if (attempt.auto_score or 0) < 70]),
        },
        question_metrics=question_metrics,
    )


def build_assignment_preview(
    course_id: int,
    db: Session,
    classroom_id: int | None = None,
) -> tuple[AssignmentPreview | None, ActivitySpec | None, ActivityPublication | None]:
    publication = latest_interactive_publication_for_course(course_id, db, classroom_id)
    revision = db.get(ActivityRevision, publication.revision_id) if publication else latest_revision_for_course(course_id, db)
    if not revision:
        return None, None, publication

    activity = db.get(Activity, revision.activity_id)
    spec = ActivitySpec.model_validate(revision.spec_json)
    attempts = _attempts_for_publication(publication.id, db) if publication else []
    average_score = round(sum(attempt.auto_score or 0 for attempt in attempts) / len(attempts), 1) if attempts else 0.0

    preview = AssignmentPreview(
        activity_id=activity.id if activity else 0,
        publication_id=publication.id if publication else None,
        title=spec.title,
        instructions=spec.instructions,
        question_count=len(spec.questions),
        component_whitelist=spec.component_whitelist,
        published_at=publication.published_at if publication else None,
        due_at=publication.due_at if publication else None,
        submission_count=len(attempts),
        average_score=average_score,
        auto_generated=revision.generated_by_ai,
    )
    return preview, spec, publication


def build_teacher_course_card(course: Course, db: Session, classroom_id: int | None = None) -> TeacherCourseCard:
    activities = db.scalars(select(Activity).where(Activity.course_id == course.id).order_by(Activity.id.asc())).all()
    publications = course_publications(course.id, db, classroom_id)
    latest_publication = publications[0] if publications else None
    latest_interactive_publication = latest_interactive_publication_for_course(course.id, db, classroom_id)
    latest_activity = None
    latest_submissions: list[WorkSubmission] = []
    latest_attempts: list[AssignmentAttempt] = []
    if latest_publication:
        revision = db.get(ActivityRevision, latest_publication.revision_id)
        latest_activity = db.get(Activity, revision.activity_id) if revision else None
    if latest_interactive_publication:
        latest_attempts = _attempts_for_publication(latest_interactive_publication.id, db)
    elif latest_activity:
        latest_submissions = work_submissions_for_activity(latest_activity.id, db, latest_publication.id if latest_publication else None)
    classroom = db.get(Classroom, classroom_id) if classroom_id else None
    student_count = classroom.student_count if classroom else 0
    current_submission_count = len(latest_attempts) if latest_attempts else len(latest_submissions)
    submission_rate = round((current_submission_count / student_count) * 100, 1) if student_count else 0.0
    latest_revision = latest_revision_for_course(course.id, db)
    last_updated = latest_publication.published_at if latest_publication else (latest_revision.updated_at if latest_revision else course.updated_at)
    agent_enabled = bool(
        db.scalar(
            select(AIAgent)
            .where(AIAgent.scope_type == "course")
            .where(AIAgent.scope_id == course.id)
            .limit(1)
        )
    )
    return TeacherCourseCard(
        id=course.id,
        title=course.title,
        subject=course.subject,
        grade_scope=course.grade_scope,
        term=course.term,
        lesson_no=course.lesson_no,
        status="已发布" if course.is_published else "草稿",
        assignment_count=len(activities),
        published_assignment_count=len(publications),
        average_score=_round_score(sum(attempt.auto_score or 0 for attempt in latest_attempts) / len(latest_attempts) if latest_attempts else 0.0),
        submission_rate=submission_rate,
        agent_enabled=agent_enabled,
        last_updated=last_updated,
    )


def _sorted_attempts(attempts: Iterable[AssignmentAttempt]) -> list[AssignmentAttempt]:
    return sorted(
        attempts,
        key=lambda attempt: (
            attempt.submitted_at.isoformat() if attempt.submitted_at else "",
            attempt.id,
        ),
        reverse=True,
    )


def build_student_course_card(
    course: Course,
    *,
    student_id: int,
    classroom_id: int,
    db: Session,
) -> StudentCourseCard:
    activities = db.scalars(select(Activity).where(Activity.course_id == course.id).order_by(Activity.id.asc())).all()
    publications = course_publications(course.id, db, classroom_id)
    publication_ids = [publication.id for publication in publications]
    attempts = (
        db.scalars(
            select(AssignmentAttempt)
            .where(AssignmentAttempt.student_id == student_id)
            .where(AssignmentAttempt.publication_id.in_(publication_ids))
        ).all()
        if publication_ids
        else []
    )
    own_work_submissions = db.scalars(
        select(WorkSubmission)
        .where(WorkSubmission.student_id == student_id)
        .where(WorkSubmission.activity_id.in_([activity.id for activity in activities] or [-1]))
        .order_by(WorkSubmission.submitted_at.desc(), WorkSubmission.id.desc())
    ).all()
    sorted_attempts = _sorted_attempts(attempts)
    latest_attempt = next((attempt for attempt in sorted_attempts if attempt.submitted_at), None)
    submitted_publication_ids = {attempt.publication_id for attempt in attempts if attempt.submitted_at}
    submitted_activity_ids = {submission.activity_id for submission in own_work_submissions}

    actionable_total = 0
    completed_total = 0
    next_task_title = None
    next_task_due_at = None
    status = "待发布"

    for activity in activities:
        _, spec, publication = resolve_activity_spec(activity, db, classroom_id)
        has_questions = bool(spec and spec.questions)
        accepts_submission = bool(spec and spec.accepted_file_types)
        if not (has_questions or accepts_submission):
            continue

        actionable_total += 1
        is_complete = False
        if publication and publication.id in submitted_publication_ids:
            is_complete = True
        if activity.id in submitted_activity_ids:
            is_complete = True

        if is_complete:
            completed_total += 1
        elif next_task_title is None:
            next_task_title = spec.title if spec else activity.title
            next_task_due_at = publication.due_at if publication else activity.due_at

    completion_rate = round((completed_total / actionable_total) * 100, 1) if actionable_total else 0.0
    if actionable_total and completed_total == actionable_total:
        status = "已完成"
    elif actionable_total:
        status = "进行中"
    preview, _, latest_publication = build_assignment_preview(course.id, db, classroom_id)
    if next_task_title is None and preview:
        next_task_title = preview.title
        next_task_due_at = latest_publication.due_at if latest_publication else None

    return StudentCourseCard(
        id=course.id,
        title=course.title,
        subject=course.subject,
        term=course.term,
        lesson_no=course.lesson_no,
        status=status,
        latest_score=latest_attempt.auto_score if latest_attempt else None,
        completion_rate=completion_rate,
        next_task_title=next_task_title,
        next_task_due_at=next_task_due_at,
    )
