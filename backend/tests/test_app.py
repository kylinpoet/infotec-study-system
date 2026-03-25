def test_health():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_demo_login():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "kylin", "password": "222221"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["user"]["role"] == "teacher"
        assert payload["access_token"].startswith("demo-session-")


def test_portal_supports_multi_school():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/api/v1/public/portal")
        assert response.status_code == 200
        payload = response.json()
        assert payload["featured_school_code"] == "xingzhi-school"
        assert len(payload["schools"]) >= 3
        assert all("features" in school for school in payload["schools"])


def test_teacher_and_student_dashboards_match_new_information_architecture():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        teacher = client.get("/api/v1/teacher/dashboard/1")
        assert teacher.status_code == 200
        teacher_payload = teacher.json()
        assert teacher_payload["lab_snapshot"]["classroom_label"] == "8.1 班"
        assert len(teacher_payload["course_directory"]) >= 3
        assert len(teacher_payload["classroom_options"]) >= 3
        assert teacher_payload["general_assistant"]["title"] == "通用智能体"

        student = client.get("/api/v1/student/dashboard/2")
        assert student.status_code == 200
        student_payload = student.json()
        assert student_payload["total_score"] > 0
        assert len(student_payload["course_directory"]) >= 3
        assert student_payload["general_assistant"]["title"] == "通用智能体"


def test_student_course_activity_flow_supports_submission_and_review():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "240101", "password": "12345", "school_code": "xingzhi-school"},
        )
        assert login.status_code == 200
        student_id = login.json()["user"]["id"]
        dashboard = client.get(f"/api/v1/student/dashboard/{student_id}")
        assert dashboard.status_code == 200
        course_id = dashboard.json()["course_directory"][0]["id"]

        detail = client.get(f"/api/v1/student/courses/{course_id}?user_id={student_id}")
        assert detail.status_code == 200
        payload = detail.json()
        assert payload["activities"]

        project_activity = next(activity for activity in payload["activities"] if activity["accepted_file_types"])
        submission = client.post(
            f"/api/v1/student/activities/{project_activity['id']}/submissions",
            json={
                "student_user_id": student_id,
                "headline": "测试作品",
                "summary": "用于验证作品提交流程。",
                "assets": [
                    {
                        "file_name": "demo.txt",
                        "file_type": "text/plain",
                        "data_url": "data:text/plain;base64,5rWL6K+V5L2c5ZOB",
                    }
                ],
            },
        )
        assert submission.status_code == 200
        assert submission.json()["submission"]["assets"][0]["file_name"] == "demo.txt"

        other_student_login = client.post(
            "/api/v1/auth/login",
            json={"username": "240102", "password": "12345", "school_code": "xingzhi-school"},
        )
        assert other_student_login.status_code == 200
        other_student_id = other_student_login.json()["user"]["id"]
        other_submission = client.post(
            f"/api/v1/student/activities/{project_activity['id']}/submissions",
            json={
                "student_user_id": other_student_id,
                "headline": "同伴互评目标作品",
                "summary": "用于验证学生互评接口。",
                "assets": [
                    {
                        "file_name": "peer-review.txt",
                        "file_type": "text/plain",
                        "data_url": "data:text/plain;base64,5ZCM5Ly05LqS6K+E55uu5qCH5L2c5ZOB",
                    }
                ],
            },
        )
        assert other_submission.status_code == 200
        review_target = other_submission.json()["submission"]["id"]
        review = client.post(
            f"/api/v1/student/submissions/{review_target}/reviews",
            json={
                "reviewer_user_id": student_id,
                "score": 92,
                "comment": "结构清楚，说明也比较完整。",
                "tags": ["主题表达", "信息结构"],
            },
        )
        assert review.status_code == 200
        assert review.json()["review"]["score"] == 92


