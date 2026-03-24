import base64
import binascii
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    Activity,
    ActivityPublication,
    ActivityRevision,
    AssignmentAnswer,
    AssignmentAttempt,
    Classroom,
    Course,
    SubmissionAsset,
    SubmissionReview,
    StudentProfile,
    Tenant,
    User,
    WorkSubmission,
)
from app.db.session import get_db
from app.schemas.contracts import (
    ActivitySpec,
    AssistantDescriptor,
    AttemptStartRequest,
    AttemptStartResponse,
    AttemptSubmitRequest,
    AttemptSubmitResponse,
    ChartDatum,
    ChartPanel,
    FeedbackItem,
    QuickStat,
    SubmissionReviewRequest,
    SubmissionReviewResponse,
    StudentCourseDetailResponse,
    StudentDashboardResponse,
    WorkSubmissionCreateRequest,
    WorkSubmissionResponse,
)
from app.core.config import UPLOAD_DIR
from app.services.activity_tasks import (
    build_activity_task_descriptor,
    build_review_descriptor,
    build_submission_descriptor,
    resolve_activity_spec,
)
from app.services.dashboard_data import (
    build_agent_cards,
    build_assignment_preview,
    build_student_course_card,
    course_publications,
)
from app.services.grading import grade_answers

router = APIRouter()


def _get_student(user_id: int, db: Session) -> tuple[User, StudentProfile, Tenant, Classroom | None]:
    user = db.get(User, user_id)
    if not user or user.role != "student":
        raise HTTPException(status_code=404, detail="学生不存在。")

    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="学生档案不存在。")

    tenant = db.get(Tenant, user.tenant_id)
    classroom = db.get(Classroom, profile.classroom_id)
    return user, profile, tenant or Tenant(name="默认学校", code="default"), classroom


def _student_general_assistant(tenant_id: int, tenant_name: str, db: Session) -> AssistantDescriptor:
    return AssistantDescriptor(
        title="通用智能体",
        subtitle="提供学习导航、平台使用帮助和通用启发式提示，不直接输出标准答案。",
        suggestions=[
            "帮我把今天待完成的课程按优先级排一下",
            "根据我的最近成绩，推荐一个适合先复习的知识点",
            "告诉我学生中心里各张图表分别代表什么",
        ],
        agents=build_agent_cards(
            tenant_id=tenant_id,
            scope_type="tenant",
            scope_id=tenant_id,
            scope_label=tenant_name,
            db=db,
        ),
        allow_external_sources=False,
    )


def _student_course_assistant(course: Course, db: Session) -> AssistantDescriptor:
    return AssistantDescriptor(
        title="课程智能体",
        subtitle="进入课程后从侧边抽屉弹出，默认采用分步提示、纠错和反问式辅导。",
        suggestions=[
            "先不要直接给答案，帮我拆成 3 个步骤",
            "根据这份作业的错题，提醒我需要回看哪些知识点",
            "如果我卡住了，请给一个更简单的提示版本",
        ],
        agents=build_agent_cards(
            tenant_id=course.tenant_id,
            scope_type="course",
            scope_id=course.id,
            scope_label=course.title,
            db=db,
        ),
        allow_external_sources=True,
        external_sources_note="课程智能体仅使用课程上下文和白名单外部来源，回答过程会被记录审计。",
    )


def _decode_data_url(data_url: str) -> bytes:
    if "," not in data_url:
        raise HTTPException(status_code=400, detail="上传内容格式不正确。")
    _, encoded = data_url.split(",", 1)
    try:
        return base64.b64decode(encoded)
    except binascii.Error as exc:
        raise HTTPException(status_code=400, detail="上传文件编码损坏。") from exc


def _guess_media_kind(file_type: str) -> str:
    if file_type.startswith("image/"):
        return "image"
    if "pdf" in file_type or "word" in file_type or "presentation" in file_type or "sheet" in file_type or "text" in file_type:
        return "document"
    return "file"


