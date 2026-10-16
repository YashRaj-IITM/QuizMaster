import os
from datetime import datetime, timedelta, timezone

from celery.result import AsyncResult
from flask import Blueprint, current_app, jsonify, request, send_file
from flask_security import current_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

import tasks
from extensions import db
from models import Attempt, Chapter, Question, Quiz, Score, Subject, User, iso, utcnow
from utils import ValidationError, error, json_body, token_roles

user_bp = Blueprint("user_api", __name__, url_prefix="/api/user")
user_only = token_roles("user")


def _today():
    return utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


def _quiz_brief(quiz):
    return {
        "id": quiz.id,
        "date_of_quiz": quiz.date_of_quiz.isoformat(),
        "time_duration": quiz.time_duration or current_app.config["DEFAULT_QUIZ_DURATION"],
        "remarks": quiz.remarks,
    }


# ===========================================================================
# Dashboard, leaderboard, stats
# ===========================================================================
@user_bp.get("/dashboard")
@user_only
def dashboard():
    subject_id = request.args.get("subject_id", type=int)
    chapter_id = request.args.get("chapter_id", type=int)
    selected_subject = db.session.get(Subject, subject_id) if subject_id else None
    selected_chapter = db.session.get(Chapter, chapter_id) if chapter_id else None

    past = (
        db.session.query(Score, Quiz)
        .join(Quiz, Score.quiz_id == Quiz.id)
        .filter(Score.user_id == current_user.id)
        .order_by(Score.time_stamp.desc())
        .all()
    )
    upcoming = (
        db.session.query(Quiz, Subject.name)
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
        .filter(Quiz.date_of_quiz >= _today())
        .order_by(Quiz.date_of_quiz.asc())
        .first()
    )

    subjects = [
        {
            "id": s.id,
            "name": s.name,
            "chapters": [
                {"id": c.id, "name": c.name, "quizzes": [_quiz_brief(q) for q in c.quizzes]}
                for c in s.chapters
            ],
        }
        for s in Subject.query.order_by(Subject.name).all()
    ]

    return jsonify(
        {
            "user": {"id": current_user.id, "full_name": current_user.full_name, "email": current_user.email},
            "subjects": subjects,
            "selected_subject": {"id": selected_subject.id, "name": selected_subject.name} if selected_subject else None,
            "selected_chapter": {"id": selected_chapter.id, "name": selected_chapter.name} if selected_chapter else None,
            "past_attempts": [
                {
                    "score": {
                        "total_score": round(score.total_score or 0, 1),
                        "time_stamp": iso(score.time_stamp),
                    },
                    "quiz": _quiz_brief(quiz),
                }
                for score, quiz in past
            ],
            "attempted_quizzes": [score.quiz_id for score, _ in past],
            "upcoming_quiz": (
                {**_quiz_brief(upcoming[0]), "subject": upcoming[1]} if upcoming else None
            ),
        }
    )


@user_bp.get("/leaderboard")
@user_only
def leaderboard():
    rows = (
        db.session.query(User.full_name, func.avg(Score.total_score))
        .join(Score, Score.user_id == User.id)
        .group_by(User.id)
        .order_by(func.avg(Score.total_score).desc())
        .limit(10)
        .all()
    )
    return jsonify([{"full_name": name, "avg_score": float(avg)} for name, avg in rows])


@user_bp.get("/quiz_stats")
@user_only
def quiz_stats():
    scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.time_stamp).all()
    return jsonify(
        {
            "labels": [s.quiz.date_of_quiz.strftime("%Y-%m-%d") for s in scores],
            "scores": [round(s.total_score or 0, 1) for s in scores],
        }
    )


# ===========================================================================
# Attempting a quiz (server enforces date, one attempt and the time limit)
# ===========================================================================
def _record_score(quiz, questions, answers):
    """Grade the answers, store one Score row and return the response payload."""
    correct, processed = 0, {}
    for q in questions:
        raw = answers.get(str(q.id))
        try:
            selected = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            selected = None
        if selected is not None and not 1 <= selected <= 4:
            selected = None
        is_correct = selected == q.correct_option
        correct += is_correct
        processed[q.id] = {
            "question": q.question_statement,
            "selected_option": selected,
            "correct_option": q.correct_option,
            "is_correct": is_correct,
            "options": {1: q.option1, 2: q.option2, 3: q.option3, 4: q.option4},
        }
    total = len(questions)
    pct = round(correct / total * 100, 1) if total else 0.0
    db.session.add(
        Score(
            user_id=current_user.id,
            quiz_id=quiz.id,
            total_score=pct,
            correct_answers=correct,
            total_questions=total,
        )
    )
    return pct, correct, total, processed


def _check_can_attempt(quiz):
    if quiz.date_of_quiz < _today():
        return error("This quiz is no longer available (its date has passed)", 403)
    if Score.query.filter_by(user_id=current_user.id, quiz_id=quiz.id).first():
        return error("You have already attempted this quiz", 409)
    return None


