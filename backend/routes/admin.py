from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_security import current_user
from sqlalchemy import desc, func

import tasks
from extensions import db
from models import (
    Chapter,
    Question,
    Quiz,
    ScheduledReport,
    Score,
    Subject,
    User,
    iso,
    utcnow,
)
from utils import (
    ValidationError,
    duration,
    error,
    integer,
    json_body,
    parse_date,
    text,
    token_roles,
)

admin_bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")
admin_only = token_roles("admin")


def _get_or_404(model, ident, label):
    obj = db.session.get(model, ident)
    if obj is None:
        raise LookupError(label)
    return obj


@admin_bp.errorhandler(LookupError)
def _not_found(err):
    return error(f"{err} not found", 404)


def _dispatch(task, *args, **kwargs):
    """Queue a Celery job; None when the broker (Redis) is unreachable."""
    try:
        return task.apply_async(args=args, **kwargs)
    except Exception:  # noqa: BLE001 - kombu raises several connection errors
        return None


def _unavailable():
    return error("Background job service unavailable - start Redis and the Celery worker", 503)


# ===========================================================================
# Subjects
# ===========================================================================
@admin_bp.get("/subjects")
@admin_only
def get_subjects():
    q = request.args.get("q", "").strip()
    query = Subject.query
    if q:
        query = query.filter(Subject.name.ilike(f"%{q}%"))
    return jsonify(
        [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "chapters": [{"id": c.id, "name": c.name} for c in s.chapters],
            }
            for s in query.order_by(Subject.name).all()
        ]
    )


@admin_bp.post("/subjects")
@admin_only
def create_subject():
    data = json_body()
    name = text(data.get("name"), "Name", required=True, max_len=100)
    description = text(data.get("description"), "Description", max_len=1000)
    if Subject.query.filter(func.lower(Subject.name) == name.lower()).first():
        return error("Subject already exists", 409)
    subject = Subject(name=name, description=description or None)
    db.session.add(subject)
    db.session.commit()
    return jsonify({"success": True, "id": subject.id}), 201


@admin_bp.put("/subjects/<int:id>")
@admin_only
def update_subject(id):
    subject = _get_or_404(Subject, id, "Subject")
    data = json_body()
    if "name" in data:
        name = text(data["name"], "Name", required=True, max_len=100)
        clash = Subject.query.filter(func.lower(Subject.name) == name.lower(), Subject.id != id).first()
        if clash:
            return error("Another subject already has this name", 409)
        subject.name = name
    if "description" in data:
        subject.description = text(data["description"], "Description", max_len=1000) or None
    db.session.commit()
    return jsonify({"success": True})


@admin_bp.delete("/subjects/<int:id>")
@admin_only
def delete_subject(id):
    db.session.delete(_get_or_404(Subject, id, "Subject"))
    db.session.commit()
    return jsonify({"success": True})


# ===========================================================================
# Chapters
# ===========================================================================
@admin_bp.get("/chapters")
@admin_only
def get_chapters():
    subject_id = request.args.get("subject_id", type=int)
    query = Chapter.query.filter_by(subject_id=subject_id) if subject_id else Chapter.query
    return jsonify(
        [
            {"id": c.id, "name": c.name, "description": c.description, "subject_id": c.subject_id}
            for c in query.order_by(Chapter.name).all()
        ]
    )


@admin_bp.post("/chapters")
@admin_only
def create_chapter():
    data = json_body()
    name = text(data.get("name"), "Name", required=True, max_len=100)
    subject_id = integer(data.get("subject_id"), "subject_id", lo=1)
    description = text(data.get("description"), "Description", max_len=1000)
    _get_or_404(Subject, subject_id, "Subject")
    if Chapter.query.filter(func.lower(Chapter.name) == name.lower(), Chapter.subject_id == subject_id).first():
        return error("This subject already has a chapter with that name", 409)
    chapter = Chapter(name=name, subject_id=subject_id, description=description or None)
    db.session.add(chapter)
    db.session.commit()
    return jsonify({"success": True, "id": chapter.id}), 201


@admin_bp.put("/chapters/<int:id>")
@admin_only
def update_chapter(id):
    chapter = _get_or_404(Chapter, id, "Chapter")
    data = json_body()
    if "name" in data:
        name = text(data["name"], "Name", required=True, max_len=100)
        clash = Chapter.query.filter(
            func.lower(Chapter.name) == name.lower(),
            Chapter.subject_id == chapter.subject_id,
            Chapter.id != id,
        ).first()
        if clash:
            return error("This subject already has a chapter with that name", 409)
        chapter.name = name
    if "description" in data:
        chapter.description = text(data["description"], "Description", max_len=1000) or None
    db.session.commit()
    return jsonify({"success": True})


