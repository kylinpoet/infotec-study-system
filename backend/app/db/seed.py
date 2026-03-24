import base64
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.demo_blueprints import TENANT_BLUEPRINTS
from app.db.models import (
    Activity,
    ActivityPublication,
    ActivityRevision,
    AIAgent,
    AssignmentAnswer,
    AssignmentAttempt,
    Classroom,
    Course,
    LiveClassSession,
    PortalAnnouncementRecord,
    PortalConfig,
    PortalSchoolProfile,
    QuestionComponentRegistry,
    SubmissionAsset,
    SubmissionReview,
    StudentProfile,
    TeacherProfile,
    Tenant,
    User,
    WorkSubmission,
)
from app.services.portal_content import (
    DEFAULT_FEATURED_SCHOOL_CODE,
    DEFAULT_HERO_SUBTITLE,
    DEFAULT_HERO_TITLE,
    build_default_announcement_payloads,
)


COURSE_BLUEPRINTS = [
    {
        "title": "开学第一课 信息社会与机房规范",
        "subject": "信息科技",
        "grade_scope": "八年级",
        "term": "2025-2026 下",
        "lesson_no": "L01",
        "activity_title": "机房规范互动任务",
        "published_offset_days": 18,
        "due_offset_days": 12,
        "spec": {
            "title": "机房规范互动任务",
            "instructions": "结合机房课堂规范完成判断与流程排序，系统会自动评分并同步到学生中心。",
            "teacher_tip": "适合在学期初检查学生机房规范、账号纪律和设备操作习惯。",
            "component_whitelist": ["single_choice", "sequence", "hotspot"],
            "questions": [
                {
                    "key": "q1",
                    "type": "single_choice",
                    "stem": "进入机房后最优先完成的动作是什么？",
                    "options": ["打开任意网站", "按座位登录并检查设备", "先和同学聊天", "直接开始提交作业"],
                    "correct_answer": "按座位登录并检查设备",
                    "points": 30,
                },
                {
                    "key": "q2",
                    "type": "sequence",
                    "stem": "请按正确顺序填写机房上课流程。",
                    "options": ["登录设备", "签到", "完成课堂任务", "安全退出"],
                    "correct_answer": ["登录设备", "签到", "完成课堂任务", "安全退出"],
                    "points": 40,
                },
                {
                    "key": "q3",
                    "type": "hotspot",
                    "stem": "截图中哪一类信息最需要注意隐私保护？",
                    "options": ["账号", "壁纸", "时间", "任务名称"],
                    "correct_answer": "账号",
                    "points": 30,
                },
            ],
        },
        "attempts": [
            ("240101", 96, 420, [True, True, True]),
            ("240102", 88, 510, [True, True, False]),
            ("240103", 79, 560, [True, False, True]),
            ("240104", 92, 470, [True, True, True]),
            ("240105", 74, 620, [True, False, False]),
            ("240106", 84, 500, [True, True, False]),
        ],
    },
    {
        "title": "八下第一单元 第2课 走进人工智能",
        "subject": "信息科技",
        "grade_scope": "八年级",
        "term": "2025-2026 下",
        "lesson_no": "L02",
        "activity_title": "人工智能概念认知",
        "published_offset_days": 10,
        "due_offset_days": 6,
        "spec": {
            "title": "人工智能概念认知",
            "instructions": "围绕人工智能的基本概念、应用边界和人工参与完成互动问答。",
            "teacher_tip": "查看学生是否能分清智能应用、算法流程和人工复核责任。",
            "component_whitelist": ["single_choice", "sequence", "hotspot"],
            "questions": [
                {
                    "key": "q1",
                    "type": "single_choice",
                    "stem": "下面哪项更符合人工智能在课堂中的合理定位？",
                    "options": ["完全替代教师", "辅助判断并提供建议", "替学生完成所有任务", "跳过课堂讲解"],
                    "correct_answer": "辅助判断并提供建议",
                    "points": 30,
                },
                {
                    "key": "q2",
                    "type": "sequence",
                    "stem": "请按顺序整理一个 AI 作业从生成到课堂分析的流程。",
                    "options": ["输入目标", "生成作业草案", "教师审核发布", "学生作答分析"],
                    "correct_answer": ["输入目标", "生成作业草案", "教师审核发布", "学生作答分析"],
                    "points": 40,
                },
                {
                    "key": "q3",
                    "type": "hotspot",
                    "stem": "在示例翻译结果中，哪一部分最需要人工重点复核？",
                    "options": ["专业术语", "页面颜色", "文件名", "时间戳"],
                    "correct_answer": "专业术语",
                    "points": 30,
                },
            ],
        },
        "attempts": [
            ("240101", 89, 530, [True, True, False]),
            ("240102", 76, 610, [True, False, False]),
            ("240103", 93, 490, [True, True, True]),
            ("240104", 82, 550, [True, False, True]),
            ("240105", 68, 650, [False, False, True]),
            ("240106", 95, 470, [True, True, True]),
        ],
    },
    {
        "title": "八下第一单元 第3课 人工智能应用",
        "subject": "信息科技",
        "grade_scope": "八年级",
        "term": "2025-2026 下",
        "lesson_no": "L03",
        "activity_title": "AI 交互作业：人工智能应用判断",
        "published_offset_days": 2,
        "due_offset_days": -3,
        "spec": {
            "title": "AI 交互作业：人工智能应用判断",
            "instructions": "请根据课堂内容完成情境判断、流程排序与重点复核题，答题数据将回流教师后台分析。",
            "teacher_tip": "优先关注高错误率情境题，再用课程智能体生成补充练习和讲评提纲。",
            "component_whitelist": ["single_choice", "sequence", "hotspot", "flow_link"],
            "questions": [
                {
                    "key": "q1",
                    "type": "single_choice",
                    "stem": "哪类场景最适合让 AI 先做第一轮处理？",
                    "options": ["旅游说明文翻译", "医学最终诊断", "法律终审裁决", "涉密文件审批"],
                    "correct_answer": "旅游说明文翻译",
                    "points": 30,
                },
                {
                    "key": "q2",
                    "type": "sequence",
                    "stem": "请按正确顺序填写机器翻译工作流程。",
                    "options": ["输入原文", "模型编码", "生成译文", "人工校对"],
                    "correct_answer": ["输入原文", "模型编码", "生成译文", "人工校对"],
                    "points": 40,
                },
                {
                    "key": "q3",
                    "type": "hotspot",
                    "stem": "截图中最需要人工复核的部分是什么？",
                    "options": ["术语", "页码", "背景色", "插图"],
                    "correct_answer": "术语",
                    "points": 30,
                },
            ],
        },
        "attempts": [
            ("240101", 98, 480, [True, True, True]),
            ("240102", 84, 560, [True, False, True]),
            ("240103", 77, 640, [True, False, False]),
            ("240104", 91, 500, [True, True, True]),
            ("240105", 86, 520, [True, True, False]),
            ("240106", 73, 610, [False, True, False]),
        ],
    },
]


