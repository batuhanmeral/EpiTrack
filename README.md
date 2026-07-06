# EpiTrack

> A digital seizure diary that keeps epilepsy patients, their doctors, and administrators on the same page.

EpiTrack turns scattered, paper-based seizure notes into a single source of truth. Patients log each seizure and watch their trends unfold, doctors follow the patients in their care and stay in touch through built-in messaging, and administrators oversee the whole platform with full audit visibility. Built on Flask, it bundles tracking, statistics, and exportable medical reports into one focused web app.

## 🚀 Features

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

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12, Flask, SQLAlchemy, Flask-Migrate, Flask-WTF, Flask-Limiter |
| **Frontend** | Jinja2, Bootstrap 5, Chart.js |
| **Database** | MySQL 8.0 (PyMySQL) |
| **DevOps** | Docker, Docker Compose, Gunicorn |

## 📦 Installation

### Option A — Docker (recommended)

```bash
git clone https://github.com/batuhanmeral/EpiTrack.git seizure-tracker
cd seizure-tracker
cp .env.example .env            # set SECRET_KEY (required) and passwords
docker compose up --build       # app on http://localhost:5000
docker compose exec web flask create-admin   # in a second terminal
```

The web container waits for MySQL, runs `flask db upgrade`, then serves via Gunicorn. MySQL is exposed on host port **3307** by default.

### Option B — Local

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

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Signs session cookies — **required**; the app refuses to start without it (random per start in debug mode) | — |
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://root:root@localhost:3306/seizure_tracking` |
| `FLASK_DEBUG` | `1` = development mode | `0` |
| `PORT` | Server port (local run) | `5000` |
| `MYSQL_ROOT_PASSWORD` / `MYSQL_DATABASE` / `MYSQL_HOST_PORT` | Docker MySQL settings | `root` / `seizure_tracking` / `3307` |

## 💡 Usage

Bootstrap an admin, then register and sign in:

```bash
flask create-admin --username admin --fullname "Batuhan Meral" --password "StrongPass123"
```

Patients and doctors self-register at `/register`; admins sign in at `/admin/login`. Doctor accounts stay inactive until an admin approves them from the **Doctors** page, and a doctor with assigned patients cannot be deleted before their patients are reassigned.

| Role | Capabilities |
|---|---|
| Patient | Log seizures, view stats, message doctor, export reports |
| Doctor | Monitor assigned patients, message patients |
| Admin | Manage all entities, approve doctors, view audit log, edit profile |

Export reports while authenticated:

```bash
curl -b cookies.txt http://localhost:5000/download_report/1 -o seizures.pdf
curl -b cookies.txt http://localhost:5000/export_csv/1 -o seizures.csv
```

## 📸 Screenshots

| Patient Dashboard | Doctor View | Admin Panel |
|:---:|:---:|:---:|
| <img src="docs/screenshots/patient.png" width="240" alt="Patient Dashboard"> | <img src="docs/screenshots/doctor.png" width="240" alt="Doctor View"> | <img src="docs/screenshots/admin.png" width="240" alt="Admin Panel"> |

## 📄 License

Licensed under the **MIT License** — see [LICENSE](LICENSE).