def test_teacher_can_review_course_submission():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        teacher_login = client.post(
            "/api/v1/auth/login",
            json={"username": "kylin", "password": "222221", "school_code": "xingzhi-school"},
        )
        assert teacher_login.status_code == 200
        teacher_id = teacher_login.json()["user"]["id"]

        student_login = client.post(
            "/api/v1/auth/login",
            json={"username": "240101", "password": "12345", "school_code": "xingzhi-school"},
        )
        assert student_login.status_code == 200
        student_id = student_login.json()["user"]["id"]

        dashboard = client.get(f"/api/v1/student/dashboard/{student_id}")
        course_id = dashboard.json()["course_directory"][0]["id"]
        detail = client.get(f"/api/v1/student/courses/{course_id}?user_id={student_id}")
        project_activity = next(activity for activity in detail.json()["activities"] if activity["accepted_file_types"])
        submission = client.post(
            f"/api/v1/student/activities/{project_activity['id']}/submissions",
            json={
                "student_user_id": student_id,
                "headline": "教师点评测试作品",
                "summary": "用于验证教师点评接口。",
                "assets": [
                    {
                        "file_name": "teacher-review.txt",
                        "file_type": "text/plain",
                        "data_url": "data:text/plain;base64,5pWZ5biI54K56K+V5L2c5ZOB",
                    }
                ],
            },
        )
        assert submission.status_code == 200
        target_submission_id = submission.json()["submission"]["id"]

        teacher_review = client.post(
            f"/api/v1/teacher/submissions/{target_submission_id}/reviews",
            json={
                "reviewer_user_id": teacher_id,
                "score": 96,
                "comment": "教师点评：结构完整，适合作为课堂展示案例。",
                "tags": ["结构清楚", "适合展示"],
            },
        )
        assert teacher_review.status_code == 200
        assert teacher_review.json()["review"]["reviewer_role"] == "teacher"
        assert teacher_review.json()["review"]["score"] == 96


def test_teacher_can_start_class_for_selected_classroom_and_generate_documents():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        teacher_login = client.post(
            "/api/v1/auth/login",
            json={"username": "kylin", "password": "222221", "school_code": "xingzhi-school"},
        )
        assert teacher_login.status_code == 200
        teacher_id = teacher_login.json()["user"]["id"]

        dashboard = client.get(f"/api/v1/teacher/dashboard/{teacher_id}")
        assert dashboard.status_code == 200
        dashboard_payload = dashboard.json()
        assert len(dashboard_payload["classroom_options"]) >= 3

        primary_classroom_id = dashboard_payload["classroom_options"][0]["id"]
        target_classroom = dashboard_payload["classroom_options"][1]
        course_id = dashboard_payload["course_directory"][0]["id"]

        start_class = client.post(
            "/api/v1/teacher/live-sessions/start",
            json={
                "teacher_user_id": teacher_id,
                "classroom_id": target_classroom["id"],
                "course_id": course_id,
                "view_mode": "activity-focus",
                "ip_lock_enabled": False,
                "class_password": "8202",
            },
        )
        assert start_class.status_code == 200
        start_payload = start_class.json()
        assert start_payload["session"]["classroom_id"] == target_classroom["id"]
        assert start_payload["session"]["course_id"] == course_id
        assert start_payload["session"]["view_mode"] == "activity-focus"
        assert start_payload["session"]["ip_lock_enabled"] is False

        selected_dashboard = client.get(
            f"/api/v1/teacher/dashboard/{teacher_id}?classroom_id={target_classroom['id']}"
        )
        assert selected_dashboard.status_code == 200
        selected_payload = selected_dashboard.json()
        assert selected_payload["current_classroom_id"] == target_classroom["id"]
        assert selected_payload["active_session"]["course_id"] == course_id
        assert selected_payload["classroom_label"] == target_classroom["name"]

        detail = client.get(f"/api/v1/teacher/courses/{course_id}?classroom_id={primary_classroom_id}")
        assert detail.status_code == 200
        activity_id = detail.json()["activities"][0]["id"]

        briefing = client.post(
            f"/api/v1/teacher/activities/{activity_id}/briefing-summary",
            json={"teacher_user_id": teacher_id, "classroom_id": primary_classroom_id},
        )
        assert briefing.status_code == 200
        briefing_payload = briefing.json()
        assert briefing_payload["title"].endswith("讲评摘要")
        assert "教师讲评重点" in briefing_payload["content"]

        lesson_script = client.post(
            f"/api/v1/teacher/activities/{activity_id}/lesson-script",
            json={"teacher_user_id": teacher_id, "classroom_id": primary_classroom_id},
        )
        assert lesson_script.status_code == 200
        lesson_payload = lesson_script.json()
        assert lesson_payload["title"].endswith("课堂讲评稿")
        assert "展示优秀作品" in lesson_payload["content"]


