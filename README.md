# EpiTrack

> A role-based seizure tracking platform that connects epilepsy patients with their doctors and gives administrators full oversight of the system.

EpiTrack is a Flask web application for logging, monitoring, and analyzing epileptic seizures. Patients record their seizures and visualize trends, doctors monitor the patients assigned to them, and administrators manage the entire system. It solves the problem of fragmented, paper-based seizure tracking by centralizing patient history, statistics, doctor–patient messaging, and exportable medical reports in one place.

## 🚀 Features

- **Role-based access** — separate dashboards and permissions for **Patients**, **Doctors**, and **Admins**
- **Seizure logging** — full CRUD for seizures with type, trigger, post-ictal notes, and duration
- **Statistics dashboard** — interactive charts (Chart.js) for seizure frequency, types, triggers, and monthly trends
- **Doctor monitoring** — doctors view the seizure history and statistics of their assigned patients
- **Doctor–patient messaging** — built-in messaging with read tracking
- **Report export** — generate **PDF** (fpdf2) and **CSV** reports of seizure history
- **Filtering & search** — date-range and keyword filters with pagination
- **Audit log** — every create/update/delete/login action is recorded for admin review
- **Security** — scrypt password hashing, CSRF protection, Turkish National ID (T.C. Kimlik No) validation, and hardened session cookies
- **Admin tooling** — CRUD for doctors/patients/seizures, admin profile management, and a CLI command to bootstrap the first admin

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12, Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-WTF |
| **Frontend** | Jinja2, Bootstrap 5, Chart.js |
| **Database** | MySQL 8.0 (via PyMySQL) |
| **Reporting** | fpdf2 |
| **DevOps** | Docker, Docker Compose, Gunicorn |

## 📦 Installation

### Option A — Docker (recommended)

Spins up the app **and** MySQL with a single command. No local Python or database required.

```bash
# 1. Clone the repository
git clone https://github.com/batuhanmeral/epitrack.git
cd epitrack

# 2. Configure environment variables
cp .env.example .env        # adjust SECRET_KEY / passwords as needed

# 3. Build and start the stack
docker compose up --build   # app on http://localhost:5000

# 4. Create the first admin (in a second terminal)
docker compose exec web flask create-admin
```

The web container waits for MySQL, runs `flask db upgrade` automatically, then serves the app with Gunicorn. MySQL is exposed on host port **3307** by default to avoid clashing with a local instance.

### Option B — Local (without Docker)

**Prerequisites:** Python 3.10+, a running MySQL 8.0 instance, and `venv`.

```bash
# 1. Clone and enter the project
git clone https://github.com/batuhanmeral/epitrack.git
cd epitrack

# 2. Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate          # fish: source venv/bin/activate.fish
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env              # set DATABASE_URL to your MySQL instance

# 4. Apply database migrations
export FLASK_APP=run.py
flask db upgrade

# 5. Create the first admin
flask create-admin

# 6. Run the development server
python run.py                     # http://localhost:5000
```

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Signs session cookies | random per start |
| `DATABASE_URL` | MySQL connection string (`mysql+pymysql://...`) | `mysql+pymysql://root:root@localhost:3306/seizure_tracking` |
| `FLASK_DEBUG` | `1` = development mode | `0` |
| `PORT` | Server port (local run) | `5000` |
| `MYSQL_ROOT_PASSWORD` | MySQL root password (Docker) | `root` |
| `MYSQL_DATABASE` | Database name (Docker) | `seizure_tracking` |
| `MYSQL_HOST_PORT` | Host port mapped to MySQL (Docker) | `3307` |

## 💡 Usage

EpiTrack is a server-rendered web app driven by three roles.

**1. Bootstrap an administrator** via the CLI:

```bash
flask create-admin --username admin --fullname "Batuhan Meral" --password "StrongPass123"
```

**2. Register and sign in.** Patients and doctors self-register at `/register`; admins sign in at `/admin/login`.

| Role | Entry point | Capabilities |
|---|---|---|
| Patient | `/` → Patient login | Log seizures, view stats, message doctor, export reports |
| Doctor | `/` → Doctor login | Monitor assigned patients, message patients |
| Admin | `/admin/login` | Manage all entities, view audit log, edit own profile |

**3. Export a report.** While authenticated, download a patient's seizure history by ID:

```bash
# PDF report for patient #1
curl -b cookies.txt http://localhost:5000/download_report/1 -o seizures.pdf

# CSV export for patient #1
curl -b cookies.txt http://localhost:5000/export_csv/1 -o seizures.csv
```

## 📸 Screenshots

| Patient Dashboard | Doctor View | Admin Panel |
|:---:|:---:|:---:|
| <img src="docs/screenshots/patient.png" width="240" alt="Patient Dashboard"> | <img src="docs/screenshots/doctor.png" width="240" alt="Doctor View"> | <img src="docs/screenshots/admin.png" width="240" alt="Admin Panel"> |
| Statistics & charts | Patient monitoring | CRUD & audit log |

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this project under the terms of the license.
