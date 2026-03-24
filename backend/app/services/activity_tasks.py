from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Activity,
    ActivityPublication,
    ActivityRevision,
    AssignmentAttempt,
    Classroom,
    SubmissionAsset,
    SubmissionReview,
    User,
    WorkSubmission,
)
from app.schemas.contracts import (
    ActivitySpec,
    ActivityTaskDescriptor,
    ReviewDescriptor,
    SubmissionAssetDescriptor,
    SubmissionDescriptor,
)

TASK_TYPE_LABELS = {
    "lesson_guide": "导学任务",
    "interactive_assignment": "交互作业",
    "project_submission": "作品提交",
    "peer_review": "同伴互评",
}


def _is_past(value: datetime | None) -> bool:
    if value is None:
        return False
    if value.tzinfo is None:
        return value < datetime.now()
    return value < datetime.now(UTC)


def latest_revision_for_activity(activity_id: int, db: Session) -> ActivityRevision | None:
    return db.scalar(
        select(ActivityRevision)
        .where(ActivityRevision.activity_id == activity_id)
        .order_by(ActivityRevision.version_no.desc(), ActivityRevision.id.desc())
        .limit(1)
    )


def latest_publication_for_activity(activity_id: int, db: Session, classroom_id: int | None = None) -> ActivityPublication | None:
    stmt = (
        select(ActivityPublication)
        .join(ActivityRevision, ActivityPublication.revision_id == ActivityRevision.id)
        .where(ActivityRevision.activity_id == activity_id)
        .order_by(ActivityPublication.published_at.desc(), ActivityPublication.id.desc())
        .limit(1)
    )
    if classroom_id is not None:
        stmt = stmt.where(ActivityPublication.classroom_id == classroom_id)
    return db.scalar(stmt)


def latest_interactive_publication_for_course(course_id: int, db: Session, classroom_id: int | None = None) -> ActivityPublication | None:
    stmt = (
        select(ActivityPublication)
        .join(ActivityRevision, ActivityPublication.revision_id == ActivityRevision.id)
        .join(Activity, ActivityRevision.activity_id == Activity.id)
        .where(Activity.course_id == course_id)
        .where(Activity.type == "interactive_assignment")
        .order_by(ActivityPublication.published_at.desc(), ActivityPublication.id.desc())
        .limit(1)
    )
    if classroom_id is not None:
        stmt = stmt.where(ActivityPublication.classroom_id == classroom_id)
    return db.scalar(stmt)


def resolve_activity_spec(
    activity: Activity,
    db: Session,
    classroom_id: int | None = None,
) -> tuple[ActivityRevision | None, ActivitySpec | None, ActivityPublication | None]:
    publication = latest_publication_for_activity(activity.id, db, classroom_id)
    revision = db.get(ActivityRevision, publication.revision_id) if publication else None
    if not revision and activity.latest_revision_id:
        revision = db.get(ActivityRevision, activity.latest_revision_id)
    revision = revision or latest_revision_for_activity(activity.id, db)
    spec = ActivitySpec.model_validate(revision.spec_json) if revision else None
    return revision, spec, publication


def work_submissions_for_activity(
    activity_id: int,
    db: Session,
    publication_id: int | None = None,
) -> list[WorkSubmission]:
    stmt = (
        select(WorkSubmission)
        .where(WorkSubmission.activity_id == activity_id)
        .order_by(WorkSubmission.submitted_at.desc(), WorkSubmission.id.desc())
    )
    if publication_id is not None:
        stmt = stmt.where(WorkSubmission.publication_id == publication_id)
    return db.scalars(stmt).all()


def submission_reviews_for_submission(submission_id: int, db: Session) -> list[SubmissionReview]:
    return db.scalars(
        select(SubmissionReview)
        .where(SubmissionReview.submission_id == submission_id)
        .order_by(SubmissionReview.reviewed_at.desc(), SubmissionReview.id.desc())
    ).all()


def build_review_descriptor(review: SubmissionReview, db: Session) -> ReviewDescriptor:
    reviewer = db.get(User, review.reviewer_id)
    return ReviewDescriptor(
        id=review.id,
        reviewer_name=reviewer.display_name if reviewer else f"用户 {review.reviewer_id}",
        reviewer_role=review.reviewer_role,
        score=round(review.score, 1),
        comment=review.comment,
        reviewed_at=review.reviewed_at,
        tags=list(review.tags_json or []),
    )


