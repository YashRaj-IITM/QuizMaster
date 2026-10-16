"""Background jobs (Celery + Redis)."""
import csv
from html import escape
import io
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from celery import shared_task
from flask import current_app
from flask_mail import Message
from sqlalchemy import func

from extensions import db, mail
from models import Quiz, ScheduledReport, Score, Subject, User, utcnow


def _send_mail(subject, recipients, body, html=None, attachment=None):
    """Send an email; never raise (MailHog may not be running)."""
    msg = Message(subject=subject, recipients=recipients, body=body, html=html)
    if attachment:
        msg.attach(*attachment)
    try:
        mail.send(msg)
        return True
    except Exception as exc:  # noqa: BLE001
        current_app.logger.warning("Could not send email to %s: %s", recipients, exc)
        return False


def _export_dir():
    path = current_app.config["EXPORT_DIR"]
    os.makedirs(path, exist_ok=True)
    return path


def _learners():
    return User.query.filter(User.active.is_(True), ~User.roles.any(name="admin"))


# --------------------------------------------------------------------------
# 1. User triggered: export own quiz history as CSV
# --------------------------------------------------------------------------
@shared_task(name="tasks.export_quiz_history_csv")
def export_quiz_history_csv(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    filename = f"quiz_history_{user_id}_{utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    path = os.path.join(_export_dir(), filename)
    scores = Score.query.filter_by(user_id=user_id).order_by(Score.time_stamp).all()
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Quiz ID", "Subject", "Chapter", "Quiz Date", "Correct", "Questions", "Score (%)", "Attempted (UTC)"])
        for s in scores:
            quiz = s.quiz
            writer.writerow(
                [
                    quiz.id,
                    quiz.chapter.subject.name,
                    quiz.chapter.name,
                    quiz.date_of_quiz.strftime("%Y-%m-%d"),
                    s.correct_answers,
                    s.total_questions,
                    f"{s.total_score:.1f}",
                    s.time_stamp.strftime("%Y-%m-%d %H:%M"),
                ]
            )
    with open(path, "rb") as fh:
        _send_mail(
            "Your quiz history (CSV export)",
            [user.email],
            f"Hello {user.full_name},\n\nYour quiz history export is attached.\n\nQuiz Master",
            attachment=(filename, "text/csv", fh.read()),
        )
    return {"user_id": user_id, "file": filename, "rows": len(scores)}


# --------------------------------------------------------------------------
# 2. Admin triggered: users' statistics CSV, e-mailed to the requesting admin
# --------------------------------------------------------------------------
@shared_task(name="tasks.send_csv_export_email")
def send_csv_export_email(admin_id):
    admin = db.session.get(User, admin_id)
    if not admin:
        raise ValueError("Admin not found")

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["User ID", "Full Name", "Email", "Quizzes Taken", "Average Score (%)", "Best Score (%)"])
    for user in _learners().order_by(User.id).all():
        scores = [s.total_score for s in user.scores]
        writer.writerow(
            [
                user.id,
                user.full_name,
                user.email,
                len(scores),
                f"{sum(scores) / len(scores):.1f}" if scores else "0.0",
                f"{max(scores):.1f}" if scores else "0.0",
            ]
        )
    filename = f"quiz-master-users-{utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    with open(os.path.join(_export_dir(), filename), "w", encoding="utf-8", newline="") as fh:
        fh.write(out.getvalue())
    sent = _send_mail(
        "Quiz Master - user statistics export",
        [admin.email],
        "The user statistics export is attached.\n\nQuiz Master",
        attachment=(filename, "text/csv", out.getvalue()),
    )
    return {"file": filename, "emailed": sent}


# --------------------------------------------------------------------------
# 3. Scheduled (e-mailed on request): one-off reminder
# --------------------------------------------------------------------------
@shared_task(name="tasks.send_reminder")
def send_reminder(email, subject, message):
    return _send_mail(subject, [email], message)


