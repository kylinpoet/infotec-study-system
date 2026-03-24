from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import (
    Activity,
    ActivityPublication,
    ActivityRevision,
    AIAgent,
    AssignmentAttempt,
    Classroom,
    Course,
    LiveClassSession,
    QuestionComponentRegistry,
    SubmissionReview,
    StudentProfile,
    TeacherProfile,
    Tenant,
    User,
    WorkSubmission,
)
from app.db.session import get_db
from app.schemas.contracts import (
    ActivityDocumentRequest,
    ActivityDraftRequest,
    ActivityDraftResponse,
    AnalyticsResponse,
    AssistantDescriptor,
    ChartPanel,
    ChartDatum,
    ClassroomOption,
    CourseCreateRequest,
    CourseCreateResponse,
    GeneratedDocumentResponse,
    LabSnapshot,
    LiveSessionDescriptor,
    PendingItem,
    PublishRequest,
    PublishResponse,
    QuickStat,
    StartClassRequest,
    StartClassResponse,
    SubmissionReviewRequest,
    SubmissionReviewResponse,
    TeacherCourseDetailResponse,
    TeacherDashboardResponse,
)
from app.services.activity_generator import build_activity_spec
from app.services.activity_tasks import (
    build_activity_task_descriptor,
    build_review_descriptor,
    build_submission_descriptor,
    latest_interactive_publication_for_course,
    latest_publication_for_activity,
    resolve_activity_spec,
)
from app.services.dashboard_data import (
    build_agent_cards,
    build_analytics,
    build_assignment_preview,
    build_teacher_course_card,
)

router = APIRouter()


def _get_teacher(user_id: int, db: Session) -> tuple[User, Tenant, TeacherProfile | None]:
    user = db.get(User, user_id)
    if not user or user.role != "teacher":
        raise HTTPException(status_code=404, detail="教师不存在。")
    tenant = db.get(Tenant, user.tenant_id)
    profile = db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
    return user, tenant or Tenant(name="默认学校", code="default"), profile


def _get_primary_classroom(tenant_id: int, db: Session) -> Classroom | None:
    return db.scalar(
        select(Classroom)
        .where(Classroom.tenant_id == tenant_id)
        .order_by(Classroom.id.asc())
        .limit(1)
    )


def _resolve_classroom(tenant_id: int, classroom_id: int | None, db: Session) -> Classroom | None:
    if classroom_id is not None:
        classroom = db.scalar(
            select(Classroom)
            .where(Classroom.tenant_id == tenant_id)
            .where(Classroom.id == classroom_id)
            .limit(1)
        )
        if classroom:
            return classroom
    return _get_primary_classroom(tenant_id, db)


def _classroom_options(tenant_id: int, db: Session) -> list[ClassroomOption]:
    classrooms = db.scalars(
        select(Classroom)
        .where(Classroom.tenant_id == tenant_id)
        .order_by(Classroom.grade.asc(), Classroom.class_no.asc(), Classroom.id.asc())
    ).all()
    return [
        ClassroomOption(
            id=classroom.id,
            name=classroom.name,
            school_year=classroom.school_year,
            grade=classroom.grade,
            class_no=classroom.class_no,
            student_count=classroom.student_count,
        )
        for classroom in classrooms
    ]


def _live_session_descriptor(
    live_session: LiveClassSession | None,
    classroom: Classroom | None,
    db: Session,
) -> LiveSessionDescriptor | None:
    if not classroom:
        return None
    course = db.get(Course, live_session.course_id) if live_session else None
    return LiveSessionDescriptor(
        id=live_session.id if live_session else None,
        classroom_id=classroom.id,
        classroom_label=classroom.name,
        course_id=course.id if course else None,
        course_title=course.title if course else None,
        status=live_session.status if live_session else "idle",
        view_mode=live_session.view_mode if live_session else "lab-grid",
        ip_lock_enabled=live_session.ip_lock_enabled if live_session else False,
        started_at=live_session.started_at if live_session else None,
    )


def _latest_live_session(classroom_id: int, db: Session) -> LiveClassSession | None:
    return db.scalar(
        select(LiveClassSession)
        .where(LiveClassSession.classroom_id == classroom_id)
        .order_by(LiveClassSession.id.desc())
        .limit(1)
    )


