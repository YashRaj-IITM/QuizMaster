# QuizMaster — Full-Stack Quiz Platform

A full-stack quiz platform. The **quiz master (admin)** builds subjects, chapters, quizzes and multiple-choice questions and monitors usage; **users** register, take timed quizzes, see their score history and compete on a leaderboard.

## Features

**User** - register / login (name, qualification, date of birth), browse subjects → chapters → quizzes, take a **timed** quiz (server-enforced countdown), review correct and wrong answers after submitting, score history, performance chart, leaderboard, schedule a reminder e-mail to yourself, export quiz history as CSV (background job).

**Admin (quiz master)** - full CRUD for subjects, chapters, quizzes (date and duration) and questions, search, user list, statistics dashboard with charts, reminders for inactive users, monthly report scheduling, user statistics CSV e-mailed to the admin.

**Quiz rules enforced by the server** - a quiz can be attempted only on or before its date, only once, and only within its time limit (plus a 30 s grace). Correct answers are never sent to the browser before submission. A late or abandoned attempt is closed with a score of 0.

**Background jobs (Celery + Redis)**

| Job | Trigger | What it does |
|---|---|---|
| `export_quiz_history_csv` | User starts an export (`POST /api/user/export`) | Builds a CSV, e-mails it and makes it downloadable |
| `send_csv_export_email` | Admin clicks *Export CSV* | CSV of all users' statistics, e-mailed to the requesting admin |
| `send_reminder` | Admin bulk reminder / user reminder (scheduled with `eta`) | Sends a reminder e-mail at the chosen time |
| `daily_quiz_reminders` | Celery beat, daily 08:00 | E-mails users about quizzes in the next 3 days they have not taken |
| `check_scheduled_reports` → `generate_monthly_report` | Celery beat every minute, for reports the admin saved (day / time) | E-mails an HTML activity report and saves it in `backend/exports/` |

## Requirements coverage

| Requirement | Where it is implemented |
|---|---|
| User authentication (login + registration) | `backend/routes/auth.py`; Flask-Security-Too hashes passwords and manages users and roles; Vue pages `Login`, `Register` |
| Token-based authentication | Login returns a Flask-Security access token. Protected user and admin endpoints require `@auth_required("token")` plus the appropriate role (`backend/utils.py: token_roles`); `/api/me` and `/api/logout` require a token; register, login and health are public. The Axios interceptor in `frontend/src/api.js` sends the `Authentication-Token` header and clears this app's session keys on 401 |
| RESTful API | Resource-based endpoints under `/api`, plural nouns, correct HTTP verbs and status codes (201 created, 202 accepted, 400/401/403/404/409 errors), JSON everywhere (see *API documentation*). Job resources (`/admin/scheduled_reports`, `/admin/reminders`) follow the same style |
| CRUD operations | Subjects, chapters, quizzes and questions: create, read, update, delete (cascading). Scores: create (submit) and read. Scheduled reports: create, read, delete |
| Validation | Server-side validation of every input: e-mail, password length, dates, `HH:MM` duration, option number 1-4, unique names, existing parents |
| Backend jobs (optional) | Celery + Redis (see *Background jobs*) |
| Stack | Flask, SQLAlchemy, Flask-Security-Too, Vue 3, Axios, Celery, Redis |

## Tech stack

- **Backend:** Flask, Flask-SQLAlchemy (SQLAlchemy 2), Flask-Security-Too (token authentication + roles), Flask-Mail, Flask-Cors
- **Frontend:** Vue 3, Vue Router, Axios, Bootstrap 5, Chart.js
- **Jobs:** Celery, Redis, MailHog (local e-mail testing)
- **Database:** SQLite (any SQLAlchemy URL works via `DATABASE_URL`)

## Project structure

```
quiz-master/
├── backend/
│   ├── app.py              # app factory (Security, CORS, Celery, blueprints)
│   ├── config.py           # all settings, read from environment / .env
│   ├── models.py           # SQLAlchemy models + Flask-Security datastore
│   ├── seed.py             # roles + default admin
│   ├── utils.py            # validation helpers, token_roles decorator
│   ├── routes/             # auth.py, admin.py, user.py
│   ├── tasks.py            # Celery jobs
│   ├── celery_worker.py    # Celery entry point
│   ├── tests/              # pytest suite (46 tests, no Redis needed)
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/               # Vue 3 app (src/api.js, router, views)
├── docker-compose.yml      # optional: Redis + MailHog for the background jobs
└── .github/workflows/ci.yml  # backend tests + frontend lint/build
```

## Installation

**Important:** Run the backend and frontend in separate terminals. Run Redis, the Celery worker and Celery beat in their own terminals when using background jobs.

### Prerequisites
Python 3.10+, Node.js 18+, and (only for background jobs) Redis. MailHog is optional.