def test_student_settings_support_zodiac_agent_selection():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "240101", "password": "12345", "school_code": "xingzhi-school"},
        )
        assert login.status_code == 200
        student = login.json()["user"]
        assert student["avatar"]

        settings = client.get(f"/api/v1/settings/student/{student['id']}")
        assert settings.status_code == 200
        settings_payload = settings.json()
        assert len(settings_payload["zodiac_options"]) == 12

        update = client.put(
            "/api/v1/settings/student",
            json={"user_id": student["id"], "display_name": "陈安然同学", "avatar": "rabbit"},
        )
        assert update.status_code == 200
        update_payload = update.json()
        assert update_payload["user"]["display_name"] == "陈安然同学"
        assert update_payload["user"]["avatar"] == "rabbit"


def test_portal_admin_can_manage_portal_content():
    from fastapi.testclient import TestClient

    from app.main import app
    from app.db.models import LLMProviderConfig
    from app.db.session import session_scope

    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "portaladmin", "password": "333333", "school_code": "xingzhi-school"},
        )
        assert login.status_code == 200
        admin = login.json()["user"]
        assert admin["role"] == "admin"

        dashboard = client.get(f"/api/v1/admin/portal/dashboard/{admin['id']}")
        assert dashboard.status_code == 200
        dashboard_payload = dashboard.json()
        assert len(dashboard_payload["schools"]) >= 3
        assert dashboard_payload["hero"]["featured_school_code"] == "xingzhi-school"
        assert dashboard_payload["llm_config"]["model_name"]
        assert isinstance(dashboard_payload["llm_config"]["model_options"], list)

        hero_update = client.put(
            "/api/v1/admin/portal/hero",
            json={
                "admin_user_id": admin["id"],
                "hero_title": "信息科技课程新门户",
                "hero_subtitle": "统一管理学校特色、公告与主题风格。",
                "featured_school_code": "haitang-school",
            },
        )
        assert hero_update.status_code == 200
        assert hero_update.json()["featured_school_code"] == "haitang-school"

        school_update = client.put(
            "/api/v1/admin/portal/schools/xingzhi-school",
            json={
                "admin_user_id": admin["id"],
                "name": "行知信息科技实验学校",
                "district": "浦东新区",
                "slogan": "新的门户标语",
                "grade_scope": "小学高段 - 初中",
                "theme": {"primary": "#2357D9", "secondary": "#19B59C", "accent": "#E99A20"},
                "features": [{"title": "智能门户", "description": "支持统一维护学校特色资料。"}],
                "metrics": [{"title": "课程目录", "value": "40", "hint": "门户首页显示最新课程规模"}],
            },
        )
        assert school_update.status_code == 200

        llm_update = client.put(
            "/api/v1/admin/llm/config",
            json={
                "admin_user_id": admin["id"],
                "provider_name": "OpenAI Compatible",
                "base_url": "https://llm.example.com/v1",
                "api_key": "sk-test-admin-12345678",
                "clear_api_key": False,
                "model_name": "deepseek-chat",
                "temperature": 0.5,
                "max_tokens": 8192,
                "is_enabled": True,
                "notes": "用于课程活动生成与讲评文档输出。",
            },
        )
        assert llm_update.status_code == 200
        llm_payload = llm_update.json()
        assert llm_payload["base_url"] == "https://llm.example.com/v1"
        assert llm_payload["model_name"] == "deepseek-chat"
        assert llm_payload["has_api_key"] is True
        assert llm_payload["api_key_masked"]

        with session_scope() as session:
            stored = session.query(LLMProviderConfig).filter(LLMProviderConfig.scope == "platform").one()
            assert stored.api_key != "sk-test-admin-12345678"
            assert stored.api_key.startswith("enc:")

        announcement_create = client.post(
            "/api/v1/admin/portal/announcements",
            json={
                "admin_user_id": admin["id"],
                "title": "门户后台已上线",
                "tag": "后台更新",
                "summary": "支持多校学校资料与公告统一管理。",
                "published_at": "2026-03-24T09:00:00",
                "is_active": True,
            },
        )
        assert announcement_create.status_code == 200
        assert announcement_create.json()["title"] == "门户后台已上线"