def _status_for_seat(seat_no: int, attempt: AssignmentAttempt | None) -> str:
    if attempt and attempt.submitted_at:
        return "已提交"
    if seat_no % 6 == 0:
        return "离线"
    if seat_no % 2 == 0:
        return "AI作业中"
    return "已签到"


def _build_lab_snapshot(
    *,
    classroom: Classroom | None,
    course_id: int | None,
    live_session: LiveClassSession | None,
    db: Session,
) -> LabSnapshot:
    if not classroom:
        return LabSnapshot(
            classroom_id=0,
            classroom_label="未绑定班级",
            view_mode="lab-grid",
            signed_in_count=0,
            student_count=0,
            submitted_count=0,
            pending_review_count=0,
            ip_lock_enabled=False,
            class_password_enabled=False,
            seats=[],
        )

    publication = latest_interactive_publication_for_course(course_id, db, classroom.id) if course_id else None
    profiles = db.scalars(
        select(StudentProfile)
        .where(StudentProfile.classroom_id == classroom.id)
        .order_by(StudentProfile.seat_no.asc(), StudentProfile.id.asc())
        .limit(8)
    ).all()

    seats = []
    if profiles:
        for profile in profiles:
            student = db.get(User, profile.user_id)
            attempt = None
            if publication:
                attempt = db.scalar(
                    select(AssignmentAttempt)
                    .where(AssignmentAttempt.publication_id == publication.id)
                    .where(AssignmentAttempt.student_id == profile.user_id)
                    .order_by(AssignmentAttempt.id.desc())
                    .limit(1)
                )
            seats.append(
                {
                    "seat_no": profile.seat_no or 0,
                    "student_name": student.display_name if student else profile.student_no,
                    "status": _status_for_seat(profile.seat_no or 0, attempt),
                    "score": attempt.auto_score if attempt and attempt.submitted_at else None,
                }
            )
    else:
        for seat_no in range(1, min(classroom.student_count, 8) + 1):
            seats.append(
                {
                    "seat_no": seat_no,
                    "student_name": f"机位 {seat_no:02d}",
                    "status": "待签到" if seat_no % 2 else "空闲机位",
                    "score": None,
                }
            )

    return LabSnapshot(
        classroom_id=classroom.id,
        classroom_label=classroom.name,
        view_mode=live_session.view_mode if live_session else "lab-grid",
        signed_in_count=live_session.signed_in_count if live_session else max(classroom.student_count - 3, 0),
        student_count=classroom.student_count,
        submitted_count=live_session.submitted_count if live_session else len([seat for seat in seats if seat["status"] == "已提交"]),
        pending_review_count=live_session.pending_review_count if live_session else max(len(seats) // 2, 0),
        ip_lock_enabled=live_session.ip_lock_enabled if live_session else True,
        class_password_enabled=bool(live_session and live_session.class_password_hash),
        seats=seats,
    )


def _teacher_general_assistant(tenant_id: int, tenant_name: str, db: Session) -> AssistantDescriptor:
    return AssistantDescriptor(
        title="通用智能体",
        subtitle="面向教师侧的跨课程助手，可协助生成备课建议、课堂讲评和平台操作说明。",
        suggestions=[
            "根据当前教师首页，整理今天最值得优先处理的 3 项事项",
            "结合机房状态，生成一段课堂开场提示词",
            "根据课程目录推荐下一门适合生成 AI 作业的课程",
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


def _teacher_course_assistant(course: Course, db: Session) -> AssistantDescriptor:
    return AssistantDescriptor(
        title="课程智能体",
        subtitle="仅在当前课程上下文内工作，可联动课程知识、作业结果与外部白名单资源。",
        suggestions=[
            "根据这门课最近一次作业结果，生成 5 分钟讲评提纲",
            "补 2 道基础题和 1 道开放题，用于课后巩固",
            "总结本课程当前最薄弱的知识点，并给出补救建议",
        ],
        agents=build_agent_cards(
            tenant_id=course.tenant_id,
            scope_type="course",
            scope_id=course.id,
            scope_label=course.title,
            db=db,
        ),
        allow_external_sources=True,
        external_sources_note="课程智能体可接入教师配置的外部网站白名单，并保留快照与审计日志。",
    )


def _activity_briefing_content(
    *,
    course: Course,
    classroom: Classroom | None,
    activity: Activity,
    db: Session,
) -> str:
    descriptor = build_activity_task_descriptor(
        activity,
        db,
        classroom_id=classroom.id if classroom else None,
    )
    top_submissions = descriptor.recent_submissions[:3]
    lines = [
        f"# {descriptor.title} 讲评摘要",
        "",
        f"- 课程：{course.title}",
        f"- 班级：{classroom.name if classroom else '未绑定班级'}",
        f"- 活动阶段：{descriptor.stage_label}",
        f"- 任务类型：{descriptor.task_type_label}",
        f"- 完成进度：{descriptor.submission_count}/{descriptor.submission_target or '--'}",
        f"- 互评条数：{descriptor.review_count}",
        f"- 待教师点评：{descriptor.pending_teacher_review_count}",
        "",
        "## 教师讲评重点",
        f"- 活动说明：{descriptor.instructions}",
    ]
    if descriptor.teacher_tip:
        lines.append(f"- 教师提示：{descriptor.teacher_tip}")
    if descriptor.average_score is not None:
        lines.append(f"- 交互作业平均分：{descriptor.average_score} 分")
    if descriptor.average_review_score is not None:
        lines.append(f"- 作品平均评价：{descriptor.average_review_score} 分")
    if descriptor.rubric_items:
        lines.append(f"- 评价维度：{'、'.join(descriptor.rubric_items)}")

    lines.extend(["", "## 讲评建议", "- 先复盘任务目标，再展示优秀案例。"])
    if descriptor.pending_teacher_review_count:
        lines.append(f"- 当前还有 {descriptor.pending_teacher_review_count} 份作品未完成教师点评，建议优先补齐。")
    if descriptor.review_count:
        lines.append("- 可结合互评中高频出现的标签，提炼班级共性问题。")
    if descriptor.spec and descriptor.spec.questions:
        weak_questions = sorted(
            descriptor.spec.questions,
            key=lambda question: next(
                (
                    metric.accuracy
                    for metric in build_analytics(descriptor.publication_id, db).question_metrics
                    if metric.key == question.key
                ),
                1.0,
            ),
        )[:2] if descriptor.publication_id else []
        if weak_questions:
            lines.append(f"- 交互作业中可重点回看：{'、'.join(question.stem for question in weak_questions)}")

    lines.extend(["", "## 优先展示作品"])
    if top_submissions:
        for index, submission in enumerate(top_submissions, start=1):
            teacher_line = submission.teacher_review.comment if submission.teacher_review else "尚未教师点评"
            lines.extend(
                [
                    f"{index}. {submission.student_name}《{submission.headline or '学生作品'}》",
                    f"   - 简述：{submission.summary or '已提交作品。'}",
                    f"   - 评价：{submission.average_review_score or '--'} 分，教师点评：{teacher_line}",
                ]
            )
    else:
        lines.append("- 当前活动暂无可展示作品。")

    return "\n".join(lines)


def _lesson_script_content(
    *,
    course: Course,
    classroom: Classroom | None,
    activity: Activity,
    db: Session,
) -> str:
    descriptor = build_activity_task_descriptor(
        activity,
        db,
        classroom_id=classroom.id if classroom else None,
    )
    showcase_submissions = descriptor.recent_submissions[:2]
    lines = [
        f"# {descriptor.title} 课堂讲评稿",
        "",
        "## 开场",
        f"同学们，今天我们一起回看《{course.title}》中的“{descriptor.title}”。先对照任务目标，看看班级目前完成了 {descriptor.submission_count} 份作品。",
        "",
        "## 第一段：回顾任务目标",
        f"请大家先重新读一遍任务要求：{descriptor.instructions}",
    ]
    if descriptor.rubric_items:
        lines.append(f"本次我们重点从 {('、'.join(descriptor.rubric_items))} 这几个维度来看。")

    lines.extend(["", "## 第二段：展示优秀作品"])
    if showcase_submissions:
        for submission in showcase_submissions:
            lines.append(
                f"- 请看 {submission.student_name} 的《{submission.headline or '学生作品'}》：{submission.summary or '这份作品完整呈现了任务要求。'}"
            )
            if submission.teacher_review:
                lines.append(f"  教师点评：{submission.teacher_review.comment}")
    else:
        lines.append("- 当前还没有完成教师点评的优秀作品，可以先展示互评较高的作品。")

    lines.extend(
        [
            "",
            "## 第三段：班级共性提醒",
            f"- 还有 {descriptor.pending_teacher_review_count} 份作品等待教师点评，说明部分同学还需要进一步完善表达。",
            "- 讲评时先肯定亮点，再指出一条最值得改进的点，让同学知道下一步怎么做。",
            "",
            "## 结尾",
            "请同学们根据讲评再完善一次自己的作品说明，并把今天学到的一个关键方法记到学习单中。",
        ]
    )
    return "\n".join(lines)


@router.get("/dashboard/{user_id}", response_model=TeacherDashboardResponse)
def get_teacher_dashboard(user_id: int, classroom_id: int | None = None, db: Session = Depends(get_db)):
    user, tenant, profile = _get_teacher(user_id, db)
    classroom = _resolve_classroom(user.tenant_id, classroom_id, db)
    courses = db.scalars(
        select(Course)
        .where(Course.tenant_id == user.tenant_id)
        .where(Course.is_published.is_(True))
        .order_by(Course.lesson_no.asc(), Course.id.asc())
    ).all()
    current_course_id = courses[0].id if courses else None
    live_session = _latest_live_session(classroom.id, db) if classroom else None
    if live_session:
        current_course_id = live_session.course_id

    course_cards = [build_teacher_course_card(course, db, classroom.id if classroom else None) for course in courses]
    lab_snapshot = _build_lab_snapshot(
        classroom=classroom,
        course_id=current_course_id,
        live_session=live_session,
        db=db,
    )

    total_course_agents = db.scalar(
        select(func.count(AIAgent.id))
        .where(AIAgent.tenant_id == user.tenant_id)
        .where(AIAgent.scope_type == "course")
    ) or 0
    tenant_work_submissions = db.scalars(
        select(WorkSubmission)
        .join(Activity, WorkSubmission.activity_id == Activity.id)
        .join(Course, Activity.course_id == Course.id)
        .where(Course.tenant_id == user.tenant_id)
        .order_by(WorkSubmission.submitted_at.desc(), WorkSubmission.id.desc())
    ).all()
    pending_teacher_review_count = 0
    for submission in tenant_work_submissions:
        descriptor = build_submission_descriptor(submission, db, review_limit=1)
        if not descriptor.teacher_reviewed:
            pending_teacher_review_count += 1
    latest_publication = (
        latest_interactive_publication_for_course(current_course_id, db, classroom.id if classroom else None)
        if current_course_id
        else None
    )
    latest_analytics = build_analytics(latest_publication.id, db) if latest_publication else None

    pending_items = [
        PendingItem(
            title="课堂待跟进",
            status=f"{lab_snapshot.pending_review_count} 项待复核",
            meta="重点查看已自动评分但仍需教师复核的作业。",
        ),
        PendingItem(
            title="课程智能体维护",
            status=f"{total_course_agents} 个已绑定",
            meta="课程专属智能体为独立模块，可在课程目录中单独管理。",
        ),
        PendingItem(
            title="作品待教师点评",
            status=f"{pending_teacher_review_count} 份待处理",
            meta="优先处理没有教师点评的作品，作品热度和优秀案例会在课程页自动更新。",
        ),
    ]
    if latest_analytics:
        pending_items.append(
            PendingItem(
                title="最近一次 AI 作业分析",
                status=f"均分 {latest_analytics.average_score}",
                meta=f"共 {latest_analytics.submission_count} 份提交，适合立即生成讲评。",
            )
        )

    charts = [
        ChartPanel(
            key="course-average-score",
            title="课程平均分",
            subtitle="按课程查看最近一次已发布作业的平均得分",
            chart_type="bar",
            unit="分",
            points=[ChartDatum(label=item.title, value=item.average_score) for item in course_cards],
        ),
        ChartPanel(
            key="course-submission-rate",
            title="课程提交率",
            subtitle="反映课程目录中各门课当前班级的作业提交情况",
            chart_type="line",
            unit="%",
            points=[ChartDatum(label=item.lesson_no, value=item.submission_rate) for item in course_cards],
        ),
        ChartPanel(
            key="lab-status",
            title="机房课堂状态",
            subtitle="实时呈现签到、提交与待复核状态",
            chart_type="bar",
            unit="人",
            points=[
                ChartDatum(label="已签到", value=lab_snapshot.signed_in_count),
                ChartDatum(label="已提交", value=lab_snapshot.submitted_count),
                ChartDatum(label="待复核", value=lab_snapshot.pending_review_count),
            ],
        ),
    ]

    return TeacherDashboardResponse(
        teacher_name=user.display_name,
        tenant_name=tenant.name,
        subject=profile.subject if profile else "信息科技",
        classroom_label=classroom.name if classroom else "未绑定班级",
        current_classroom_id=classroom.id if classroom else None,
        classroom_options=_classroom_options(user.tenant_id, db),
        quick_stats=[
            QuickStat(title="课程目录", value=str(len(course_cards)), hint="支持按课程进入作业预览与分析"),
            QuickStat(title="当前机房", value=lab_snapshot.classroom_label, hint="保留机房视图、IP 锁定与班级密码"),
            QuickStat(title="待复核作业", value=str(lab_snapshot.pending_review_count), hint="教师复核后成绩会回流学生中心"),
            QuickStat(title="待点评作品", value=str(pending_teacher_review_count), hint="教师点评后会同步更新作品展示与互评热度"),
        ],
        lab_snapshot=lab_snapshot,
        active_session=_live_session_descriptor(live_session, classroom, db),
        course_directory=course_cards,
        pending_items=pending_items,
        charts=charts,
        general_assistant=_teacher_general_assistant(user.tenant_id, tenant.name, db),
    )


@router.get("/courses/{course_id}", response_model=TeacherCourseDetailResponse)
def get_teacher_course_detail(course_id: int, classroom_id: int | None = None, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course or not course.is_published:
        raise HTTPException(status_code=404, detail="课程不存在。")

    classroom = _resolve_classroom(course.tenant_id, classroom_id, db)
    course_card = build_teacher_course_card(course, db, classroom.id if classroom else None)
    preview, spec, publication = build_assignment_preview(course.id, db, classroom.id if classroom else None)
    analytics = build_analytics(publication.id, db) if publication else None
    activity_rows = db.scalars(
        select(Activity)
        .where(Activity.course_id == course.id)
        .order_by(Activity.id.asc())
    ).all()
    activities = [
        build_activity_task_descriptor(
            activity,
            db,
            classroom_id=classroom.id if classroom else None,
            stage_index=index,
        )
        for index, activity in enumerate(activity_rows, start=1)
    ]
    featured_activity = next(
        (item for item in reversed(activities) if item.status in {"进行中", "已截止", "已准备"}),
        activities[0] if activities else None,
    )

    recent_submissions: list[PendingItem] = []
    if publication:
        attempts = db.scalars(
            select(AssignmentAttempt)
            .where(AssignmentAttempt.publication_id == publication.id)
            .where(AssignmentAttempt.submitted_at.is_not(None))
            .order_by(AssignmentAttempt.submitted_at.desc(), AssignmentAttempt.id.desc())
            .limit(5)
        ).all()
        for attempt in attempts:
            student = db.get(User, attempt.student_id)
            minutes = round((attempt.total_time_sec or 0) / 60, 1)
            recent_submissions.append(
                PendingItem(
                    title=student.display_name if student else f"学生 {attempt.student_id}",
                    status=f"{attempt.auto_score or 0} 分",
                    meta=f"{minutes} 分钟完成，状态：{attempt.status}",
                )
            )

    work_items = db.scalars(
        select(WorkSubmission)
        .join(Activity, WorkSubmission.activity_id == Activity.id)
        .where(Activity.course_id == course.id)
        .order_by(WorkSubmission.submitted_at.desc(), WorkSubmission.id.desc())
    ).all()
    work_descriptors = [build_submission_descriptor(submission, db, review_limit=3) for submission in work_items]
    for descriptor in work_descriptors[:5]:
        recent_submissions.append(
            PendingItem(
                title=f"{descriptor.student_name} · {descriptor.headline or '作品提交'}",
                status=(
                    f"待教师点评 / {descriptor.review_count} 条评价"
                    if not descriptor.teacher_reviewed
                    else f"已点评 / {descriptor.review_count} 条评价"
                ),
                meta=descriptor.summary or "已回流到教师后台，可继续查看作品预览与互评记录。",
            )
        )

    image_asset_count = 0
    document_asset_count = 0
    teacher_reviewed_count = 0
    for descriptor in work_descriptors:
        if descriptor.teacher_reviewed:
            teacher_reviewed_count += 1
        for asset in descriptor.assets:
            if asset.media_kind == "image":
                image_asset_count += 1
            elif asset.media_kind == "document":
                document_asset_count += 1

    charts = [
        ChartPanel(
            key="activity-submission-progress",
            title="活动任务提交进度",
            subtitle="按课程活动查看当前班级的完成节奏，作品上传与交互作业统一纳入统计。",
            chart_type="bar",
            unit="%",
            points=[
                ChartDatum(
                    label=item.stage_label,
                    value=round((item.submission_count / item.submission_target) * 100, 1) if item.submission_target else 0,
                )
                for item in activities
            ],
        ),
        ChartPanel(
            key="activity-review-heat",
            title="作品评价活跃度",
            subtitle="展示每个活动目前累计的互评条数，便于判断是否需要教师引导补评。",
            chart_type="line",
            unit="条",
            points=[ChartDatum(label=item.stage_label, value=item.review_count) for item in activities],
        ),
        ChartPanel(
            key="teacher-review-progress",
            title="教师点评进度",
            subtitle="按活动查看当前还有多少作品等待教师点评。",
            chart_type="bar",
            unit="份",
            points=[ChartDatum(label=item.stage_label, value=item.pending_teacher_review_count) for item in activities],
        ),
        ChartPanel(
            key="asset-media-distribution",
            title="作品附件类型分布",
            subtitle="帮助教师快速判断本课程更适合做图片展示墙还是文档讲评。",
            chart_type="pie",
            unit="个",
            points=[
                ChartDatum(label="图片附件", value=image_asset_count),
                ChartDatum(label="文档附件", value=document_asset_count),
                ChartDatum(label="教师已点评作品", value=teacher_reviewed_count),
            ],
        ),
    ]
    if analytics:
        charts.extend(
            [
                ChartPanel(
                    key="question-accuracy",
                    title="题目正确率",
                    subtitle="方便教师快速定位需要讲评的知识点",
                    chart_type="bar",
                    unit="%",
                    points=[
                        ChartDatum(label=metric.key, value=round(metric.accuracy * 100, 1))
                        for metric in analytics.question_metrics
                    ],
                ),
                ChartPanel(
                    key="score-distribution",
                    title="分数分布",
                    subtitle="课程目录内查看作业分析，不占用工作台首页篇幅",
                    chart_type="pie",
                    unit="份",
                    points=[
                        ChartDatum(label=label, value=value)
                        for label, value in analytics.score_distribution.items()
                    ],
                ),
            ]
        )

    allowed_components = [
        registry.component_key
        for registry in db.scalars(
            select(QuestionComponentRegistry)
            .where(QuestionComponentRegistry.enabled.is_(True))
            .order_by(QuestionComponentRegistry.id.asc())
        ).all()
    ]

    return TeacherCourseDetailResponse(
        course=course_card,
        classroom_id=classroom.id if classroom else None,
        classroom_label=classroom.name if classroom else None,
        featured_activity_id=featured_activity.id if featured_activity else None,
        assignment_preview=preview,
        latest_spec=spec,
        analytics=analytics,
        activities=activities,
        charts=charts,
        recent_submissions=recent_submissions[:8],
        allowed_components=allowed_components,
        course_assistant=_teacher_course_assistant(course, db),
    )


@router.post("/courses", response_model=CourseCreateResponse)
def create_course(payload: CourseCreateRequest, db: Session = Depends(get_db)):
    teacher, _, _ = _get_teacher(payload.teacher_user_id, db)

    course = Course(
        tenant_id=teacher.tenant_id,
        title=payload.title,
        subject=payload.subject,
        grade_scope=payload.grade_scope,
        term=payload.term,
        lesson_no=payload.lesson_no,
        cover_image=None,
        is_published=True,
    )
    db.add(course)
    db.flush()

    agent_card = None
    if payload.create_course_agent:
        agent = AIAgent(
            tenant_id=teacher.tenant_id,
            scope_type="course",
            scope_id=course.id,
            role="课程助教",
            name=f"{payload.title} 课程智能体",
            system_prompt=(
                f"你负责课程《{payload.title}》的备课辅助、作业讲评与课堂资源推荐。"
                f"课程摘要：{payload.summary or '教师将在后续补充课程资料。'}"
            ),
            status="active",
        )
        db.add(agent)
        db.flush()
        agent_card = build_agent_cards(
            tenant_id=teacher.tenant_id,
            scope_type="course",
            scope_id=course.id,
            scope_label=course.title,
            db=db,
        )[0]

    db.commit()
    classroom = _get_primary_classroom(teacher.tenant_id, db)
    return CourseCreateResponse(
        course=build_teacher_course_card(course, db, classroom.id if classroom else None),
        agent=agent_card,
        message="课程已创建，可在课程目录中继续生成作业、查看分析并管理课程智能体。",
    )


@router.post("/activity-drafts/generate", response_model=ActivityDraftResponse)
def generate_activity_draft(payload: ActivityDraftRequest, db: Session = Depends(get_db)):
    course = db.get(Course, payload.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在。")

    activity = db.scalar(
        select(Activity)
        .where(Activity.course_id == course.id)
        .order_by(Activity.id.desc())
        .limit(1)
    )
    if not activity:
        activity = Activity(
            course_id=course.id,
            title=payload.title or f"{course.title} AI 交互作业",
            type="interactive_assignment",
            latest_revision_id=None,
            rubric_id=None,
            is_published=False,
        )
        db.add(activity)
        db.flush()

    next_version = (
        db.scalar(
            select(func.max(ActivityRevision.version_no)).where(ActivityRevision.activity_id == activity.id)
        )
        or 0
    ) + 1

    spec = build_activity_spec(payload)
    revision = ActivityRevision(
        activity_id=activity.id,
        version_no=next_version,
        schema_version="1.0",
        spec_json=spec.model_dump(),
        render_mode="activity_renderer",
        generated_by_ai=True,
        prompt_version="draft-v2",
        created_by=payload.teacher_user_id,
        status="draft",
    )
    db.add(revision)
    db.flush()

    activity.title = spec.title
    activity.latest_revision_id = revision.id
    db.commit()

    return ActivityDraftResponse(
        activity_id=activity.id,
        revision_id=revision.id,
        draft_summary="已生成结构化交互作业草案。教师可在课程目录中预览后再发布到班级。",
        spec=spec,
    )


@router.post("/publications", response_model=PublishResponse)
def publish_revision(payload: PublishRequest, db: Session = Depends(get_db)):
    revision = db.get(ActivityRevision, payload.revision_id)
    classroom = db.get(Classroom, payload.classroom_id)
    if not revision or not classroom:
        raise HTTPException(status_code=404, detail="发布对象不存在。")

    activity = db.get(Activity, revision.activity_id)
    publication = ActivityPublication(
        revision_id=revision.id,
        classroom_id=classroom.id,
        published_by=payload.published_by_user_id,
        starts_at=payload.starts_at or datetime.now(UTC),
        due_at=payload.due_at or (datetime.now(UTC) + timedelta(days=7)),
        status="published",
    )
    revision.status = "published"
    if activity:
        activity.is_published = True
        activity.latest_revision_id = revision.id
        activity.due_at = publication.due_at
    db.add(publication)
    db.commit()
    db.refresh(publication)

    return PublishResponse(
        publication_id=publication.id,
        revision_id=revision.id,
        classroom_id=classroom.id,
        status=publication.status,
    )


@router.post("/live-sessions/start", response_model=StartClassResponse)
def start_live_session(payload: StartClassRequest, db: Session = Depends(get_db)):
    teacher, _, _ = _get_teacher(payload.teacher_user_id, db)
    classroom = db.scalar(
        select(Classroom)
        .where(Classroom.tenant_id == teacher.tenant_id)
        .where(Classroom.id == payload.classroom_id)
        .limit(1)
    )
    course = db.get(Course, payload.course_id)
    if not classroom or not course or course.tenant_id != teacher.tenant_id:
        raise HTTPException(status_code=404, detail="班级或课程不存在。")

    session = _latest_live_session(classroom.id, db)
    if not session:
        session = LiveClassSession(
            tenant_id=teacher.tenant_id,
            classroom_id=classroom.id,
            course_id=course.id,
            status="active",
            view_mode=payload.view_mode,
            ip_lock_enabled=payload.ip_lock_enabled,
            class_password_hash=hash_password(payload.class_password) if payload.class_password else None,
            signed_in_count=0,
            submitted_count=0,
            pending_review_count=0,
        )
        db.add(session)
        db.flush()
    else:
        session.tenant_id = teacher.tenant_id
        session.classroom_id = classroom.id
        session.course_id = course.id
        session.status = "active"
        session.view_mode = payload.view_mode
        session.ip_lock_enabled = payload.ip_lock_enabled
        session.class_password_hash = hash_password(payload.class_password) if payload.class_password else None
        session.started_at = datetime.now(UTC)
        session.ended_at = None

    db.commit()
    db.refresh(session)
    return StartClassResponse(
        session=_live_session_descriptor(session, classroom, db) or LiveSessionDescriptor(
            classroom_id=classroom.id,
            classroom_label=classroom.name,
            course_id=course.id,
            course_title=course.title,
            status="active",
            view_mode=payload.view_mode,
            ip_lock_enabled=payload.ip_lock_enabled,
        ),
        message=f"已为 {classroom.name} 开启《{course.title}》课堂。",
    )


@router.post("/activities/{activity_id}/briefing-summary", response_model=GeneratedDocumentResponse)
def export_activity_briefing_summary(
    activity_id: int,
    payload: ActivityDocumentRequest,
    db: Session = Depends(get_db),
):
    teacher, _, _ = _get_teacher(payload.teacher_user_id, db)
    activity = db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在。")
    course = db.get(Course, activity.course_id)
    if not course or course.tenant_id != teacher.tenant_id:
        raise HTTPException(status_code=404, detail="课程不存在。")
    classroom = _resolve_classroom(teacher.tenant_id, payload.classroom_id, db)
    title = f"{course.title} - {activity.title} 讲评摘要"
    return GeneratedDocumentResponse(
        activity_id=activity.id,
        title=title,
        suggested_filename=f"{course.lesson_no.lower()}-activity-{activity.id}-briefing.md",
        content=_activity_briefing_content(course=course, classroom=classroom, activity=activity, db=db),
    )


@router.post("/activities/{activity_id}/lesson-script", response_model=GeneratedDocumentResponse)
def generate_activity_lesson_script(
    activity_id: int,
    payload: ActivityDocumentRequest,
    db: Session = Depends(get_db),
):
    teacher, _, _ = _get_teacher(payload.teacher_user_id, db)
    activity = db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在。")
    course = db.get(Course, activity.course_id)
    if not course or course.tenant_id != teacher.tenant_id:
        raise HTTPException(status_code=404, detail="课程不存在。")
    classroom = _resolve_classroom(teacher.tenant_id, payload.classroom_id, db)
    title = f"{course.title} - {activity.title} 课堂讲评稿"
    return GeneratedDocumentResponse(
        activity_id=activity.id,
        title=title,
        suggested_filename=f"{course.lesson_no.lower()}-activity-{activity.id}-script.md",
        content=_lesson_script_content(course=course, classroom=classroom, activity=activity, db=db),
    )


@router.get("/analytics/publications/{publication_id}", response_model=AnalyticsResponse)
def get_publication_analytics(publication_id: int, db: Session = Depends(get_db)):
    publication = db.get(ActivityPublication, publication_id)
    if not publication:
        raise HTTPException(status_code=404, detail="发布版本不存在。")
    return build_analytics(publication_id, db)


@router.post("/submissions/{submission_id}/reviews", response_model=SubmissionReviewResponse)
def create_teacher_submission_review(
    submission_id: int,
    payload: SubmissionReviewRequest,
    db: Session = Depends(get_db),
):
    teacher, _, _ = _get_teacher(payload.reviewer_user_id, db)
    submission = db.get(WorkSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="作品不存在。")

    activity = db.get(Activity, submission.activity_id)
    course = db.get(Course, activity.course_id) if activity else None
    if not activity or not course or course.tenant_id != teacher.tenant_id:
        raise HTTPException(status_code=404, detail="课程不存在。")

    existing = db.scalar(
        select(SubmissionReview)
        .where(SubmissionReview.submission_id == submission.id)
        .where(SubmissionReview.reviewer_id == teacher.id)
        .limit(1)
    )
    if existing:
        existing.score = payload.score
        existing.comment = payload.comment
        existing.tags_json = payload.tags
        existing.reviewed_at = datetime.now(UTC)
        existing.reviewer_role = "teacher"
        review = existing
    else:
        review = SubmissionReview(
            submission_id=submission.id,
            reviewer_id=teacher.id,
            reviewer_role="teacher",
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
        message="教师点评已保存，作品展示墙和统计分析会自动刷新。",
    )