def _save_submission_assets(
    *,
    submission_id: int,
    tenant_id: int,
    activity_id: int,
    assets: list,
    db: Session,
):
    target_dir = UPLOAD_DIR / f"tenant-{tenant_id}" / f"activity-{activity_id}" / f"submission-{submission_id}"
    target_dir.mkdir(parents=True, exist_ok=True)

    for index, asset in enumerate(assets, start=1):
        file_name = Path(asset.file_name).name or f"asset-{index}"
        file_bytes = _decode_data_url(asset.data_url)
        stored_name = f"{index:02d}-{uuid4().hex[:8]}-{file_name}"
        file_path = target_dir / stored_name
        file_path.write_bytes(file_bytes)
        file_url = f"/api/v1/public/uploads/tenant-{tenant_id}/activity-{activity_id}/submission-{submission_id}/{stored_name}"
        media_kind = _guess_media_kind(asset.file_type)
        db.add(
            SubmissionAsset(
                submission_id=submission_id,
                file_name=file_name,
                file_type=asset.file_type,
                media_kind=media_kind,
                file_url=file_url,
                preview_url=file_url if media_kind == "image" else None,
                size_kb=max(1, round(len(file_bytes) / 1024)),
            )
        )


@router.get("/dashboard/{user_id}", response_model=StudentDashboardResponse)
def get_student_dashboard(user_id: int, db: Session = Depends(get_db)):
    user, profile, tenant, classroom = _get_student(user_id, db)
    courses = db.scalars(
        select(Course)
        .where(Course.tenant_id == user.tenant_id)
        .where(Course.is_published.is_(True))
        .order_by(Course.lesson_no.asc(), Course.id.asc())
    ).all()
    course_cards = [
        build_student_course_card(
            course,
            student_id=user.id,
            classroom_id=profile.classroom_id,
            db=db,
        )
        for course in courses
    ]

    latest_scores = [card.latest_score for card in course_cards if card.latest_score is not None]
    total_score = round(sum(latest_scores), 1) if latest_scores else 0.0
    average_score = round(total_score / len(latest_scores), 1) if latest_scores else 0.0
    completed_count = len([card for card in course_cards if card.status == "已完成"])
    pending_count = len([card for card in course_cards if card.status != "已完成"])

    recent_feedback = []
    for card in course_cards[:3]:
        if card.latest_score is None:
            recent_feedback.append(
                FeedbackItem(
                    title=card.title,
                    content="当前课程已有任务待进入，完成后会回流成绩、题目分析和教师反馈。",
                )
            )
        else:
            recent_feedback.append(
                FeedbackItem(
                    title=card.title,
                    content=f"最近一次成绩 {card.latest_score} 分，建议结合课程目录中的作业分析继续巩固。",
                )
            )

    charts = [
        ChartPanel(
            key="student-score-trend",
            title="课程成绩概览",
            subtitle="按课程查看最近一次已提交作业成绩",
            chart_type="bar",
            unit="分",
            points=[
                ChartDatum(label=card.lesson_no, value=card.latest_score or 0)
                for card in course_cards
            ],
        ),
        ChartPanel(
            key="student-completion-rate",
            title="课程完成率",
            subtitle="帮助学生快速判断哪些课程还需要继续推进",
            chart_type="line",
            unit="%",
            points=[
                ChartDatum(label=card.lesson_no, value=card.completion_rate)
                for card in course_cards
            ],
        ),
        ChartPanel(
            key="student-task-status",
            title="任务状态分布",
            subtitle="首页优先呈现完成课程与待推进课程数量",
            chart_type="pie",
            unit="门",
            points=[
                ChartDatum(label="已完成", value=completed_count),
                ChartDatum(label="待推进", value=pending_count),
            ],
        ),
    ]

    return StudentDashboardResponse(
        student_name=user.display_name,
        tenant_name=tenant.name,
        classroom_label=classroom.name if classroom else profile.classroom_label,
        total_score=total_score,
        quick_stats=[
            QuickStat(title="总分成绩", value=str(total_score), hint="按已提交课程最近一次成绩汇总"),
            QuickStat(title="平均成绩", value=str(average_score), hint="便于快速查看整体表现"),
            QuickStat(title="课程目录", value=str(len(course_cards)), hint="统一进入课程、作业与分析"),
            QuickStat(title="待推进任务", value=str(pending_count), hint="优先进入未完成或进行中的课程"),
        ],
        charts=charts,
        course_directory=course_cards,
        recent_feedback=recent_feedback,
        general_assistant=_student_general_assistant(user.tenant_id, tenant.name, db),
    )


