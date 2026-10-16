from datetime import timedelta

from extensions import db
from models import Attempt, utcnow


def test_dashboard_shows_upcoming_quiz(api, u1, course):
    d = api.get("/api/user/dashboard", u1).get_json()
    assert d["subjects"] and d["upcoming_quiz"]["id"] == course["quiz"]


def test_past_quiz_is_not_available(api, admin, u1, course, yesterday):
    old = api.post("/api/admin/quizzes", admin, json={
        "chapter_id": course["chapter"], "date_of_quiz": yesterday, "remarks": "Old quiz"}).get_json()["id"]
    assert api.get(f"/api/user/quiz/{old}", u1).status_code == 403


def test_cannot_submit_without_starting(api, u1, course):
    assert api.post(f"/api/user/quiz/{course['quiz']}/submit", u1, json={"user_answers": {}}).status_code == 400


def test_correct_answer_never_reaches_the_browser(api, u1, course):
    r = api.get(f"/api/user/quiz/{course['quiz']}?question_index=0", u1).get_json()
    assert "correct_option" not in r["question"]
    assert r["total_questions"] == 2 and 0 < r["remaining_seconds"] <= 600


def test_question_index_and_payload_validation(api, u1, course):
    qid = course["quiz"]
    assert api.get(f"/api/user/quiz/{qid}?question_index=9", u1).status_code == 400
    assert api.post(f"/api/user/quiz/{qid}/submit", u1, json={"user_answers": [1]}).status_code == 400


def test_submit_scores_and_blocks_retries(api, u1, course):
    qid = course["quiz"]
    api.get(f"/api/user/quiz/{qid}", u1)                                   # starts the attempt
    answers = {str(course["q1"]): 1, str(course["q2"]): 2}                  # one right, one wrong
    r = api.post(f"/api/user/quiz/{qid}/submit", u1, json={"user_answers": answers})
    assert r.status_code == 200 and r.get_json()["score"] == 50.0 and r.get_json()["correct_answers"] == 1
    assert api.post(f"/api/user/quiz/{qid}/submit", u1, json={"user_answers": {}}).status_code == 409
    assert api.get(f"/api/user/quiz/{qid}", u1).status_code == 409          # no re-attempt


def _start_and_make_late(app, api, token, qid):
    assert api.get(f"/api/user/quiz/{qid}", token).status_code == 200
    with app.app_context():
        at = Attempt.query.filter_by(quiz_id=qid).order_by(Attempt.id.desc()).first()
        at.started_at = utcnow() - timedelta(hours=1)
        db.session.commit()


def test_time_limit_is_enforced(app, api, u2, course):
    qid = course["quiz"]
    _start_and_make_late(app, api, u2, qid)
    late = api.post(f"/api/user/quiz/{qid}/submit", u2, json={"user_answers": {str(course["q1"]): 1}})
    assert late.status_code == 403
    assert api.get(f"/api/user/quiz/{qid}", u2).status_code == 409          # a late attempt cannot be retried


def test_history_leaderboard_and_admin_stats(app, api, admin, u1, u2, course):
    qid = course["quiz"]
    api.get(f"/api/user/quiz/{qid}", u1)
    api.post(f"/api/user/quiz/{qid}/submit", u1, json={"user_answers": {str(course["q1"]): 1, str(course["q2"]): 2}})
    _start_and_make_late(app, api, u2, qid)
    api.post(f"/api/user/quiz/{qid}/submit", u2, json={"user_answers": {str(course["q1"]): 1}})

    assert api.get("/api/user/leaderboard", u1).status_code == 200
    assert api.get("/api/user/quiz_stats", u1).status_code == 200
    d = api.get("/api/user/dashboard", u1).get_json()
    assert d["attempted_quizzes"] == [qid] and d["past_attempts"][0]["score"]["total_score"] == 50.0
    s = api.get("/api/admin/stats", admin).get_json()
    assert s["totalAttempts"] == 2 and s["totalUsers"] == 2