def test_llm_config_rejects_enabled_state_without_api_key():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "portaladmin", "password": "333333", "school_code": "xingzhi-school"},
        )
        assert login.status_code == 200
        admin = login.json()["user"]

        clear_key = client.put(
            "/api/v1/admin/llm/config",
            json={
                "admin_user_id": admin["id"],
                "provider_name": "OpenAI Compatible",
                "base_url": "https://api.openai.com/v1",
                "api_key": None,
                "clear_api_key": True,
                "model_name": "gpt-4.1-mini",
                "temperature": 0.4,
                "max_tokens": 4096,
                "is_enabled": False,
                "notes": "clear key first",
            },
        )
        assert clear_key.status_code == 200

        invalid_enable = client.put(
            "/api/v1/admin/llm/config",
            json={
                "admin_user_id": admin["id"],
                "provider_name": "OpenAI Compatible",
                "base_url": "https://api.openai.com/v1",
                "api_key": None,
                "clear_api_key": False,
                "model_name": "gpt-4.1-mini",
                "temperature": 0.4,
                "max_tokens": 4096,
                "is_enabled": True,
                "notes": "should fail",
            },
        )
        assert invalid_enable.status_code == 422


def test_school_application_review_and_school_admin_management():
    import uuid

    from fastapi.testclient import TestClient

    from app.main import app

    unique_suffix = uuid.uuid4().hex[:8]
    school_code = f"test-{unique_suffix}"
    admin_username = f"admin-{unique_suffix}"
    teacher_username = f"teacher-{unique_suffix}"

    with TestClient(app) as client:
        application = client.post(
            "/api/v1/public/school-applications",
            json={
                "school_name": "测试未来学校",
                "school_code": school_code,
                "district": "浦东新区",
                "grade_scope": "小学 - 初中",
                "slogan": "用于验证学校申请审核与学校后台。",
                "contact_name": "李老师",
                "contact_phone": "13800000000",
                "applicant_display_name": "测试校管",
                "applicant_username": admin_username,
                "applicant_password": "555555",
                "note": "请开通学校管理员后台。",
            },
        )
        assert application.status_code == 200
        application_payload = application.json()
        assert application_payload["application"]["status"] == "pending"

        platform_login = client.post(
            "/api/v1/auth/login",
            json={"username": "portaladmin", "password": "333333", "school_code": "xingzhi-school"},
        )
        assert platform_login.status_code == 200
        platform_admin = platform_login.json()["user"]

        dashboard = client.get(f"/api/v1/admin/portal/dashboard/{platform_admin['id']}")
        assert dashboard.status_code == 200
        dashboard_payload = dashboard.json()
        target_application = next(
            item for item in dashboard_payload["school_applications"] if item["school_code"] == school_code
        )
        assert target_application["status"] == "pending"

        approval = client.post(
            f"/api/v1/admin/portal/school-applications/{target_application['id']}/review",
            json={
                "admin_user_id": platform_admin["id"],
                "decision": "approve",
                "review_note": "资料完整，开通学校后台。",
            },
        )
        assert approval.status_code == 200
        assert approval.json()["status"] == "approved"
        assert approval.json()["approved_tenant_id"] is not None

        portal = client.get("/api/v1/public/portal")
        assert portal.status_code == 200
        assert any(item["code"] == school_code for item in portal.json()["schools"])

        school_admin_login = client.post(
            "/api/v1/auth/login",
            json={"username": admin_username, "password": "555555", "school_code": school_code},
        )
        assert school_admin_login.status_code == 200
        school_admin = school_admin_login.json()["user"]
        assert school_admin["role"] == "school_admin"

        school_admin_dashboard = client.get(f"/api/v1/school-admin/dashboard/{school_admin['id']}")
        assert school_admin_dashboard.status_code == 200
        school_dashboard_payload = school_admin_dashboard.json()
        assert school_dashboard_payload["school"]["code"] == school_code
        assert len(school_dashboard_payload["staff_members"]) == 1

        create_teacher = client.post(
            "/api/v1/school-admin/staff",
            json={
                "admin_user_id": school_admin["id"],
                "username": teacher_username,
                "password": "666666",
                "display_name": "新教师",
                "subject": "信息科技",
                "title": "教研组长",
                "teacher_no": "T-900",
            },
        )
        assert create_teacher.status_code == 200
        created_teacher = create_teacher.json()["staff_member"]
        assert created_teacher["role"] == "teacher"
        assert created_teacher["teacher_no"] == "T-900"

        promote_teacher = client.put(
            f"/api/v1/school-admin/staff/{created_teacher['id']}/role",
            json={"admin_user_id": school_admin["id"], "role": "school_admin"},
        )
        assert promote_teacher.status_code == 200
        assert promote_teacher.json()["staff_member"]["role"] == "school_admin"