STUDENT_BLUEPRINTS = [
    ("240101", "陈安然", 1),
    ("240102", "林浩然", 2),
    ("240103", "苏雨宁", 3),
    ("240104", "周知夏", 4),
    ("240105", "沈嘉禾", 5),
    ("240106", "许知意", 6),
    ("240107", "顾明朗", 7),
    ("240108", "程可心", 8),
]


CLASSROOM_BLUEPRINTS = [
    {
        "school_year": "2025-2026",
        "grade": "八年级",
        "class_no": "1",
        "name": "8.1 班",
        "student_count": len(STUDENT_BLUEPRINTS),
    },
    {
        "school_year": "2025-2026",
        "grade": "八年级",
        "class_no": "2",
        "name": "8.2 班",
        "student_count": 46,
    },
    {
        "school_year": "2025-2026",
        "grade": "七年级",
        "class_no": "3",
        "name": "7.3 班",
        "student_count": 44,
    },
]


def _upsert_tenant(session: Session, blueprint: dict) -> Tenant:
    tenant = session.scalar(select(Tenant).where(Tenant.code == blueprint["code"]))
    if not tenant:
        tenant = Tenant(
            code=blueprint["code"],
            name=blueprint["name"],
            theme_json=blueprint["theme"],
            ai_quota_json={"teacher_monthly_tokens": 2_000_000, "student_daily_hints": 20},
            status="active",
        )
        session.add(tenant)
        session.flush()
    else:
        tenant.name = blueprint["name"]
        tenant.theme_json = blueprint["theme"]
        tenant.status = "active"
    return tenant


def _upsert_user(
    session: Session,
    *,
    tenant_id: int,
    username: str,
    password: str,
    role: str,
    display_name: str,
    avatar: str | None = None,
) -> User:
    user = session.scalar(select(User).where(User.username == username))
    if not user:
        user = User(
            tenant_id=tenant_id,
            username=username,
            password_hash=hash_password(password),
            role=role,
            display_name=display_name,
            avatar=avatar,
            status="active",
        )
        session.add(user)
        session.flush()
    else:
        user.tenant_id = tenant_id
        user.password_hash = hash_password(password)
        user.role = role
        user.display_name = display_name
        user.avatar = avatar
        user.status = "active"
    return user


def _upsert_classroom(
    session: Session,
    *,
    tenant_id: int,
    teacher_id: int,
    school_year: str,
    grade: str,
    class_no: str,
    name: str,
    student_count: int,
) -> Classroom:
    classroom = session.scalar(
        select(Classroom)
        .where(Classroom.tenant_id == tenant_id)
        .where(Classroom.name == name)
    )
    if not classroom:
        classroom = Classroom(
            tenant_id=tenant_id,
            school_year=school_year,
            grade=grade,
            class_no=class_no,
            name=name,
            homeroom_teacher_id=teacher_id,
            student_count=student_count,
        )
        session.add(classroom)
        session.flush()
    else:
        classroom.school_year = school_year
        classroom.grade = grade
        classroom.class_no = class_no
        classroom.name = name
        classroom.homeroom_teacher_id = teacher_id
        classroom.student_count = student_count
    return classroom


