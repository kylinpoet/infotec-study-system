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
