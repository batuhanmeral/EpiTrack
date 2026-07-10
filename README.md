# EpiTrack

> A digital seizure diary that keeps epilepsy patients, their doctors, and administrators on the same page.

EpiTrack turns scattered, paper-based seizure notes into a single source of truth. Patients log each seizure and watch their trends unfold, doctors follow the patients in their care and stay in touch through built-in messaging, and administrators oversee the whole platform with full audit visibility. Built on Flask, it bundles tracking, statistics, and exportable medical reports into one focused web app.

## Features

- **Role-based access** — separate dashboards for **Patients**, **Doctors**, and **Admins**
- **Doctor approval** — self-registered doctors stay inactive until an admin approves them
- **Seizure logging** — full CRUD with type, trigger, post-ictal notes, and duration
- **Statistics** — interactive Chart.js dashboards for frequency, types, triggers, and trends
- **Doctor monitoring** — doctors view history and stats of assigned patients
- **Messaging** — doctor–patient messaging with read tracking
- **Reports** — export seizure history as **PDF** (fpdf2) and **CSV**
- **Filtering & search** — date-range and keyword filters with pagination
- **Audit log** — every create/update/delete/login is recorded for admin review
- **Dark / light theme** — toggle that follows the system preference and persists per device
- **Security** — scrypt hashing, CSRF protection, login rate limiting, T.C. Kimlik No validation, hardened session cookies

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12, Flask, SQLAlchemy, Flask-Migrate, Flask-WTF, Flask-Limiter |
| **Frontend** | Jinja2, Bootstrap 5, Chart.js |
| **Database** | MySQL 8.0 (PyMySQL) |
| **DevOps** | Docker, Docker Compose, Gunicorn |

## Installation

**Prerequisites:** Python 3.10+, MySQL 8.0, `venv`.

```bash
git clone https://github.com/batuhanmeral/EpiTrack.git seizure-tracker
cd seizure-tracker
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set SECRET_KEY and DATABASE_URL
export FLASK_APP=run.py
flask db upgrade
flask create-admin
python run.py                   # http://localhost:5000
```

**Environment variables:**

- `SECRET_KEY` — signs session cookies; **required**, the app refuses to start without it (random per start in debug mode)
- `DATABASE_URL` — MySQL connection string (default: `mysql+pymysql://root:root@localhost:3306/seizure_tracking`)
- `FLASK_DEBUG` — `1` enables development mode (default: `0`)
- `PORT` — server port (default: `5000`)

## Screenshots

| Screenshot |
|:---:|
| **Patient Dashboard**<br><img src="docs/screenshots/patient.png" width="720" alt="Patient Dashboard"> |
| **Doctor View**<br><img src="docs/screenshots/doctor.png" width="720" alt="Doctor View"> |
| **Admin Panel**<br><img src="docs/screenshots/admin.png" width="720" alt="Admin Panel"> |

## License

Licensed under the **MIT License** — see [LICENSE](LICENSE).