@admin_bp.delete("/chapters/<int:id>")
@admin_only
def delete_chapter(id):
    db.session.delete(_get_or_404(Chapter, id, "Chapter"))
    db.session.commit()
    return jsonify({"success": True})


# ===========================================================================
# Quizzes
# ===========================================================================
def _quiz_dict(q):
    return {
        "id": q.id,
        "date_of_quiz": q.date_of_quiz.isoformat(),
        "time_duration": q.time_duration,
        "remarks": q.remarks,
        "chapter_id": q.chapter_id,
    }


@admin_bp.get("/quizzes")
@admin_only
def get_quizzes():
    chapter_id = request.args.get("chapter_id", type=int)
    query = Quiz.query.filter_by(chapter_id=chapter_id) if chapter_id else Quiz.query
    return jsonify([_quiz_dict(q) for q in query.order_by(Quiz.date_of_quiz).all()])


@admin_bp.post("/quizzes")
@admin_only
def create_quiz():
    data = json_body()
    chapter_id = integer(data.get("chapter_id"), "chapter_id", lo=1)
    date_of_quiz = parse_date(data.get("date_of_quiz"), "date_of_quiz")
    remarks = text(data.get("remarks"), "Remarks", required=True, max_len=500)
    time_duration = duration(data.get("time_duration"))
    _get_or_404(Chapter, chapter_id, "Chapter")
    quiz = Quiz(
        chapter_id=chapter_id,
        date_of_quiz=date_of_quiz,
        remarks=remarks,
        time_duration=time_duration,
    )
    db.session.add(quiz)
    db.session.commit()
    return jsonify({"success": True, "id": quiz.id}), 201


@admin_bp.put("/quizzes/<int:id>")
@admin_only
def update_quiz(id):
    quiz = _get_or_404(Quiz, id, "Quiz")
    data = json_body()
    if "date_of_quiz" in data:
        quiz.date_of_quiz = parse_date(data["date_of_quiz"], "date_of_quiz")
    if "remarks" in data:
        quiz.remarks = text(data["remarks"], "Remarks", required=True, max_len=500)
    if "time_duration" in data:
        quiz.time_duration = duration(data["time_duration"])
    db.session.commit()
    return jsonify({"success": True})


@admin_bp.delete("/quizzes/<int:id>")
@admin_only
def delete_quiz(id):
    db.session.delete(_get_or_404(Quiz, id, "Quiz"))
    db.session.commit()
    return jsonify({"success": True})


# ===========================================================================
# Questions
# ===========================================================================
def _question_dict(q):
    return {
        "id": q.id,
        "question_statement": q.question_statement,
        "option1": q.option1,
        "option2": q.option2,
        "option3": q.option3,
        "option4": q.option4,
        "correct_option": q.correct_option,
        "quiz_id": q.quiz_id,
    }


def _question_fields(data, partial=False, current=None):
    """Validate question fields; on update only the supplied ones change."""
    out = {}
    if not partial or "question_statement" in data:
        out["question_statement"] = text(data.get("question_statement"), "Question", required=True, max_len=1000)
    for i in range(1, 5):
        key = f"option{i}"
        if not partial or key in data:
            out[key] = text(data.get(key), f"Option {i}", required=True, max_len=255)
    if not partial or "correct_option" in data:
        out["correct_option"] = integer(data.get("correct_option"), "correct_option", lo=1, hi=4)
    return out


@admin_bp.get("/questions")
@admin_only
def get_questions():
    quiz_id = request.args.get("quiz_id", type=int)
    query = Question.query.filter_by(quiz_id=quiz_id) if quiz_id else Question.query
    return jsonify([_question_dict(q) for q in query.order_by(Question.id).all()])


@admin_bp.post("/questions")
@admin_only
def create_question():
    data = json_body()
    quiz_id = integer(data.get("quiz_id"), "quiz_id", lo=1)
    fields = _question_fields(data)
    _get_or_404(Quiz, quiz_id, "Quiz")
    options = [fields[f"option{i}"].lower() for i in range(1, 5)]
    if len(set(options)) != 4:
        raise ValidationError("The four options must be different")
    question = Question(quiz_id=quiz_id, **fields)
    db.session.add(question)
    db.session.commit()
    return jsonify({"success": True, "id": question.id}), 201


@admin_bp.put("/questions/<int:id>")
@admin_only
def update_question(id):
    question = _get_or_404(Question, id, "Question")
    fields = _question_fields(json_body(), partial=True)
    # Validate the final option set, not just fields present in a partial update.
    final_options = [
        str(fields.get(f"option{i}", getattr(question, f"option{i}"))).strip().casefold()
        for i in range(1, 5)
    ]
    if len(set(final_options)) != 4:
        raise ValidationError("The four options must be different")
    for key, value in fields.items():
        setattr(question, key, value)
    db.session.commit()
    return jsonify({"success": True})