### 1. Backend
```bash
git clone <your-repo-url>
cd <your-repo-folder>/backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then replace EVERY placeholder (see below)
python app.py                     # http://127.0.0.1:5000
```
Tables and the default admin are created automatically on first start.

**Secrets are mandatory.** The app refuses to start while `SECRET_KEY` or `SECURITY_PASSWORD_SALT` in `backend/.env` is missing, shorter than 16 characters or still a placeholder. Generate each value with `python -c "import secrets; print(secrets.token_hex(32))"`.

**Admin account:** created on first start from `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `backend/.env`. Set a unique password of at least 12 characters before the first run. Outside test mode, the app refuses to start if the admin password is a known placeholder or shorter than 12 characters. Never commit your `.env` file.

### 2. Frontend
Open a **second terminal** at the repository root, then run:
```bash
cd frontend
npm ci
npm run serve                     # http://localhost:8080
```
Use `npm install` instead of `npm ci` only if you intentionally need to update `package-lock.json`.
The dev server proxies `/api` to Flask, so no extra configuration is needed. If you host the API elsewhere, set `VUE_APP_API_URL` (see `frontend/.env.example`).

### 3. Background jobs (optional)
Run each command in its own terminal, and activate the backend virtual environment before the `celery` commands.
```bash
docker compose up -d                                             # terminal 1 (repo root): Redis + MailHog
#   no Docker? run `redis-server` (and optionally `mailhog`) instead
cd backend && celery -A celery_worker.celery_app worker -l info   # terminal 2
cd backend && celery -A celery_worker.celery_app beat -l info     # terminal 3 (scheduled jobs)
```
E-mails land in MailHog at http://localhost:8025. Without Redis the app still works; job buttons report that the job service is unavailable (HTTP 503). On Windows add `--pool=solo` to the worker command.

### 4. Run the tests
From a new terminal at the repository root (with the backend virtual environment active):
```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```

## Authentication

Login returns an access token issued by Flask-Security. Send it on every protected request:

```
Authentication-Token: <token>
```

Tokens expire after 24 hours and are invalidated on logout. Missing / invalid token → `401`; wrong role → `403`.

```bash
curl -X POST http://127.0.0.1:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<ADMIN_EMAIL>","password":"<ADMIN_PASSWORD>"}'

curl http://127.0.0.1:5000/api/admin/stats -H "Authentication-Token: <token>"
```

## API documentation

All endpoints are under `/api`, accept and return JSON. Errors look like `{"success": false, "error": "...", "message": "..."}`.

### Auth
| Method | Endpoint | Auth | Body / notes |
|---|---|---|---|
| POST | `/register` | - | `email`, `password` (min 8), `full_name`, `qualification?`, `dob?` (YYYY-MM-DD); 409 if the e-mail exists |
| POST | `/login` | - | `email`, `password` → `{success, token, is_admin, full_name, user}` |
| POST | `/logout` | token | invalidates the user's tokens |
| GET | `/me` | token | current user |
| GET | `/health` | - | health check |

### User (role `user`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/user/dashboard?subject_id=&chapter_id=` | subjects with chapters and quizzes, past attempts, attempted quiz ids, next upcoming quiz |
| GET | `/user/quiz/<id>?question_index=0` | one question (without the answer) plus `total_questions`, `duration_seconds`, `remaining_seconds`. Starts the timer on first call. 403 if the quiz date passed or time ran out, 409 if already attempted |
| POST | `/user/quiz/<id>/submit` | `{"user_answers": {"<question_id>": 1-4}}` → `{score, correct_answers, total_questions, user_answers}`; 409 on double submit, 403 if too late |
| GET | `/user/leaderboard` | top 10 learners by average score |
| GET | `/user/quiz_stats` | labels and scores for the performance chart |
| POST | `/user/reminders` | `reminder_time` (future ISO 8601), `subject?`, `body?`; mailed to yourself (legacy alias: `/user/schedule_reminder`) |
| POST | `/user/export` | start CSV export → `202 {task_id}` |
| GET | `/user/export/<task_id>` | `202` while running, `200` + CSV when done |