@router.get("/courses/{course_id}", response_model=StudentCourseDetailResponse)
def get_student_course_detail(course_id: int, user_id: int, db: Session = Depends(get_db)):
    user, profile, _, _ = _get_student(user_id, db)
    course = db.get(Course, course_id)
    if not course or not course.is_published or course.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="课程不存在。")

    course_card = build_student_course_card(
        course,
        student_id=user.id,
        classroom_id=profile.classroom_id,
        db=db,
    )
    preview, spec, publication = build_assignment_preview(course.id, db, profile.classroom_id)
    activity_rows = db.scalars(
        select(Activity)
        .where(Activity.course_id == course.id)
        .order_by(Activity.id.asc())
    ).all()
    activities = [
        build_activity_task_descriptor(
            activity,
            db,
            classroom_id=profile.classroom_id,
            student_id=user.id,
            stage_index=index,
        )
        for index, activity in enumerate(activity_rows, start=1)
    ]
    featured_activity = next(
        (item for item in activities if item.status in {"待作答", "待提交", "进行中"}),
        activities[0] if activities else None,
    )

    recent_feedback = []
    publications = course_publications(course.id, db, profile.classroom_id)
    publication_ids = [item.id for item in publications]
    attempts = (
        db.scalars(
            select(AssignmentAttempt)
            .where(AssignmentAttempt.student_id == user.id)
            .where(AssignmentAttempt.publication_id.in_(publication_ids))
            .where(AssignmentAttempt.submitted_at.is_not(None))
            .order_by(AssignmentAttempt.submitted_at.desc(), AssignmentAttempt.id.desc())
            .limit(3)
        ).all()
        if publication_ids
        else []
    )
    for attempt in attempts:
        related_publication = db.get(ActivityPublication, attempt.publication_id)
        related_revision = db.get(ActivityRevision, related_publication.revision_id) if related_publication else None
        related_spec = ActivitySpec.model_validate(related_revision.spec_json) if related_revision else None
        recent_feedback.append(
            FeedbackItem(
                title=related_spec.title if related_spec else course.title,
                content=f"最近一次自动评分 {attempt.auto_score or 0} 分，可在课程目录中继续查看题目预览与复习建议。",
            )
        )
    own_submissions = db.scalars(
        select(WorkSubmission)
        .join(Activity, WorkSubmission.activity_id == Activity.id)
        .where(Activity.course_id == course.id)
        .where(WorkSubmission.student_id == user.id)
        .order_by(WorkSubmission.submitted_at.desc(), WorkSubmission.id.desc())
        .limit(3)
    ).all()
    for submission in own_submissions:
        descriptor = build_submission_descriptor(submission, db, review_limit=2)
        if descriptor.reviews:
            latest_review = descriptor.reviews[0]
            recent_feedback.append(
                FeedbackItem(
                    title=descriptor.headline or "作品互评反馈",
                    content=f"{latest_review.reviewer_name} 给出 {latest_review.score} 分：{latest_review.comment}",
                )
            )
        elif descriptor.review_count == 0:
            recent_feedback.append(
                FeedbackItem(
                    title=descriptor.headline or "作品上传",
                    content="作品已提交，等待教师或同伴完成评价后会回流到这里。",
                )
            )

    return StudentCourseDetailResponse(
        course=course_card,
        featured_activity_id=featured_activity.id if featured_activity else None,
        assignment_preview=preview,
        latest_spec=spec,
        current_publication_id=publication.id if publication else None,
        activities=activities,
        recent_feedback=recent_feedback,
        course_assistant=_student_course_assistant(course, db),
    )