def _upsert_teacher_profile(session: Session, *, user_id: int):
    profile = session.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user_id))
    if not profile:
        profile = TeacherProfile(
            user_id=user_id,
            teacher_no="T-001",
            subject="信息科技",
            title="骨干教师",
        )
        session.add(profile)
    else:
        profile.subject = "信息科技"
        profile.title = "骨干教师"


def _upsert_portal_config(session: Session):
    config = session.scalar(select(PortalConfig).order_by(PortalConfig.id.asc()).limit(1))
    if not config:
        config = PortalConfig(
            hero_title=DEFAULT_HERO_TITLE,
            hero_subtitle=DEFAULT_HERO_SUBTITLE,
            featured_school_code=DEFAULT_FEATURED_SCHOOL_CODE,
        )
        session.add(config)
        session.flush()
    else:
        config.hero_title = DEFAULT_HERO_TITLE
        config.hero_subtitle = DEFAULT_HERO_SUBTITLE
        config.featured_school_code = DEFAULT_FEATURED_SCHOOL_CODE
    return config


def _upsert_portal_school_profile(session: Session, *, tenant: Tenant, blueprint: dict):
    profile = session.scalar(
        select(PortalSchoolProfile).where(PortalSchoolProfile.tenant_id == tenant.id).limit(1)
    )
    features = [{"title": title, "description": description} for title, description in blueprint["features"]]
    metrics = [{"title": title, "value": value, "hint": hint} for title, value, hint in blueprint["metrics"]]
    if not profile:
        profile = PortalSchoolProfile(
            tenant_id=tenant.id,
            district=blueprint["district"],
            slogan=blueprint["slogan"],
            grade_scope=blueprint["grade_scope"],
            features_json=features,
            metrics_json=metrics,
        )
        session.add(profile)
        session.flush()
    else:
        profile.district = blueprint["district"]
        profile.slogan = blueprint["slogan"]
        profile.grade_scope = blueprint["grade_scope"]
        profile.features_json = features
        profile.metrics_json = metrics
    return profile


def _upsert_portal_announcement(session: Session, *, payload: dict):
    announcement = session.scalar(
        select(PortalAnnouncementRecord)
        .where(PortalAnnouncementRecord.title == payload["title"])
        .limit(1)
    )
    if not announcement:
        announcement = PortalAnnouncementRecord(**payload)
        session.add(announcement)
        session.flush()
    else:
        announcement.tag = payload["tag"]
        announcement.summary = payload["summary"]
        announcement.published_at = payload["published_at"]
        announcement.display_order = payload["display_order"]
        announcement.is_active = payload["is_active"]
    return announcement


def _upsert_student_profile(
    session: Session,
    *,
    user_id: int,
    student_no: str,
    classroom: Classroom,
    seat_no: int,
) -> StudentProfile:
    profile = session.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    if not profile:
        profile = StudentProfile(
            user_id=user_id,
            student_no=student_no,
            grade="八年级",
            classroom_id=classroom.id,
            classroom_label=classroom.name,
            gender=None,
            seat_no=seat_no,
        )
        session.add(profile)
        session.flush()
    else:
        profile.student_no = student_no
        profile.grade = "八年级"
        profile.classroom_id = classroom.id
        profile.classroom_label = classroom.name
        profile.seat_no = seat_no
    return profile


def _upsert_course(session: Session, *, tenant_id: int, blueprint: dict) -> Course:
    course = session.scalar(
        select(Course)
        .where(Course.tenant_id == tenant_id)
        .where(Course.title == blueprint["title"])
    )
    if not course:
        course = Course(
            tenant_id=tenant_id,
            title=blueprint["title"],
            subject=blueprint["subject"],
            grade_scope=blueprint["grade_scope"],
            term=blueprint["term"],
            lesson_no=blueprint["lesson_no"],
            is_published=True,
        )
        session.add(course)
        session.flush()
    else:
        course.subject = blueprint["subject"]
        course.grade_scope = blueprint["grade_scope"]
        course.term = blueprint["term"]
        course.lesson_no = blueprint["lesson_no"]
        course.is_published = True
    return course


def _upsert_activity(session: Session, *, course_id: int, title: str, activity_type: str = "interactive_assignment") -> Activity:
    activity = session.scalar(
        select(Activity)
        .where(Activity.course_id == course_id)
        .where(Activity.title == title)
    )
    if not activity:
        activity = Activity(
            course_id=course_id,
            title=title,
            type=activity_type,
            latest_revision_id=None,
            rubric_id=None,
            is_published=True,
        )
        session.add(activity)
        session.flush()
    else:
        activity.title = title
        activity.type = activity_type
        activity.is_published = True
    return activity


