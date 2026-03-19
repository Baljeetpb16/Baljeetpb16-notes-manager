# NoteNest 📚

A Django web application for college students to manage **notes** and **assignments**.
Built as a college project using GitHub Student Developer Pack (DigitalOcean hosting).

![CI](https://github.com/Baljeetpb16/Baljeetpb16-notes-manager/actions/workflows/ci.yml/badge.svg)

## Features

- **Authentication** – signup, login, logout with per-user data isolation
- **Notes** – upload files (PDF/images), add tags/subject/semester, search and filter
- **Assignments** – create assignments with due dates, mark done, edit, delete
- **Dashboard** – quick stats and recent activity
- **Summarizer** – auto-generate an extractive summary of any note's text content
- **Export** – download notes as Markdown (`.md`), PDF (`.pdf`), or Word (`.docx`)
- **Collaboration** – share notes with other users; view notes shared with you
- **Responsive UI** – Bootstrap 5 with clean navbar

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Static files | WhiteNoise |
| Config | django-environ |
| WSGI server | Gunicorn |
| PDF export | fpdf2 |
| DOCX export | python-docx |
| Lint | Ruff |

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Baljeetpb16/Baljeetpb16-notes-manager.git
cd Baljeetpb16-notes-manager
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set at minimum a strong SECRET_KEY
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (optional, for Django admin)

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

Visit <http://localhost:8000> — sign up and start adding notes!

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (required in production) | insecure dev default |
| `DEBUG` | `True` for dev, `False` in production | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection URL | `sqlite:///db.sqlite3` |

Example `.env`:

```env
SECRET_KEY=replace-me-with-50-random-chars
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

For PostgreSQL (production):

```env
DATABASE_URL=postgres://user:password@host:5432/dbname
```

---

## Running Tests

```bash
python manage.py test
```

## Linting

```bash
ruff check .
```

---

## DigitalOcean App Platform Deployment

### 1. Create a managed PostgreSQL database

In DigitalOcean control panel → **Databases → Create Database Cluster** (PostgreSQL).
Copy the **connection string** (URI format).

### 2. Push code to GitHub

Make sure your code is on the `main` branch.

### 3. Create an App on DigitalOcean App Platform

1. Go to **Apps → Create App** and connect your GitHub repo.
2. DigitalOcean will auto-detect the `Procfile`.
3. Set **Run Command**: `gunicorn notenest.wsgi:application --log-file -`

### 4. Set environment variables in App settings

| Key | Value |
|-----|-------|
| `SECRET_KEY` | A strong random string (50+ chars) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | Your app's domain, e.g. `myapp.ondigitalocean.app` |
| `DATABASE_URL` | PostgreSQL connection string from step 1 |

### 5. Add build and release commands

Under **App Spec** or the **Components** settings, add:

- **Build command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- **Run command**: `gunicorn notenest.wsgi:application --log-file -`

Or add a `release` phase:

```yaml
# .do/app.yaml (optional)
services:
  - name: web
    run_command: gunicorn notenest.wsgi:application --log-file -
    build_command: pip install -r requirements.txt && python manage.py collectstatic --noinput
    envs:
      - key: SECRET_KEY
        scope: RUN_AND_BUILD_TIME
        type: SECRET
      ...

jobs:
  - name: migrate
    kind: PRE_DEPLOY
    run_command: python manage.py migrate --noinput
```

### 6. Media file storage (optional)

For uploaded files in production, use **DigitalOcean Spaces** (S3-compatible):

```bash
pip install django-storages boto3
```

Add to `settings.py`:

```python
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = env("DO_SPACES_KEY")
AWS_SECRET_ACCESS_KEY = env("DO_SPACES_SECRET")
AWS_STORAGE_BUCKET_NAME = env("DO_SPACES_BUCKET")
AWS_S3_ENDPOINT_URL = env("DO_SPACES_ENDPOINT")  # e.g. https://nyc3.digitaloceanspaces.com
AWS_DEFAULT_ACL = "public-read"
```

---

## CI/CD (GitHub Actions)

The workflow `.github/workflows/ci.yml` runs on every push/PR:

1. Sets up Python 3.11
2. Installs dependencies
3. Runs `python manage.py check`
4. Runs `ruff check .` (lint)
5. Runs `python manage.py test`

---

## Project Structure

```
Baljeetpb16-notes-manager/
├── notenest/           # Django project settings & URLs
├── accounts/           # Auth: signup, login, logout
├── notes/              # Notes upload, list, search, filter
├── assignments/        # Assignment CRUD
├── templates/          # HTML templates (base + per-app)
├── static/css/         # Custom CSS
├── .env.example        # Environment variable template
├── .gitignore
├── Procfile            # DigitalOcean/Heroku deployment
├── runtime.txt         # Python version
├── requirements.txt
├── manage.py
└── README.md
```

---

## License

MIT
