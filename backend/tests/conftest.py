from datetime import datetime, timedelta

import pytest

from app import create_app
from config import TestConfig

HDR = "Authentication-Token"


@pytest.fixture()
def app(tmp_path):
    """A fresh app + in-memory database for every test (full isolation)."""
    app = create_app(TestConfig)
    app.config["EXPORT_DIR"] = str(tmp_path / "exports")  # keep generated files out of the repo
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


class Api:
    """Tiny helper: send requests with the Flask-Security token header."""

    def __init__(self, client):
        self.client = client

    def request(self, method, url, token=None, **kw):
        headers = {HDR: token} if token else {}
        return getattr(self.client, method)(url, headers=headers, **kw)

    def get(self, url, token=None, **kw):
        return self.request("get", url, token, **kw)

    def post(self, url, token=None, **kw):
        return self.request("post", url, token, **kw)

    def put(self, url, token=None, **kw):
        return self.request("put", url, token, **kw)

    def delete(self, url, token=None, **kw):
        return self.request("delete", url, token, **kw)

    def register(self, email, password="password1", **extra):
        body = {"email": email, "password": password, "full_name": "Test User", **extra}
        return self.post("/api/register", json=body)

    def login(self, email, password):
        return self.post("/api/login", json={"email": email, "password": password})

    def token(self, email, password):
        r = self.login(email, password)
        assert r.status_code == 200, r.get_data(as_text=True)
        return r.get_json()["token"]

    def new_user(self, email, password="password1"):
        assert self.register(email, password).status_code == 201
        return self.token(email, password)


@pytest.fixture()
def api(client):
    return Api(client)


@pytest.fixture()
def admin(app, api):
    return api.token(app.config["ADMIN_EMAIL"], app.config["ADMIN_PASSWORD"])


@pytest.fixture()
def u1(api):
    return api.new_user("u1@x.com", "password1")


@pytest.fixture()
def u2(api):
    return api.new_user("u2@x.com", "password2")


@pytest.fixture()
def today():
    return datetime.now().strftime("%Y-%m-%d")


@pytest.fixture()
def yesterday():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


@pytest.fixture()
def course(api, admin, today):
    """Subject -> chapter -> quiz (today, 10 minutes) with two questions."""
    sid = api.post("/api/admin/subjects", admin, json={"name": "Python", "description": "Basics"}).get_json()["id"]
    cid = api.post("/api/admin/chapters", admin, json={"name": "Loops", "subject_id": sid}).get_json()["id"]
    qid = api.post("/api/admin/quizzes", admin, json={
        "chapter_id": cid, "date_of_quiz": today, "remarks": "Loops quiz", "time_duration": "00:10"}).get_json()["id"]
    body = {"quiz_id": qid, "question_statement": "Which keyword starts a loop?",
            "option1": "for", "option2": "if", "option3": "def", "option4": "class", "correct_option": 1}
    q1 = api.post("/api/admin/questions", admin, json=body)
    q2 = api.post("/api/admin/questions", admin, json={
        **body, "question_statement": "Which defines a function?", "correct_option": 3})
    assert q1.status_code == 201 and q2.status_code == 201
    return {"subject": sid, "chapter": cid, "quiz": qid, "q1": q1.get_json()["id"], "q2": q2.get_json()["id"]}
