

```markdown
# HabitPulse (Containerized Development Environment)

HabitPulse is a full-stack daily habit tracker built with **Flask**, **PostgreSQL**, **Redis**, and a static **HTML/CSS/JS** frontend, orchestrated with **Docker Compose** and fronted by an **Nginx** reverse proxy.

## Architecture

```text
Browser (http://localhost:8000)
   │
   ▼
Nginx Reverse Proxy (:80)
   ├── /      ──▶ frontend (Nginx serving static HTML/JS on :80)
   └── /api/  ──▶ backend  (Flask API on :5000)
                     ├── db    (PostgreSQL 18 on :5432)
                     └── redis (Redis on :6379)

```

## Project Structure

```text
.
├── docker-compose.yaml          # Multi-container dev orchestration & bind mounts
├── nginx.conf                   # Reverse proxy routing (/ -> frontend, /api/ -> backend)
└── habitpulse/
    ├── backend/
    │   ├── Dockerfile           # Python/Flask image
    │   ├── requirements.txt     # Python dependencies (flask, psycopg, redis)
    │   └── app.py               # REST API & DB table initialization
    └── frontend/
        ├── Dockerfile           # Static Nginx image
        └── index.html           # Single-page UI calling /api/*

```

## Prerequisites

* [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)

## Getting Started (Development)

1. **Build and start all services:**
```bash
docker compose up -d --build

```


2. **Open the application:**
* Web UI: `http://localhost:8000`
* API Health Check: `http://localhost:8000/api/health`


3. **View live container logs:**
```bash
docker compose logs -f

```



## Live Development Workflow

Both application services use **bind mounts** so local edits are reflected inside the running containers without rebuilding images:

* **Frontend (`./habitpulse/frontend` → `/usr/share/nginx/html`):** Edit `index.html` locally and refresh the browser to see updates immediately.
* **Backend (`./habitpulse/backend` → `/app`):** Edit `app.py` locally; with Flask debug/reload enabled (`flask run --host=0.0.0.0 --port=5000 --debug`), the API server restarts automatically on save.

> **When to rebuild:** Run `docker compose up -d --build` only when modifying a `Dockerfile` or adding packages to `requirements.txt`.

## Environment Variables

Configured in `docker-compose.yaml`:

| Service | Variable | Value | Purpose |
| --- | --- | --- | --- |
| `backend` | `POSTGRES_HOST` | `db` | PostgreSQL container hostname |
| `backend` | `POSTGRES_PASSWORD` | `harshit123` | Database password |
| `backend` | `REDIS_HOST` | `redis` | Redis container hostname |
| `db` | `POSTGRES_DB` | `habitpulse` | Auto-created database name |
| `db` | `POSTGRES_PASSWORD` | `harshit123` | Superuser password |