def _upsert_revision(
    session: Session,
    *,
    activity: Activity,
    spec: dict,
    created_by: int,
    prompt_version: str,
) -> ActivityRevision:
    revision = session.scalar(
        select(ActivityRevision)
        .where(ActivityRevision.activity_id == activity.id)
        .where(ActivityRevision.version_no == 1)
    )
    if not revision:
        revision = ActivityRevision(
            activity_id=activity.id,
            version_no=1,
            schema_version="1.0",
            spec_json=spec,
            render_mode="activity_renderer",
            generated_by_ai=True,
            prompt_version=prompt_version,
            created_by=created_by,
            status="published",
        )
        session.add(revision)
        session.flush()
    else:
        revision.spec_json = spec
        revision.render_mode = "activity_renderer"
        revision.generated_by_ai = True
        revision.prompt_version = prompt_version
        revision.created_by = created_by
        revision.status = "published"
    activity.latest_revision_id = revision.id
    activity.is_published = True
    return revision


def _upsert_publication(
    session: Session,
    *,
    revision_id: int,
    classroom_id: int,
    published_by: int,
    published_at: datetime,
    due_at: datetime,
) -> ActivityPublication:
    publication = session.scalar(
        select(ActivityPublication)
        .where(ActivityPublication.revision_id == revision_id)
        .where(ActivityPublication.classroom_id == classroom_id)
    )
    if not publication:
        publication = ActivityPublication(
            revision_id=revision_id,
            classroom_id=classroom_id,
            published_by=published_by,
            published_at=published_at,
            starts_at=published_at,
            due_at=due_at,
            status="published",
        )
        session.add(publication)
        session.flush()
    else:
        publication.published_by = published_by
        publication.published_at = published_at
        publication.starts_at = published_at
        publication.due_at = due_at
        publication.status = "published"
    return publication


def _data_url(mime_type: str, content: str) -> str:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _guide_spec(course: Course) -> dict:
    return {
        "title": f"{course.title} 导学任务",
        "instructions": "先阅读课程目标、观察任务样例，再确认本节课的作品方向与评价标准。",
        "teacher_tip": "导学任务不计自动分，但会帮助学生在进入交互练习和作品提交前建立任务框架。",
        "stage_label": "活动 1",
        "activity_type": "lesson_guide",
        "deliverable": "阅读导学卡并记录本节课的创作方向。",
        "prompt_starters": [
            "请帮我概括这节课最重要的三个任务目标",
            "如果要做一个班级作品，我应该先准备哪些素材",
        ],
        "component_whitelist": [],
        "questions": [],
    }


def _project_spec(course: Course) -> dict:
    return {
        "title": f"{course.title} 作品提交与互评",
        "instructions": "上传你的数字作品与设计说明，系统会把作品回流到课程目录，支持同伴互评与教师点评。",
        "teacher_tip": "建议先看作品提交热力，再结合互评意见定位展示样例和讲评重点。",
        "stage_label": "活动 3",
        "activity_type": "project_submission",
        "deliverable": "提交至少 1 个图片或文档附件，并附上 80 字左右的设计说明。",
        "accepted_file_types": [
            "image/png",
            "image/jpeg",
            "image/svg+xml",
            "application/pdf",
            "text/plain",
        ],
        "review_enabled": True,
        "rubric_items": ["主题表达", "信息结构", "视觉呈现", "技术实现"],
        "prompt_starters": [
            "帮我检查这份作品说明是否清楚表达了设计思路",
            "请提醒我互评时应该重点看哪些维度",
        ],
        "component_whitelist": [],
        "questions": [],
    }


def _upsert_work_submission(
    session: Session,
    *,
    activity_id: int,
    publication_id: int | None,
    student_id: int,
    headline: str,
    summary: str,
    submitted_at: datetime,
    assets: list[tuple[str, str, str]],
) -> WorkSubmission:
    submission = session.scalar(
        select(WorkSubmission)
        .where(WorkSubmission.activity_id == activity_id)
        .where(WorkSubmission.student_id == student_id)
        .limit(1)
    )
    if not submission:
        submission = WorkSubmission(
            activity_id=activity_id,
            publication_id=publication_id,
            student_id=student_id,
            headline=headline,
            summary=summary,
            status="submitted",
            submitted_at=submitted_at,
            overall_score=None,
        )
        session.add(submission)
        session.flush()
    else:
        submission.publication_id = publication_id
        submission.headline = headline
        submission.summary = summary
        submission.status = "submitted"
        submission.submitted_at = submitted_at

    session.execute(delete(SubmissionAsset).where(SubmissionAsset.submission_id == submission.id))
    for file_name, file_type, file_url in assets:
        media_kind = "image" if file_type.startswith("image/") else "document"
        session.add(
            SubmissionAsset(
                submission_id=submission.id,
                file_name=file_name,
                file_type=file_type,
                media_kind=media_kind,
                file_url=file_url,
                preview_url=file_url if media_kind == "image" else None,
                size_kb=32 if media_kind == "image" else 18,
            )
        )
    return submission


