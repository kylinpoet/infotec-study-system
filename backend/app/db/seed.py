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
    QuestionComponentRegistry,
    SubmissionAsset,
    SubmissionReview,
    StudentProfile,
    TeacherProfile,
    Tenant,
    User,
    WorkSubmission,
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
) -> User:
    user = session.scalar(select(User).where(User.username == username))
    if not user:
        user = User(
            tenant_id=tenant_id,
            username=username,
            password_hash=hash_password(password),
            role=role,
            display_name=display_name,
            status="active",
        )
        session.add(user)
        session.flush()
    else:
        user.tenant_id = tenant_id
        user.password_hash = hash_password(password)
        user.role = role
        user.display_name = display_name
        user.status = "active"
    return user


def _upsert_classroom(session: Session, *, tenant_id: int, teacher_id: int) -> Classroom:
    classroom = session.scalar(
        select(Classroom)
        .where(Classroom.tenant_id == tenant_id)
        .where(Classroom.name == "8.1 班")
    )
    if not classroom:
        classroom = Classroom(
            tenant_id=tenant_id,
            school_year="2025-2026",
            grade="八年级",
            class_no="1",
            name="8.1 班",
            homeroom_teacher_id=teacher_id,
            student_count=len(STUDENT_BLUEPRINTS),
        )
        session.add(classroom)
        session.flush()
    else:
        classroom.homeroom_teacher_id = teacher_id
        classroom.student_count = len(STUDENT_BLUEPRINTS)
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

    demo_tenant = tenant_by_code["xingzhi-school"]
    teacher = _upsert_user(
        session,
        tenant_id=demo_tenant.id,
        username="kylin",
        password="222221",
        role="teacher",
        display_name="Kylin 老师",
    )
    _upsert_teacher_profile(session, user_id=teacher.id)

    classroom = _upsert_classroom(session, tenant_id=demo_tenant.id, teacher_id=teacher.id)

    students_by_no: dict[str, User] = {}
    for student_no, display_name, seat_no in STUDENT_BLUEPRINTS:
        student = _upsert_user(
            session,
            tenant_id=demo_tenant.id,
            username=student_no,
            password="12345",
            role="student",
            display_name=display_name,
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
        activity = _upsert_activity(session, course_id=course.id, title=blueprint["activity_title"])
        revision = _upsert_revision(
            session,
            activity=activity,
            spec=blueprint["spec"],
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
                spec=blueprint["spec"],
                correctness_pattern=correctness_pattern,
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