### Admin (role `admin`)
| Method | Endpoint | Description |
|---|---|---|
| GET / POST | `/admin/subjects` | list (`?q=` search) / create `{name, description?}` (409 on duplicate name) |
| PUT / DELETE | `/admin/subjects/<id>` | update / delete (cascades to chapters, quizzes, questions, scores) |
| GET / POST | `/admin/chapters` | list (`?subject_id=`) / create `{name, subject_id, description?}` |
| PUT / DELETE | `/admin/chapters/<id>` | update / delete |
| GET / POST | `/admin/quizzes` | list (`?chapter_id=`) / create `{chapter_id, date_of_quiz (YYYY-MM-DD), remarks, time_duration? "HH:MM"}` |
| PUT / DELETE | `/admin/quizzes/<id>` | update / delete |
| GET / POST | `/admin/questions` | list (`?quiz_id=`) / create `{quiz_id, question_statement, option1-4, correct_option 1-4}` |
| PUT / DELETE | `/admin/questions/<id>` | update / delete |
| GET | `/admin/users?q=` | list / search users |
| GET | `/admin/stats` | totals, per-quiz stats, recent activity, top performers, per-subject stats |
| GET | `/admin/inactive_users?only_pending=` | users with attempts, last activity and pending quizzes |
| POST | `/admin/reminders` | `{user_ids, reminder_time, subject?, body?}` (legacy alias: `/admin/schedule_bulk_reminders`) |
| GET / POST | `/admin/scheduled_reports` | list active monthly report schedules / create `{cron_expression: "min hour day * *", recipients: "a@x.com,b@x.com"}` (day 1-28; `201`, or `200` if the same schedule exists) |
| DELETE | `/admin/scheduled_reports/<id>` | remove a schedule |

The older action-style URLs (`/admin/schedule_monthly_report`, `/admin/get_scheduled_reports`, `/admin/delete_scheduled_report/<id>`) still work as aliases.

| POST | `/admin/export_csv_email` | CSV of user statistics, e-mailed to the requesting admin → `202` |

## Testing and CI

![CI](https://github.com/<your-username>/<your-repo>/actions/workflows/ci.yml/badge.svg)

```bash
# backend (46 tests, in-memory database, Celery runs eagerly - no Redis or SMTP needed)
cd backend && pip install -r requirements-dev.txt && python -m pytest -q

# frontend
cd frontend && npm ci && npx vue-cli-service lint --no-fix && npm run build
```

The GitHub Actions workflow runs both on every push to `main` / `master` and on pull requests. Replace `<your-username>/<your-repo>` in the badge URL above after you publish the repository.

## Demo walkthrough (about 3 minutes)

1. Start the backend and frontend (see *Installation*) and open http://localhost:8080.
2. Log in as the admin (the `ADMIN_EMAIL` / `ADMIN_PASSWORD` from your `.env`).
3. Create a subject, a chapter, a quiz dated today (duration e.g. `00:05`) and add two or three questions.
4. In a private window register a user and log in.
5. Open the subject → chapter and start the quiz. Watch the countdown, answer and submit.
6. Review the correct answers, then open the dashboard history, performance chart and leaderboard.
7. As admin, open *Stats* for the charts and *Reminders* to schedule a reminder or monthly report. With Redis, the worker and MailHog running, the e-mails arrive at http://localhost:8025.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: flask_security` | Activate the virtual environment and run `pip install -r requirements.txt` inside `backend/` |
| Frontend shows network errors | Make sure the backend is running on port 5000; the dev server proxies `/api` to it (`frontend/vue.config.js`) |
| Job buttons say the service is unavailable | Start Redis and the Celery worker (see *Background jobs*); the rest of the app works without them |
| Login returns 401 after a long time | Tokens expire after 24 hours or after logout; log in again |
| Want a fresh database | Stop the server, delete `backend/quiz_master.db`, start again (the admin account is re-created) |
| Old database from the previous version | The schema changed (Flask-Security users, `Attempt`, `ScheduledReport`); delete the old `quiz_master.db` |
| Windows: Celery worker does not start | Add `--pool=solo` to the worker command |
| `ModuleNotFoundError: No module named 'pkg_resources'` | `setuptools<81` is pinned because Flask-Security's `passlib` needs it; reinstall requirements |

## Data model

`User` (+ `Role`, Flask-Security) 1-N `Score` and `Attempt`; `Subject` 1-N `Chapter` 1-N `Quiz` 1-N `Question`; `Quiz` 1-N `Score` (unique per user and quiz) and `Attempt` (stores the server-side start time that enforces the timer); `ScheduledReport` stores admin-defined monthly reports. Deletes cascade down the tree: deleting a subject, chapter or quiz also deletes the questions, scores and attempts below it (the admin is warned in the confirmation dialog). A production system would archive results instead.

## Security notes

- Passwords are hashed by Flask-Security; the API is stateless and token based (no cookies, so no CSRF surface).
- Secrets come from `.env` (not committed). Start-up fails fast if `SECRET_KEY` / `SECURITY_PASSWORD_SALT` are missing, short or placeholders. Outside test mode, start-up also fails if `ADMIN_PASSWORD` is a known placeholder or shorter than 12 characters (covered by tests).
- Report e-mails escape user-supplied names, and the frontend clears only its own `localStorage` keys on logout / 401.
- All input is validated server-side; role checks use `@auth_required('token')` + `@roles_required(...)`.
- Reminders can only be sent to the logged-in user's own address, and the correct answers stay on the server until a quiz is submitted.