def _upsert_submission_review(
    session: Session,
    *,
    submission_id: int,
    reviewer_id: int,
    reviewer_role: str,
    score: float,
    comment: str,
    reviewed_at: datetime,
    tags: list[str],
):
    review = session.scalar(
        select(SubmissionReview)
        .where(SubmissionReview.submission_id == submission_id)
        .where(SubmissionReview.reviewer_id == reviewer_id)
        .limit(1)
    )
    if not review:
        review = SubmissionReview(
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            score=score,
            comment=comment,
            tags_json=tags,
            reviewed_at=reviewed_at,
        )
        session.add(review)
    else:
        review.reviewer_role = reviewer_role
        review.score = score
        review.comment = comment
        review.tags_json = tags
        review.reviewed_at = reviewed_at


def _wrong_value(question: dict):
    correct_answer = question["correct_answer"]
    if isinstance(correct_answer, list):
        return list(reversed(correct_answer))
    options = question.get("options", [])
    for option in options:
        if option != correct_answer:
            return option
    return "未作答"


def _upsert_attempt(
    session: Session,
    *,
    publication_id: int,
    student_id: int,
    idempotency_key: str,
    started_at: datetime,
    submitted_at: datetime,
    auto_score: float,
    total_time_sec: int,
    spec: dict,
    correctness_pattern: list[bool],
):
    attempt = session.scalar(
        select(AssignmentAttempt)
        .where(AssignmentAttempt.publication_id == publication_id)
        .where(AssignmentAttempt.student_id == student_id)
        .where(AssignmentAttempt.idempotency_key == idempotency_key)
    )
    if not attempt:
        attempt = AssignmentAttempt(
            publication_id=publication_id,
            student_id=student_id,
            status="submitted",
            idempotency_key=idempotency_key,
            started_at=started_at,
            submitted_at=submitted_at,
            auto_score=auto_score,
            teacher_score=None,
            total_time_sec=total_time_sec,
            device_info="lab-desktop-edge",
        )
        session.add(attempt)
        session.flush()
    else:
        attempt.status = "submitted"
        attempt.started_at = started_at
        attempt.submitted_at = submitted_at
        attempt.auto_score = auto_score
        attempt.teacher_score = None
        attempt.total_time_sec = total_time_sec
        attempt.device_info = "lab-desktop-edge"

    session.execute(delete(AssignmentAnswer).where(AssignmentAnswer.attempt_id == attempt.id))
    for question, is_correct in zip(spec["questions"], correctness_pattern, strict=False):
        session.add(
            AssignmentAnswer(
                attempt_id=attempt.id,
                question_key=question["key"],
                answer_json={
                    "value": question["correct_answer"] if is_correct else _wrong_value(question),
                },
                is_correct=is_correct,
                score=float(question["points"] if is_correct else 0),
                feedback="回答正确，已纳入课堂分析。" if is_correct else "该题需要结合讲评继续复习。",
            )
        )


def _upsert_agent(
    session: Session,
    *,
    tenant_id: int,
    scope_type: str,
    scope_id: int,
    role: str,
    name: str,
    system_prompt: str,
):
    agent = session.scalar(
        select(AIAgent)
        .where(AIAgent.tenant_id == tenant_id)
        .where(AIAgent.scope_type == scope_type)
        .where(AIAgent.scope_id == scope_id)
        .where(AIAgent.role == role)
    )
    if not agent:
        agent = AIAgent(
            tenant_id=tenant_id,
            scope_type=scope_type,
            scope_id=scope_id,
            role=role,
            name=name,
            system_prompt=system_prompt,
            status="active",
        )
        session.add(agent)
        session.flush()
    else:
        agent.name = name
        agent.system_prompt = system_prompt
        agent.status = "active"


def _upsert_live_session(
    session: Session,
    *,
    tenant_id: int,
    classroom_id: int,
    course_id: int,
):
    live_session = session.scalar(
        select(LiveClassSession)
        .where(LiveClassSession.classroom_id == classroom_id)
        .order_by(LiveClassSession.id.desc())
        .limit(1)
    )
    if not live_session:
        live_session = LiveClassSession(
            tenant_id=tenant_id,
            classroom_id=classroom_id,
            course_id=course_id,
            status="active",
            view_mode="lab-grid",
            ip_lock_enabled=True,
            class_password_hash=hash_password("8101"),
            signed_in_count=7,
            submitted_count=5,
            pending_review_count=2,
        )
        session.add(live_session)
        session.flush()
    else:
        live_session.tenant_id = tenant_id
        live_session.course_id = course_id
        live_session.status = "active"
        live_session.view_mode = "lab-grid"
        live_session.ip_lock_enabled = True
        live_session.class_password_hash = hash_password("8101")
        live_session.signed_in_count = 7
        live_session.submitted_count = 5
        live_session.pending_review_count = 2