@admin_bp.delete("/questions/<int:id>")
@admin_only
def delete_question(id):
    db.session.delete(_get_or_404(Question, id, "Question"))
    db.session.commit()
    return jsonify({"success": True})


# ===========================================================================
# Users
# ===========================================================================
@admin_bp.get("/users")
@admin_only
def get_users():
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(User.full_name.ilike(like) | User.email.ilike(like))
    return jsonify([u.to_dict() for u in query.order_by(User.id).all()])


# ===========================================================================
# Statistics
# ===========================================================================
@admin_bp.get("/stats")
@admin_only
def get_stats():
    total_users = User.query.filter(~User.roles.any(name="admin")).count()

    quiz_stats = []
    for quiz in Quiz.query.order_by(Quiz.date_of_quiz).all():
        attempts = Score.query.filter_by(quiz_id=quiz.id).all()
        avg = sum(a.total_score for a in attempts) / len(attempts) if attempts else 0
        quiz_stats.append(
            {
                "id": quiz.id,
                "remarks": quiz.remarks,
                "subject": quiz.chapter.subject.name,
                "date_of_quiz": quiz.date_of_quiz.isoformat(),
                "attempts": len(attempts),
                "avgScore": avg,
                "completionRate": (len(attempts) / total_users * 100) if total_users else 0,
            }
        )

    recent_activity = [
        {
            "id": s.id,
            "user_name": s.user.full_name,
            "action": f"Completed quiz: {s.quiz.remarks}",
            "timestamp": iso(s.time_stamp),
        }
        for s in Score.query.order_by(desc(Score.time_stamp)).limit(10).all()
    ]

    rows = (
        db.session.query(User.id, User.full_name, func.avg(Score.total_score))
        .join(Score, User.id == Score.user_id)
        .group_by(User.id)
        .order_by(desc(func.avg(Score.total_score)))
        .limit(10)
        .all()
    )
    top_performers = [{"id": r[0], "name": r[1], "avgScore": r[2] or 0} for r in rows]

    subject_stats = []
    for subject in Subject.query.order_by(Subject.name).all():
        scores = (
            db.session.query(Score.total_score)
            .join(Quiz, Score.quiz_id == Quiz.id)
            .join(Chapter, Quiz.chapter_id == Chapter.id)
            .filter(Chapter.subject_id == subject.id)
            .all()
        )
        subject_stats.append(
            {
                "id": subject.id,
                "name": subject.name,
                "chapters": len(subject.chapters),
                "quizzes": sum(len(c.quizzes) for c in subject.chapters),
                "avgScore": (sum(s[0] for s in scores) / len(scores)) if scores else 0,
            }
        )

    return jsonify(
        {
            "totalUsers": total_users,
            "totalQuizzes": Quiz.query.count(),
            "totalAttempts": Score.query.count(),
            "totalQuestions": Question.query.count(),
            "quizStats": quiz_stats,
            "recentActivity": recent_activity,
            "topPerformers": top_performers,
            "subjectStats": subject_stats,
        }
    )


# ===========================================================================
# Reminders, monthly reports and CSV export (Celery jobs)
# ===========================================================================
@admin_bp.get("/inactive_users")
@admin_only
def get_inactive_users():
    only_pending = request.args.get("only_pending", "false").lower() == "true"
    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    upcoming = Quiz.query.filter(Quiz.date_of_quiz >= today).all()

    result = []
    for user in User.query.filter(~User.roles.any(name="admin")).order_by(User.id).all():
        scores = Score.query.filter_by(user_id=user.id).order_by(Score.time_stamp.desc()).all()
        done = {s.quiz_id for s in scores}
        pending = [q for q in upcoming if q.id not in done]
        last = scores[0].time_stamp if scores else None
        item = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "attempted_quizzes": len(scores),
            "last_activity": iso(last),
            "upcoming_quizzes": len(upcoming),
            "pending_quizzes": len(pending),
            "is_inactive": (not scores) or (utcnow() - last).days > 7,
        }
        if not only_pending or pending:
            result.append(item)
    return jsonify(result)


