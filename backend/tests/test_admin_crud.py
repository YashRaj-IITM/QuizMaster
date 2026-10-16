def test_subject_crud_and_validation(api, admin):
    assert api.post("/api/admin/subjects", admin, json={}).status_code == 400
    sid = api.post("/api/admin/subjects", admin, json={"name": "Python", "description": "Basics"}).get_json()["id"]
    assert api.post("/api/admin/subjects", admin, json={"name": "python"}).status_code == 409   # unique, case-insensitive
    assert api.put(f"/api/admin/subjects/{sid}", admin, json={"name": "Python 3"}).status_code == 200
    assert api.get("/api/admin/subjects?q=pyth", admin).status_code == 200
    assert api.delete(f"/api/admin/subjects/{sid}", admin).status_code == 200
    assert api.delete(f"/api/admin/subjects/{sid}", admin).status_code == 404


def test_chapter_needs_real_subject_and_can_be_updated(api, admin, course):
    assert api.post("/api/admin/chapters", admin, json={"name": "Loops", "subject_id": 999}).status_code == 404
    r = api.put(f"/api/admin/chapters/{course['chapter']}", admin, json={"name": "Loops & Iteration"})
    assert r.status_code == 200
    # A chapter name must remain unique within its subject on update as well.
    duplicate = api.post("/api/admin/chapters", admin, json={
        "name": "Existing", "subject_id": course["subject"]
    }).get_json()["id"]
    assert api.put(f"/api/admin/chapters/{course['chapter']}", admin, json={"name": "Existing"}).status_code == 409
    assert api.delete(f"/api/admin/chapters/{duplicate}", admin).status_code == 200


def test_quiz_validation_and_update(api, admin, course, today):
    cid = course["chapter"]
    bad_date = {"chapter_id": cid, "date_of_quiz": "31/12/2026", "remarks": "x"}
    bad_duration = {"chapter_id": cid, "date_of_quiz": today, "remarks": "x", "time_duration": "abc"}
    assert api.post("/api/admin/quizzes", admin, json=bad_date).status_code == 400
    assert api.post("/api/admin/quizzes", admin, json=bad_duration).status_code == 400
    assert api.put(f"/api/admin/quizzes/{course['quiz']}", admin, json={"remarks": "Loops quiz v2"}).status_code == 200


def test_question_validation_and_crud(api, admin, course):
    body = {"quiz_id": course["quiz"], "question_statement": "Pick one", "option1": "for", "option2": "if",
            "option3": "def", "option4": "class", "correct_option": 1}
    assert api.post("/api/admin/questions", admin, json={**body, "correct_option": 5}).status_code == 400
    assert api.post("/api/admin/questions", admin, json={**body, "option2": "for"}).status_code == 400  # duplicate options
    assert api.put(f"/api/admin/questions/{course['q2']}", admin, json={"option1": "while"}).status_code == 200
    # Partial updates must not create duplicate options against unchanged fields.
    assert api.put(f"/api/admin/questions/{course['q2']}", admin, json={"option1": "if"}).status_code == 400
    assert len(api.get(f"/api/admin/questions?quiz_id={course['quiz']}", admin).get_json()) >= 2
    assert api.delete(f"/api/admin/questions/{course['q2']}", admin).status_code == 200


def test_admin_lists_users(api, admin, u1):
    assert api.get("/api/admin/users", admin).status_code == 200


def test_deleting_a_subject_cascades(api, admin, u1, course):
    assert api.delete(f"/api/admin/subjects/{course['subject']}", admin).status_code == 200
    assert api.get(f"/api/user/quiz/{course['quiz']}", u1).status_code == 404