# --------------------------------------------------------------------------
# 4. Scheduled (daily 08:00): new / pending quizzes
# --------------------------------------------------------------------------
@shared_task(name="tasks.daily_quiz_reminders")
def daily_quiz_reminders():
    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    soon = today + timedelta(days=3)
    quizzes = Quiz.query.filter(Quiz.date_of_quiz >= today, Quiz.date_of_quiz < soon).all()
    if not quizzes:
        return {"quizzes": 0, "emails": 0}

    sent = 0
    for user in _learners().all():
        done = {s.quiz_id for s in user.scores}
        todo = [q for q in quizzes if q.id not in done]
        if not todo:
            continue
        lines = "\n".join(
            f"- {q.chapter.subject.name} / {q.chapter.name}: {q.remarks} ({q.date_of_quiz:%d %b %Y})"
            for q in todo
        )
        body = f"Hello {user.full_name},\n\nYou have quizzes coming up:\n\n{lines}\n\nQuiz Master"
        if _send_mail("Quiz reminder", [user.email], body):
            sent += 1
    return {"quizzes": len(quizzes), "emails": sent}


# --------------------------------------------------------------------------
# 5. Monthly report (admin-defined schedules, checked every minute by beat)
# --------------------------------------------------------------------------
def build_monthly_report():
    """Return (label, html) for the last 30 days of activity."""
    since = utcnow() - timedelta(days=30)
    label = utcnow().strftime("%B %Y")
    attempts = Score.query.filter(Score.time_stamp >= since).count()
    avg = db.session.query(func.avg(Score.total_score)).filter(Score.time_stamp >= since).scalar() or 0
    top = (
        db.session.query(User.full_name, func.avg(Score.total_score))
        .join(Score, Score.user_id == User.id)
        .filter(Score.time_stamp >= since)
        .group_by(User.id)
        .order_by(func.avg(Score.total_score).desc())
        .limit(5)
        .all()
    )
    rows = "".join(f"<tr><td>{escape(str(n))}</td><td>{a:.1f}%</td></tr>" for n, a in top) or (
        "<tr><td colspan='2'>No attempts</td></tr>"
    )
    html = f"""
    <h2>Quiz Master - Monthly Report ({label})</h2>
    <ul>
      <li>Learners: <b>{_learners().count()}</b></li>
      <li>Subjects: <b>{Subject.query.count()}</b>, Quizzes: <b>{Quiz.query.count()}</b></li>
      <li>Attempts in the last 30 days: <b>{attempts}</b> (average {avg:.1f}%)</li>
    </ul>
    <h3>Top performers</h3>
    <table border="1" cellpadding="6" cellspacing="0">
      <tr><th>Learner</th><th>Average score</th></tr>{rows}
    </table>"""
    return label, html


@shared_task(name="tasks.generate_monthly_report")
def generate_monthly_report(recipients):
    label, html = build_monthly_report()
    path = os.path.join(_export_dir(), f"monthly_report_{utcnow().strftime('%Y_%m')}.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    to = [r.strip() for r in recipients.split(",") if r.strip()]
    sent = _send_mail(f"Quiz Master monthly report - {label}", to, f"Monthly report for {label}", html=html)
    return {"month": label, "recipients": to, "emailed": sent, "file": path}


@shared_task(name="tasks.check_scheduled_reports")
def check_scheduled_reports():
    # Admins enter the day/time in local time (CELERY_TIMEZONE, default Asia/Kolkata)
    tz = ZoneInfo(current_app.config["CELERY"].get("timezone") or "UTC")
    now = datetime.now(tz).replace(tzinfo=None)
    queued = 0
    for report in ScheduledReport.query.filter_by(is_active=True).all():
        due = (report.day_of_month, report.hour, report.minute) == (now.day, now.hour, now.minute)
        if due and not (report.last_sent and report.last_sent > utcnow() - timedelta(hours=23)):
            report.last_sent = utcnow()
            db.session.commit()
            generate_monthly_report.delay(report.recipients)
            queued += 1
    return {"queued": queued}
