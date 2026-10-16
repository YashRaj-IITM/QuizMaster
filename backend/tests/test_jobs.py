"""Background jobs. Celery runs eagerly in tests, so no Redis or SMTP server is needed."""
import os
from datetime import datetime, timedelta, timezone

import tasks

PAST = "2000-01-01T00:00:00"


def _future():
    return (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)).isoformat()


def test_user_reminder_must_be_in_the_future(api, u1):
    assert api.post("/api/user/schedule_reminder", u1, json={"reminder_time": PAST}).status_code == 400
    assert api.post("/api/user/schedule_reminder", u1, json={"reminder_time": _future()}).status_code == 200


def test_reminder_endpoint_requires_login(api):
    assert api.post("/api/user/schedule_reminder", json={"reminder_time": _future()}).status_code == 401


def test_csv_export_is_private_to_its_owner(api, u1, u2):
    r = api.post("/api/user/export", u1)
    assert r.status_code == 202
    assert api.get(f"/api/user/export/{r.get_json()['task_id']}", u2).status_code == 404


def test_bulk_reminders(api, admin, u2):
    inactive = api.get("/api/admin/inactive_users", admin).get_json()
    uid = next(u["id"] for u in inactive if u["email"] == "u2@x.com")
    assert api.post("/api/admin/schedule_bulk_reminders", admin, json={"user_ids": [uid], "reminder_time": _future()}).status_code == 200
    assert api.post("/api/admin/schedule_bulk_reminders", admin, json={"user_ids": [uid], "reminder_time": PAST}).status_code == 400


def test_monthly_report_scheduling(api, admin):
    url = "/api/admin/schedule_monthly_report"
    assert api.post(url, admin, json={"cron_expression": "bad", "recipients": "a@b.com"}).status_code == 400
    assert api.post(url, admin, json={"cron_expression": "0 9 1 * *", "recipients": "nope"}).status_code == 400
    body = {"cron_expression": "0 9 1 * *", "recipients": "a@b.com"}
    rid = api.post(url, admin, json=body).get_json()["report_id"]
    assert api.post(url, admin, json=body).status_code == 200               # same schedule is idempotent
    assert len(api.get("/api/admin/get_scheduled_reports", admin).get_json()["reports"]) == 1
    assert api.delete(f"/api/admin/delete_scheduled_report/{rid}", admin).status_code == 200
    assert api.delete(f"/api/admin/delete_scheduled_report/{rid}", admin).status_code == 404


def test_admin_csv_export_is_admin_only(api, admin, u1):
    assert api.post("/api/admin/export_csv_email", admin).status_code == 202
    assert api.post("/api/admin/export_csv_email", u1).status_code == 403


def test_daily_reminder_task_runs(app, api, u1, course):
    with app.app_context():
        result = tasks.daily_quiz_reminders()
    assert {"quizzes", "emails"} <= set(result)


def test_monthly_report_task_writes_a_file(app, api, u1, course):
    with app.app_context():
        result = tasks.generate_monthly_report("a@b.com")
    assert result["recipients"] == ["a@b.com"] and isinstance(result["emailed"], bool)
    assert os.path.exists(result["file"])


# ----------------------------------------------------- RESTful job endpoints
REPORT = {"cron_expression": "0 9 1 * *", "recipients": "a@b.com"}


def test_scheduled_reports_rest_endpoints(api, admin):
    r = api.post("/api/admin/scheduled_reports", admin, json=REPORT)
    assert r.status_code == 201
    rid = r.get_json()["report_id"]
    assert api.post("/api/admin/scheduled_reports", admin, json=REPORT).status_code == 200   # idempotent
    assert len(api.get("/api/admin/scheduled_reports", admin).get_json()["reports"]) == 1
    assert api.delete(f"/api/admin/scheduled_reports/{rid}", admin).status_code == 200
    assert api.delete(f"/api/admin/scheduled_reports/{rid}", admin).status_code == 404
    assert api.get("/api/admin/scheduled_reports").status_code == 401                        # token required


def test_reminder_rest_endpoints(api, admin, u1, u2):
    assert api.post("/api/user/reminders", u1, json={"reminder_time": _future()}).status_code == 200
    assert api.post("/api/user/reminders", u1, json={"reminder_time": PAST}).status_code == 400
    uid = next(u["id"] for u in api.get("/api/admin/inactive_users", admin).get_json() if u["email"] == "u2@x.com")
    assert api.post("/api/admin/reminders", admin, json={"user_ids": [uid], "reminder_time": _future()}).status_code == 200
    assert api.post("/api/admin/reminders", u1, json={"user_ids": [uid], "reminder_time": _future()}).status_code == 403


def test_legacy_job_urls_still_work(api, admin, u1):
    assert api.post("/api/user/schedule_reminder", u1, json={"reminder_time": _future()}).status_code == 200
    rid = api.post("/api/admin/schedule_monthly_report", admin, json=REPORT).get_json()["report_id"]
    assert len(api.get("/api/admin/get_scheduled_reports", admin).get_json()["reports"]) == 1
    assert api.delete(f"/api/admin/delete_scheduled_report/{rid}", admin).status_code == 200
