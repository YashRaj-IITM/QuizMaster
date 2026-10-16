from datetime import datetime, timezone

from flask_security import RoleMixin, SQLAlchemyUserDatastore, UserMixin

from extensions import db


def utcnow():
    """Naive UTC datetime (all datetimes in the DB are UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt):
    """ISO string with a trailing Z so browsers parse it as UTC."""
    return dt.isoformat() + "Z" if dt else None


roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
)


class Role(db.Model, RoleMixin):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.UnicodeText)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    qualification = db.Column(db.String(150))
    dob = db.Column(db.Date)
    # Flask-Security: `active` False means blacklisted / cannot log in
    active = db.Column(db.Boolean, default=True, nullable=False)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )
    scores = db.relationship("Score", backref="user", cascade="all, delete-orphan")
    attempts = db.relationship("Attempt", backref="user", cascade="all, delete-orphan")

    @property
    def is_admin(self):
        return self.has_role("admin")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "qualification": self.qualification,
            "dob": self.dob.isoformat() if self.dob else None,
            "is_admin": self.is_admin,
        }


user_datastore = SQLAlchemyUserDatastore(db, User, Role)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    chapters = db.relationship(
        "Chapter", backref="subject", cascade="all, delete-orphan", lazy=True
    )


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quizzes = db.relationship(
        "Quiz", backref="chapter", cascade="all, delete-orphan", lazy=True
    )


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"), nullable=False)
    date_of_quiz = db.Column(db.DateTime, default=utcnow)
    time_duration = db.Column(db.String(5))  # "HH:MM"
    remarks = db.Column(db.Text)

    questions = db.relationship(
        "Question", backref="quiz", cascade="all, delete-orphan", lazy=True
    )
    scores = db.relationship(
        "Score", backref="quiz", cascade="all, delete-orphan", lazy=True
    )
    attempts = db.relationship(
        "Attempt", backref="quiz", cascade="all, delete-orphan", lazy=True
    )

    def duration_seconds(self, default="00:30"):
        value = self.time_duration or default
        hours, minutes = value.split(":")
        return (int(hours) * 60 + int(minutes)) * 60


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # 1-4


class Attempt(db.Model):
    """Server-side start of a quiz attempt; used to enforce the time limit."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "quiz_id", name="uq_attempt"),)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    time_stamp = db.Column(db.DateTime, default=utcnow)
    total_score = db.Column(db.Float)  # percentage 0-100
    correct_answers = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    __table_args__ = (db.UniqueConstraint("user_id", "quiz_id", name="uq_score"),)


class ScheduledReport(db.Model):
    """Admin-defined monthly report, executed by the Celery beat checker."""

    id = db.Column(db.Integer, primary_key=True)
    day_of_month = db.Column(db.Integer, nullable=False)
    hour = db.Column(db.Integer, nullable=False)
    minute = db.Column(db.Integer, nullable=False)
    recipients = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_sent = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