def build_submission_descriptor(
    submission: WorkSubmission,
    db: Session,
    *,
    review_limit: int = 3,
) -> SubmissionDescriptor:
    student = db.get(User, submission.student_id)
    assets = db.scalars(
        select(SubmissionAsset)
        .where(SubmissionAsset.submission_id == submission.id)
        .order_by(SubmissionAsset.id.asc())
    ).all()
    reviews = submission_reviews_for_submission(submission.id, db)
    review_preview = reviews[:review_limit]
    teacher_review_row = next((review for review in reviews if review.reviewer_role == "teacher"), None)
    peer_review_count = len([review for review in reviews if review.reviewer_role != "teacher"])
    average_review_score = round(sum(review.score for review in reviews) / len(reviews), 1) if reviews else None
    preview_asset = next(
        (
            asset
            for asset in assets
            if asset.preview_url or asset.media_kind == "image"
        ),
        assets[0] if assets else None,
    )
    return SubmissionDescriptor(
        id=submission.id,
        student_id=submission.student_id,
        student_name=student.display_name if student else f"学生 {submission.student_id}",
        status=submission.status,
        headline=submission.headline,
        summary=submission.summary,
        submitted_at=submission.submitted_at,
        preview_asset_url=(preview_asset.preview_url or preview_asset.file_url) if preview_asset else None,
        average_review_score=average_review_score,
        review_count=len(reviews),
        peer_review_count=peer_review_count,
        teacher_reviewed=teacher_review_row is not None,
        teacher_review=build_review_descriptor(teacher_review_row, db) if teacher_review_row else None,
        assets=[
            SubmissionAssetDescriptor(
                id=asset.id,
                file_name=asset.file_name,
                file_type=asset.file_type,
                media_kind=asset.media_kind,
                file_url=asset.file_url,
                preview_url=asset.preview_url,
                size_kb=asset.size_kb,
            )
            for asset in assets
        ],
        reviews=[build_review_descriptor(review, db) for review in review_preview],
    )


def _activity_submission_target(classroom_id: int | None, db: Session) -> int:
    classroom = db.get(Classroom, classroom_id) if classroom_id else None
    return classroom.student_count if classroom else 0


def _interactive_attempts(publication_id: int | None, db: Session) -> list[AssignmentAttempt]:
    if publication_id is None:
        return []
    return db.scalars(
        select(AssignmentAttempt)
        .where(AssignmentAttempt.publication_id == publication_id)
        .where(AssignmentAttempt.submitted_at.is_not(None))
        .order_by(AssignmentAttempt.submitted_at.desc(), AssignmentAttempt.id.desc())
    ).all()


def _student_activity_status(
    *,
    activity: Activity,
    publication: ActivityPublication | None,
    spec: ActivitySpec | None,
    student_id: int | None,
    db: Session,
) -> str:
    if not student_id:
        return ""

    if activity.type == "interactive_assignment" and publication:
        own_attempt = db.scalar(
            select(AssignmentAttempt)
            .where(AssignmentAttempt.publication_id == publication.id)
            .where(AssignmentAttempt.student_id == student_id)
            .where(AssignmentAttempt.submitted_at.is_not(None))
            .order_by(AssignmentAttempt.submitted_at.desc(), AssignmentAttempt.id.desc())
            .limit(1)
        )
        if own_attempt:
            return "我已完成"
        return "待作答"

    if spec and spec.accepted_file_types:
        own_submission = db.scalar(
            select(WorkSubmission)
            .where(WorkSubmission.activity_id == activity.id)
            .where(WorkSubmission.student_id == student_id)
            .order_by(WorkSubmission.submitted_at.desc(), WorkSubmission.id.desc())
            .limit(1)
        )
        if own_submission:
            return "我已提交"
        return "待提交"

    return ""