@router.post("/publications/{publication_id}/attempts", response_model=AttemptStartResponse)
def start_attempt(publication_id: int, payload: AttemptStartRequest, db: Session = Depends(get_db)):
    publication = db.get(ActivityPublication, publication_id)
    if not publication:
        raise HTTPException(status_code=404, detail="发布版本不存在。")

    existing = db.scalar(
        select(AssignmentAttempt)
        .where(AssignmentAttempt.publication_id == publication_id)
        .where(AssignmentAttempt.student_id == payload.student_user_id)
        .where(AssignmentAttempt.idempotency_key == payload.idempotency_key)
    )
    if existing:
        return AttemptStartResponse(attempt_id=existing.id, status=existing.status, message="复用已有作答记录。")

    attempt = AssignmentAttempt(
        publication_id=publication_id,
        student_id=payload.student_user_id,
        status="in_progress",
        idempotency_key=payload.idempotency_key,
        started_at=datetime.now(UTC),
        total_time_sec=0,
        device_info=payload.device_info,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return AttemptStartResponse(attempt_id=attempt.id, status=attempt.status, message="已开始本次作答。")


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptSubmitResponse)
def submit_attempt(attempt_id: int, payload: AttemptSubmitRequest, db: Session = Depends(get_db)):
    attempt = db.get(AssignmentAttempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="作答记录不存在。")

    publication = db.get(ActivityPublication, attempt.publication_id)
    revision = db.get(ActivityRevision, publication.revision_id)
    spec = ActivitySpec.model_validate(revision.spec_json)
    grading = grade_answers(spec.questions, payload.answers)

    db.execute(delete(AssignmentAnswer).where(AssignmentAnswer.attempt_id == attempt.id))
    for result in grading["answers"]:
        db.add(
            AssignmentAnswer(
                attempt_id=attempt.id,
                question_key=result["question_key"],
                answer_json=result["answer"],
                is_correct=result["is_correct"],
                score=result["score"],
                feedback=result["feedback"],
            )
        )

    attempt.status = "submitted"
    attempt.auto_score = grading["total_score"]
    attempt.teacher_score = None
    attempt.submitted_at = datetime.now(UTC)
    attempt.total_time_sec = payload.total_time_sec
    db.commit()

    return AttemptSubmitResponse(
        attempt_id=attempt.id,
        auto_score=grading["total_score"],
        correct_count=grading["correct_count"],
        total_questions=len(spec.questions),
        feedback="作答已提交，课程目录中的作业分析与学生总览图表会自动刷新。",
    )


@router.post("/activities/{activity_id}/submissions", response_model=WorkSubmissionResponse)
def create_work_submission(activity_id: int, payload: WorkSubmissionCreateRequest, db: Session = Depends(get_db)):
    user, profile, _, _ = _get_student(payload.student_user_id, db)
    activity = db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在。")

    course = db.get(Course, activity.course_id)
    if not course or course.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="课程不存在。")

    _, activity_spec, activity_publication = resolve_activity_spec(activity, db, profile.classroom_id)
    if not activity_spec or not activity_spec.accepted_file_types:
        raise HTTPException(status_code=400, detail="当前活动不支持作品提交。")
    if not payload.assets:
        raise HTTPException(status_code=400, detail="请至少上传一个文件。")

    submission = WorkSubmission(
        activity_id=activity.id,
        publication_id=activity_publication.id if activity_publication else None,
        student_id=user.id,
        headline=payload.headline,
        summary=payload.summary,
        status="submitted",
        submitted_at=datetime.now(UTC),
        overall_score=None,
    )
    db.add(submission)
    db.flush()
    _save_submission_assets(
        submission_id=submission.id,
        tenant_id=user.tenant_id,
        activity_id=activity.id,
        assets=payload.assets,
        db=db,
    )
    db.commit()
    db.refresh(submission)

    return WorkSubmissionResponse(
        submission=build_submission_descriptor(submission, db),
        message="作品已提交，教师端和课程评价面板会同步刷新。",
    )


@router.post("/submissions/{submission_id}/reviews", response_model=SubmissionReviewResponse)
def create_submission_review(submission_id: int, payload: SubmissionReviewRequest, db: Session = Depends(get_db)):
    reviewer, _, _, _ = _get_student(payload.reviewer_user_id, db)
    submission = db.get(WorkSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="作品不存在。")
    if submission.student_id == reviewer.id:
        raise HTTPException(status_code=400, detail="不能评价自己的作品。")

    activity = db.get(Activity, submission.activity_id)
    course = db.get(Course, activity.course_id) if activity else None
    if not activity or not course or course.tenant_id != reviewer.tenant_id:
        raise HTTPException(status_code=404, detail="课程不存在。")

    existing = db.scalar(
        select(SubmissionReview)
        .where(SubmissionReview.submission_id == submission.id)
        .where(SubmissionReview.reviewer_id == reviewer.id)
        .limit(1)
    )
    if existing:
        existing.score = payload.score
        existing.comment = payload.comment
        existing.tags_json = payload.tags
        existing.reviewed_at = datetime.now(UTC)
        existing.reviewer_role = "student"
        review = existing
    else:
        review = SubmissionReview(
            submission_id=submission.id,
            reviewer_id=reviewer.id,
            reviewer_role="student",
            score=payload.score,
            comment=payload.comment,
            tags_json=payload.tags,
            reviewed_at=datetime.now(UTC),
        )
        db.add(review)

    db.commit()
    db.refresh(review)

    return SubmissionReviewResponse(
        review=build_review_descriptor(review, db),
        message="评价已提交，作品热度和分析图表会自动更新。",
    )