@user_bp.get("/quiz/<int:quiz_id>")
@user_only
def attempt_quiz(quiz_id):
    quiz = db.get_or_404(Quiz, quiz_id)
    problem = _check_can_attempt(quiz)
    if problem:
        return problem

    questions = Question.query.filter_by(quiz_id=quiz_id).order_by(Question.id).all()
    if not questions:
        return error("No questions found for this quiz", 404)
    index = request.args.get("question_index", 0, type=int)
    if not 0 <= index < len(questions):
        return error("Question index out of range", 400)

    attempt = Attempt.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    if attempt is None:
        attempt = Attempt(user_id=current_user.id, quiz_id=quiz_id)
        db.session.add(attempt)
        db.session.commit()

    limit = quiz.duration_seconds(current_app.config["DEFAULT_QUIZ_DURATION"])
    remaining = limit - (utcnow() - attempt.started_at).total_seconds()
    if remaining <= -current_app.config["SUBMIT_GRACE_SECONDS"]:
        # Time ran out without a submission: the attempt is closed with 0
        _record_score(quiz, questions, {})
        db.session.commit()
        return error("Time is up for this quiz; your attempt was closed", 403)

    q = questions[index]
    return jsonify(
        {
            "quiz": {**_quiz_brief(quiz)},
            # the correct answer is never sent before the quiz is submitted
            "question": {
                "id": q.id,
                "question_statement": q.question_statement,
                "option1": q.option1,
                "option2": q.option2,
                "option3": q.option3,
                "option4": q.option4,
            },
            "total_questions": len(questions),
            "current_question_index": index,
            "duration_seconds": limit,
            "remaining_seconds": max(0, int(remaining)),
        }
    )


@user_bp.post("/quiz/<int:quiz_id>/submit")
@user_only
def submit_quiz(quiz_id):
    quiz = db.get_or_404(Quiz, quiz_id)
    if Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first():
        return error("You have already attempted this quiz", 409)

    attempt = Attempt.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    if attempt is None:
        return error("Start the quiz before submitting it", 400)

    data = json_body()
    answers = data.get("user_answers", {})
    if not isinstance(answers, dict):
        raise ValidationError("user_answers must be an object of question id -> option number")

    questions = Question.query.filter_by(quiz_id=quiz_id).order_by(Question.id).all()
    elapsed = (utcnow() - attempt.started_at).total_seconds()
    limit = quiz.duration_seconds(current_app.config["DEFAULT_QUIZ_DURATION"])
    late = elapsed > limit + current_app.config["SUBMIT_GRACE_SECONDS"]

    try:
        pct, correct, total, processed = _record_score(quiz, questions, {} if late else answers)
        db.session.commit()
    except IntegrityError:  # double submit race
        db.session.rollback()
        return error("You have already attempted this quiz", 409)

    if late:
        return error("Time limit exceeded; the attempt was recorded with a score of 0", 403)
    return jsonify(
        {
            "success": True,
            "score": pct,
            "correct_answers": correct,
            "total_questions": total,
            "user_answers": processed,
        }
    )


# ===========================================================================
# Reminders and CSV export (Celery jobs)
# ===========================================================================
@user_bp.post("/reminders")
@user_bp.post("/schedule_reminder")  # legacy alias
@user_only
def schedule_reminder():
    """Schedule a reminder e-mail to yourself (the recipient is always the logged-in user)."""
    data = json_body()
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
    subject = str(data.get("subject") or "Quiz Reminder")[:200]
    body = str(data.get("body") or "This is your quiz reminder!")[:2000]
    try:
        result = tasks.send_reminder.apply_async(args=[current_user.email, subject, body], eta=eta)
    except Exception as exc:  # noqa: BLE001
        current_app.logger.warning("Could not queue reminder: %s", exc)
        return error("Background job service (Redis/Celery) is unavailable", 503)
    return jsonify({"success": True, "message": "Reminder scheduled successfully.", "task_id": result.id}), 200


@user_bp.post("/export")
@user_only
def start_export():
    try:
        task = tasks.export_quiz_history_csv.delay(current_user.id)
    except Exception as exc:  # noqa: BLE001
        current_app.logger.warning("Could not queue export: %s", exc)
        return error("Background job service (Redis/Celery) is unavailable", 503)
    return jsonify({"success": True, "message": "Export started", "task_id": task.id}), 202


@user_bp.get("/export/<task_id>")
@user_only
def export_status(task_id):
    try:
        result = AsyncResult(task_id, app=current_app.extensions["celery"])
        state = result.state
        payload = result.result if state == "SUCCESS" else None
    except Exception as exc:  # noqa: BLE001
        current_app.logger.warning("Could not read export result: %s", exc)
        return error("Background job service (Redis/Celery) is unavailable", 503)

    if state == "SUCCESS":
        if not isinstance(payload, dict) or payload.get("user_id") != current_user.id:
            return error("Export not found", 404)
        path = os.path.join(current_app.config["EXPORT_DIR"], os.path.basename(payload["file"]))
        if not os.path.exists(path):
            return error("Export file no longer exists", 404)
        return send_file(path, mimetype="text/csv", as_attachment=True, download_name="quiz_history.csv")
    if state in ("FAILURE", "REVOKED"):
        return error("Export failed, please try again", 500)
    return jsonify({"status": state}), 202