def build_activity_task_descriptor(
    activity: Activity,
    db: Session,
    *,
    classroom_id: int | None = None,
    student_id: int | None = None,
    stage_index: int | None = None,
) -> ActivityTaskDescriptor:
    _, spec, publication = resolve_activity_spec(activity, db, classroom_id)
    spec = spec or ActivitySpec(title=activity.title, instructions="当前活动尚未配置说明。", teacher_tip="")
    attempts = _interactive_attempts(publication.id if publication else None, db) if activity.type == "interactive_assignment" else []
    submissions = work_submissions_for_activity(activity.id, db, publication.id if publication else None)
    all_reviews: list[SubmissionReview] = []
    for submission in submissions:
        all_reviews.extend(submission_reviews_for_submission(submission.id, db))

    average_attempt_score = round(sum(attempt.auto_score or 0 for attempt in attempts) / len(attempts), 1) if attempts else None
    average_review_score = round(sum(review.score for review in all_reviews) / len(all_reviews), 1) if all_reviews else None
    submission_count = len(attempts) if activity.type == "interactive_assignment" else len(submissions)
    target = _activity_submission_target(classroom_id, db)

    status = "未发布"
    if publication:
        status = "进行中"
        if _is_past(publication.due_at):
            status = "已截止"
    elif activity.is_published:
        status = "已准备"

    student_status = _student_activity_status(
        activity=activity,
        publication=publication,
        spec=spec,
        student_id=student_id,
        db=db,
    )
    if student_status:
        status = student_status

    my_submission = None
    my_review_queue: list[SubmissionDescriptor] = []
    if student_id and spec.accepted_file_types:
        own_submission = db.scalar(
            select(WorkSubmission)
            .where(WorkSubmission.activity_id == activity.id)
            .where(WorkSubmission.student_id == student_id)
            .order_by(WorkSubmission.submitted_at.desc(), WorkSubmission.id.desc())
            .limit(1)
        )
        if own_submission:
            my_submission = build_submission_descriptor(own_submission, db)

        if spec.review_enabled:
            reviewed_submission_ids = {
                review.submission_id
                for review in db.scalars(
                    select(SubmissionReview)
                    .where(SubmissionReview.reviewer_id == student_id)
                ).all()
            }
            queue_candidates = [
                submission
                for submission in submissions
                if submission.student_id != student_id and submission.id not in reviewed_submission_ids
            ]
            my_review_queue = [build_submission_descriptor(item, db, review_limit=2) for item in queue_candidates[:4]]

    recent_submission_descriptors = [build_submission_descriptor(item, db, review_limit=3) for item in submissions]
    pending_teacher_review_count = len([item for item in recent_submission_descriptors if not item.teacher_reviewed])
    recent_submission_descriptors.sort(
        key=lambda item: (
            not item.teacher_reviewed,
            item.submitted_at.isoformat() if item.submitted_at else "",
        ),
        reverse=True,
    )
    recent_submissions = recent_submission_descriptors[:4]
    recent_reviews = [build_review_descriptor(item, db) for item in all_reviews[:4]]

    return ActivityTaskDescriptor(
        id=activity.id,
        title=spec.title or activity.title,
        task_type=activity.type,
        task_type_label=TASK_TYPE_LABELS.get(activity.type, activity.type),
        status=status,
        stage_label=spec.stage_label or f"活动 {stage_index or 1}",
        instructions=spec.instructions,
        teacher_tip=spec.teacher_tip,
        deliverable=spec.deliverable,
        publication_id=publication.id if publication else None,
        published_at=publication.published_at if publication else None,
        due_at=publication.due_at if publication else activity.due_at,
        question_count=len(spec.questions),
        component_whitelist=list(spec.component_whitelist),
        accepted_file_types=list(spec.accepted_file_types),
        review_enabled=spec.review_enabled,
        rubric_items=list(spec.rubric_items),
        prompt_starters=list(spec.prompt_starters),
        submission_count=submission_count,
        submission_target=target,
        review_count=len(all_reviews),
        pending_teacher_review_count=pending_teacher_review_count,
        average_score=average_attempt_score,
        average_review_score=average_review_score,
        spec=spec,
        recent_submissions=recent_submissions,
        recent_reviews=recent_reviews,
        my_submission=my_submission,
        my_review_queue=my_review_queue,
    )