def _upsert_question_component(
    session: Session,
    *,
    component_key: str,
    schema_json: dict,
    renderer_name: str,
    scoring_adapter: str,
):
    registry = session.scalar(
        select(QuestionComponentRegistry).where(QuestionComponentRegistry.component_key == component_key)
    )
    if not registry:
        registry = QuestionComponentRegistry(
            component_key=component_key,
            schema_json=schema_json,
            renderer_name=renderer_name,
            scoring_adapter=scoring_adapter,
            enabled=True,
            tenant_scope="global",
        )
        session.add(registry)
    else:
        registry.schema_json = schema_json
        registry.renderer_name = renderer_name
        registry.scoring_adapter = scoring_adapter
        registry.enabled = True
        registry.tenant_scope = "global"


def seed_database(session: Session):
    now = datetime.now(UTC)

    tenant_by_code = {
        blueprint["code"]: _upsert_tenant(session, blueprint)
        for blueprint in TENANT_BLUEPRINTS
    }
    blueprint_by_code = {blueprint["code"]: blueprint for blueprint in TENANT_BLUEPRINTS}

    _upsert_portal_config(session)
    for tenant in tenant_by_code.values():
        blueprint = blueprint_by_code.get(tenant.code)
        if blueprint:
            _upsert_portal_school_profile(session, tenant=tenant, blueprint=blueprint)
    for payload in build_default_announcement_payloads():
        _upsert_portal_announcement(session, payload=payload)

    demo_tenant = tenant_by_code["xingzhi-school"]
    teacher = _upsert_user(
        session,
        tenant_id=demo_tenant.id,
        username="kylin",
        password="222221",
        role="teacher",
        display_name="Kylin 老师",
        avatar="dragon",
    )
    _upsert_teacher_profile(session, user_id=teacher.id)
    _upsert_user(
        session,
        tenant_id=demo_tenant.id,
        username="portaladmin",
        password="333333",
        role="admin",
        display_name="门户管理员",
        avatar="rooster",
    )

    classrooms = {
        blueprint["name"]: _upsert_classroom(
            session,
            tenant_id=demo_tenant.id,
            teacher_id=teacher.id,
            school_year=blueprint["school_year"],
            grade=blueprint["grade"],
            class_no=blueprint["class_no"],
            name=blueprint["name"],
            student_count=blueprint["student_count"],
        )
        for blueprint in CLASSROOM_BLUEPRINTS
    }
    classroom = classrooms["8.1 班"]

    students_by_no: dict[str, User] = {}
    for student_no, display_name, seat_no in STUDENT_BLUEPRINTS:
        zodiac_key = ["rat", "ox", "tiger", "rabbit", "dragon", "snake", "horse", "goat"][seat_no - 1]
        student = _upsert_user(
            session,
            tenant_id=demo_tenant.id,
            username=student_no,
            password="12345",
            role="student",
            display_name=display_name,
            avatar=zodiac_key,
        )
        _upsert_student_profile(
            session,
            user_id=student.id,
            student_no=student_no,
            classroom=classroom,
            seat_no=seat_no,
        )
        students_by_no[student_no] = student

    for index, blueprint in enumerate(COURSE_BLUEPRINTS):
        course = _upsert_course(session, tenant_id=demo_tenant.id, blueprint=blueprint)
        guide_activity = _upsert_activity(
            session,
            course_id=course.id,
            title=f"{course.title} 导学任务",
            activity_type="lesson_guide",
        )
        guide_revision = _upsert_revision(
            session,
            activity=guide_activity,
            spec=_guide_spec(course),
            created_by=teacher.id,
            prompt_version=f"seed-v3-guide-{course.lesson_no.lower()}",
        )
        guide_activity.latest_revision_id = guide_revision.id
        guide_activity.due_at = now - timedelta(days=max(blueprint["published_offset_days"] - 1, 1))

        interactive_spec = {
            **blueprint["spec"],
            "stage_label": "活动 2",
            "activity_type": "interactive_assignment",
            "deliverable": "完成交互练习并将成绩自动回流到课程看板。",
            "prompt_starters": [
                "帮我分析这份交互练习最容易出错的题型",
                "请根据这节课内容再补 2 个巩固问题",
            ],
        }
        activity = _upsert_activity(
            session,
            course_id=course.id,
            title=blueprint["activity_title"],
            activity_type="interactive_assignment",
        )
        revision = _upsert_revision(
            session,
            activity=activity,
            spec=interactive_spec,
            created_by=teacher.id,
            prompt_version=f"seed-v2-{course.lesson_no.lower()}",
        )
        publication = _upsert_publication(
            session,
            revision_id=revision.id,
            classroom_id=classroom.id,
            published_by=teacher.id,
            published_at=now - timedelta(days=blueprint["published_offset_days"]),
            due_at=now + timedelta(days=blueprint["due_offset_days"]),
        )
        activity.due_at = publication.due_at

        for attempt_index, (student_no, auto_score, total_time_sec, correctness_pattern) in enumerate(blueprint["attempts"], start=1):
            student = students_by_no[student_no]
            submitted_at = publication.published_at + timedelta(hours=attempt_index + index)
            started_at = submitted_at - timedelta(minutes=max(total_time_sec // 60, 5))
            _upsert_attempt(
                session,
                publication_id=publication.id,
                student_id=student.id,
                idempotency_key=f"{course.lesson_no.lower()}-{student_no}",
                started_at=started_at,
                submitted_at=submitted_at,
                auto_score=auto_score,
                total_time_sec=total_time_sec,
                spec=interactive_spec,
                correctness_pattern=correctness_pattern,
            )

        project_activity = _upsert_activity(
            session,
            course_id=course.id,
            title=f"{course.title} 作品提交与互评",
            activity_type="project_submission",
        )
        project_revision = _upsert_revision(
            session,
            activity=project_activity,
            spec=_project_spec(course),
            created_by=teacher.id,
            prompt_version=f"seed-v3-project-{course.lesson_no.lower()}",
        )
        project_publication = _upsert_publication(
            session,
            revision_id=project_revision.id,
            classroom_id=classroom.id,
            published_by=teacher.id,
            published_at=publication.published_at + timedelta(days=2),
            due_at=publication.due_at + timedelta(days=5),
        )
        project_activity.due_at = project_publication.due_at

        submission_blueprints = [
            (
                "240101",
                "智慧校园提示海报",
                "我把课堂里关于 AI 使用边界的要点整理成一张海报，并附了设计说明。",
                [
                    (
                        f"{course.lesson_no.lower()}-poster.svg",
                        "image/svg+xml",
                        _data_url(
                            "image/svg+xml",
                            f"<svg xmlns='http://www.w3.org/2000/svg' width='960' height='720'>"
                            f"<rect width='100%' height='100%' fill='#E8F0FF'/>"
                            f"<rect x='48' y='48' width='864' height='624' rx='36' fill='#FFFFFF' stroke='#2F6FED' stroke-width='8'/>"
                            f"<text x='90' y='150' font-size='58' fill='#1E3A5F'>课程 {course.lesson_no}</text>"
                            f"<text x='90' y='250' font-size='42' fill='#2F6FED'>信息科技作品海报</text>"
                            f"<text x='90' y='350' font-size='28' fill='#334155'>1. 先理解场景  2. 再设计交互  3. 最后复核输出</text>"
                            f"<text x='90' y='420' font-size='28' fill='#0F766E'>AI 负责辅助生成，人负责判断与表达。</text>"
                            f"</svg>",
                        ),
                    ),
                    (
                        f"{course.lesson_no.lower()}-design-note.txt",
                        "text/plain",
                        _data_url("text/plain", f"{course.title} 设计说明：我希望用图文结合的方式呈现课程重点，并让同学一眼看到任务顺序。"),
                    ),
                ],
                [
                    ("240102", "student", 91, "结构很清楚，海报和说明文能互相支撑。", ["结构清楚", "表达完整"]),
                    ("kylin", "teacher", 95, "适合作为课堂展示样例，后续可再增强配色层次。", ["可展示", "可迭代"]),
                ],
            ),
            (
                "240103",
                "智能翻译流程卡",
                "我把从输入原文到人工校对的流程做成了卡片，方便在课程目录里展示。",
                [
                    (
                        f"{course.lesson_no.lower()}-flow.svg",
                        "image/svg+xml",
                        _data_url(
                            "image/svg+xml",
                            "<svg xmlns='http://www.w3.org/2000/svg' width='960' height='720'>"
                            "<rect width='100%' height='100%' fill='#F6FFFB'/>"
                            "<rect x='60' y='90' width='220' height='100' rx='24' fill='#14B8A6'/>"
                            "<rect x='360' y='90' width='220' height='100' rx='24' fill='#2F6FED'/>"
                            "<rect x='660' y='90' width='220' height='100' rx='24' fill='#F59E0B'/>"
                            "<text x='110' y='150' font-size='30' fill='#fff'>输入原文</text>"
                            "<text x='395' y='150' font-size='30' fill='#fff'>模型生成</text>"
                            "<text x='680' y='150' font-size='30' fill='#fff'>人工复核</text>"
                            "<path d='M285 140 H350' stroke='#0F172A' stroke-width='10'/>"
                            "<path d='M585 140 H650' stroke='#0F172A' stroke-width='10'/>"
                            "</svg>",
                        ),
                    ),
                    (
                        f"{course.lesson_no.lower()}-rubric.txt",
                        "text/plain",
                        _data_url("text/plain", "互评提示：请从主题表达、信息结构、视觉呈现、技术实现四个维度分别观察。"),
                    ),
                ],
                [
                    ("240104", "student", 88, "流程卡一眼就能看懂，如果再补一点应用场景会更完整。", ["逻辑清楚", "可补场景"]),
                    ("kylin", "teacher", 93, "流程信息准确，适合放到课堂大屏讲评。", ["逻辑准确", "适合讲评"]),
                ],
            ),
            (
                "240105",
                "机房规范提醒单",
                "我把机房登录、签到、提交和退出流程做成了规范提醒单，准备给小组展示。",
                [
                    (
                        f"{course.lesson_no.lower()}-notice.svg",
                        "image/svg+xml",
                        _data_url(
                            "image/svg+xml",
                            "<svg xmlns='http://www.w3.org/2000/svg' width='960' height='720'>"
                            "<rect width='100%' height='100%' fill='#FFF8EB'/>"
                            "<rect x='100' y='100' width='760' height='520' rx='32' fill='#FFFFFF' stroke='#F59E0B' stroke-width='8'/>"
                            "<text x='160' y='200' font-size='52' fill='#B45309'>机房规范提醒单</text>"
                            "<text x='160' y='310' font-size='30' fill='#334155'>登录设备 -> 课堂签到 -> 完成任务 -> 安全退出</text>"
                            "<text x='160' y='390' font-size='28' fill='#0F766E'>重点提醒：保护账号信息，不替同学操作设备。</text>"
                            "</svg>",
                        ),
                    ),
                ],
                [
                    ("240106", "student", 86, "提醒点完整，适合给低年级同学做示范。", ["适合展示", "规范完整"]),
                    ("kylin", "teacher", 90, "如果再加入图标和分栏，门户展示效果会更好。", ["表达完整", "建议优化"]),
                ],
            ),
        ]

        for submission_index, (student_no, headline, summary, assets, reviews) in enumerate(submission_blueprints, start=1):
            student = students_by_no[student_no]
            submission = _upsert_work_submission(
                session,
                activity_id=project_activity.id,
                publication_id=project_publication.id,
                student_id=student.id,
                headline=headline,
                summary=summary,
                submitted_at=project_publication.published_at + timedelta(hours=submission_index + index),
                assets=assets,
            )
            for review_index, (reviewer_no, reviewer_role, score, comment, tags) in enumerate(reviews, start=1):
                reviewer = teacher if reviewer_no == "kylin" else students_by_no[reviewer_no]
                _upsert_submission_review(
                    session,
                    submission_id=submission.id,
                    reviewer_id=reviewer.id,
                    reviewer_role=reviewer_role,
                    score=score,
                    comment=comment,
                    reviewed_at=submission.submitted_at + timedelta(hours=review_index),
                    tags=tags,
                )

        _upsert_agent(
            session,
            tenant_id=demo_tenant.id,
            scope_type="course",
            scope_id=course.id,
            role="课程助教",
            name=f"{course.title} 课程智能体",
            system_prompt=f"围绕课程《{course.title}》提供备课辅助、作业讲评与资源检索建议。",
        )
        _upsert_agent(
            session,
            tenant_id=demo_tenant.id,
            scope_type="course",
            scope_id=course.id,
            role="学生答疑助手",
            name=f"{course.title} 学生答疑助手",
            system_prompt="默认采用启发式提示、反问和纠错，不直接输出标准答案。",
        )

    active_course_titles = {blueprint["title"] for blueprint in COURSE_BLUEPRINTS}
    for course in session.scalars(select(Course).where(Course.tenant_id == demo_tenant.id)).all():
        if course.title not in active_course_titles:
            course.is_published = False

    _upsert_agent(
        session,
        tenant_id=demo_tenant.id,
        scope_type="tenant",
        scope_id=demo_tenant.id,
        role="通用教学助手",
        name="信息科技通用智能体",
        system_prompt="服务于整个平台的教师与学生，负责提供导航、备课建议和平台使用说明。",
    )

    _upsert_live_session(
        session,
        tenant_id=demo_tenant.id,
        classroom_id=classroom.id,
        course_id=session.scalar(
            select(Course.id)
            .where(Course.tenant_id == demo_tenant.id)
            .where(Course.lesson_no == "L03")
        ),
    )

    _upsert_question_component(
        session,
        component_key="single_choice",
        schema_json={"options": "string[]", "correct_answer": "string"},
        renderer_name="SingleChoiceRenderer",
        scoring_adapter="ExactChoiceScorer",
    )
    _upsert_question_component(
        session,
        component_key="sequence",
        schema_json={"options": "string[]", "correct_answer": "string[]"},
        renderer_name="SequenceRenderer",
        scoring_adapter="SequenceScorer",
    )
    _upsert_question_component(
        session,
        component_key="hotspot",
        schema_json={"options": "string[]", "correct_answer": "string"},
        renderer_name="HotspotRenderer",
        scoring_adapter="KeywordMatchScorer",
    )
    _upsert_question_component(
        session,
        component_key="flow_link",
        schema_json={"nodes": "string[]", "correct_answer": "string[]"},
        renderer_name="FlowLinkRenderer",
        scoring_adapter="SequenceScorer",
    )

    session.commit()
