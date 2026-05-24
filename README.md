# Placement Portal Application - V2

A web-based campus placement management system built for App Dev II (Jan 2026).  
Allows Admin (Institute), Companies, and Students to manage placement drives, applications, and recruitment.



## Tech Stack

Backend : Flask (Python) 
Frontend : Vue.js 3 + Vite 
Database : SQLite via SQLAlchemy 
Auth : JWT (flask-jwt-extended) 
Caching : Redis + Flask-Caching 
Background Jobs : Celery + Celery Beat 
Email : Flask-Mail (Gmail SMTP)
Styling : Bootstrap 5 + Font Awesome 



## Prerequisites

Make sure the following are installed and running before starting:

- Python 3.10+
- Node.js 18+
- Redis Server (must be running on port 6379)



## How to Run

### 1. Start Redis
```bash
redis-server
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python run.py
```
Flask runs at: `http://127.0.0.1:5000`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Vue runs at: `http://localhost:5173`

### 4. Celery Worker (for async CSV export)
```bash
cd backend
celery -A app.tasks worker --loglevel=info
```

### 5. Celery Beat (for scheduled jobs)
```bash
cd backend
celery -A app.tasks beat --loglevel=info
```

> ⚠️ If restarting Beat, delete the old schedule file first:
> ```bash
> rm -f celerybeat-schedule
> ```

---

## Default Login Credentials

Role - Admin
Username - admin
Password - admin123

> Admin is created automatically when the backend starts for the first time.  
> Students and Companies must register via the Register page.

---

## Folder Structure

```
Placement_Portal/
├── backend/
│   ├── app/
│   │   ├── __init__.py       # App factory, JWT, Redis, Celery setup
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── routes.py         # All API endpoints
│   │   ├── tasks.py          # Celery background jobs
│   │   └── static/           # Resume uploads, CSV exports
│   ├── run.py                # App entry point + admin seeding
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/            # Login, Register, AdminDash, CompanyDash, StudentDash
│   │   ├── router/           # Vue Router with role-based guards
│   │   ├── App.vue
│   │   └── main.js           # JWT token restoration on page load
│   └── index.html
└── README.md
```


## Key Features

- **JWT Authentication** — token-based login, all API routes protected
- **Role-based access** — Admin / Company / Student with route guards
- **CGPA Eligibility Check** — backend validates before allowing application
- **Redis Caching** — dashboard responses cached with auto-expiry
- **Celery Beat Jobs** — daily email reminders + monthly HTML report to admin
- **Async CSV Export** — student triggers export, receives email when ready
- **Interview Scheduling** — companies can schedule interviews per applicant