@admin_bp.post("/reminders")
@admin_bp.post("/schedule_bulk_reminders")  # legacy alias
@admin_only
def schedule_bulk_reminders():
    data = json_body()
    user_ids = data.get("user_ids")
    if not isinstance(user_ids, list) or not user_ids:
        raise ValidationError("user_ids must be a non-empty list")
    subject = text(
        data.get("subject") or "Quiz Reminder - Please visit and attempt quizzes",
        "Subject", max_len=200,
    )
    body = text(
        data.get("body") or "You have upcoming quizzes you haven't attempted yet. Please visit Quiz Master and complete them.",
        "Body", max_len=2000,
    )
    when = data.get("reminder_time")
    if not when:
        raise ValidationError("reminder_time is required")
    try:
        eta = datetime.fromisoformat(str(when).replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError("reminder_time must be an ISO 8601 date-time")
    if eta.tzinfo is None:
        eta = eta.replace(tzinfo=timezone.utc)
    if eta <= datetime.now(timezone.utc):
        raise ValidationError("Reminder time must be in the future")

    scheduled, failed = 0, []
    for uid in user_ids:
        user = db.session.get(User, uid) if isinstance(uid, int) else None
        if not user or user.is_admin:
            failed.append(f"User {uid} not found or is an admin")
            continue
        if _dispatch(tasks.send_reminder, user.email, subject, body, eta=eta) is None:
            return _unavailable()
        scheduled += 1
    return jsonify(
        {"success": True, "scheduled_count": scheduled, "failed_users": failed, "reminder_time": eta.isoformat()}
    )


def _report_dict(r):
    return {
        "id": r.id,
        "report_type": "monthly",
        "day_of_month": r.day_of_month,
        "hour": r.hour,
        "minute": r.minute,
        "recipients": r.recipients,
        "is_active": r.is_active,
        "last_sent": iso(r.last_sent),
        "created_at": iso(r.created_at),
        "next_run": f"Day {r.day_of_month} at {r.hour:02d}:{r.minute:02d}",
    }


@admin_bp.post("/scheduled_reports")
@admin_bp.post("/schedule_monthly_report")  # legacy alias
@admin_only
def schedule_monthly_report():
    data = json_body()
    cron = text(data.get("cron_expression"), "Cron expression", required=True, max_len=50)
    recipients_raw = data.get("recipients")
    if isinstance(recipients_raw, list):
        recipients_raw = ",".join(str(r) for r in recipients_raw)
    recipients = [r.strip().lower() for r in str(recipients_raw or "").split(",") if r.strip()]
    if not recipients:
        raise ValidationError("Email recipients are required")
    from utils import EMAIL_RE

    bad = [r for r in recipients if not EMAIL_RE.match(r)]
    if bad:
        raise ValidationError(f"Invalid email address: {bad[0]}")

    parts = cron.split()
    if len(parts) != 5:
        raise ValidationError("Cron expression must have 5 fields: minute hour day * *")
    minute = integer(parts[0], "Minute", lo=0, hi=59)
    hour = integer(parts[1], "Hour", lo=0, hi=23)
    day = integer(parts[2], "Day of month", lo=1, hi=28)
    recipients_str = ",".join(recipients)

    existing = ScheduledReport.query.filter_by(
        day_of_month=day, hour=hour, minute=minute, recipients=recipients_str, is_active=True
    ).first()
    report = existing
    if not report:
        report = ScheduledReport(day_of_month=day, hour=hour, minute=minute, recipients=recipients_str)
        db.session.add(report)
        db.session.commit()
    msg = f"Monthly report scheduled for day {day} at {hour:02d}:{minute:02d}"
    return jsonify(
        {
            "success": True,
            "report_id": report.id,
            "task_name": f"monthly_report_{day}_{hour}_{minute}",
            "next_run": f"Day {day} at {hour:02d}:{minute:02d}",
            "cron_expression": cron,
            "recipients": recipients_str,
            "message": msg if not existing else "This schedule already exists",
        }
    ), (200 if existing else 201)


@admin_bp.get("/scheduled_reports")
@admin_bp.get("/get_scheduled_reports")  # legacy alias
@admin_only
def get_scheduled_reports():
    reports = ScheduledReport.query.filter_by(is_active=True).order_by(ScheduledReport.id).all()
    return jsonify({"success": True, "reports": [_report_dict(r) for r in reports]})


@admin_bp.delete("/scheduled_reports/<int:report_id>")
@admin_bp.delete("/delete_scheduled_report/<int:report_id>")  # legacy alias
@admin_only
def delete_scheduled_report(report_id):
    report = _get_or_404(ScheduledReport, report_id, "Scheduled report")
    db.session.delete(report)
    db.session.commit()
    return jsonify({"success": True, "message": "Scheduled monthly report deleted successfully"})


@admin_bp.post("/export_csv_email")
@admin_only
def export_csv_email():
    """Build a CSV of every user's quiz statistics and email it to the requesting admin."""
    result = _dispatch(tasks.send_csv_export_email, current_user.id)
    if result is None:
        return _unavailable()
    return jsonify(
        {
            "success": True,
            "message": "CSV export started. It will be emailed to you shortly.",
            "task_id": result.id,
            "recipients_count": 1,
        }
    ), 202
