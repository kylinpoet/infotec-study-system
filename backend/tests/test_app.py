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
