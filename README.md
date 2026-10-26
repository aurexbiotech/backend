# AUREX HMS Backend API

Simple, secure, beginner-friendly REST API for the **AUREX Hospital Management System (HMS)** built with FastAPI, SQLAlchemy, MySQL, and Argon2 password hashing.

---

## Features

- **FastAPI Framework**: High performance, type-safe API with automatic Swagger UI (`/docs`).
- **MySQL & SQLAlchemy**: Persistent database storage with pooled connections.
- **Secure Authentication**:
  - Passwords hashed using standard **Argon2id**.
  - Dual authentication support: **HttpOnly session cookies** (for frontend browser security) and **Bearer tokens** (for Swagger UI and Postman).
  - CSRF cookie (`hms_csrf`) and header (`X-CSRF-Token`) support.
- **Supported Roles**:
  - `patient`
  - `doctor`
  - `nurse`
  - `laboratory`
  - `pharmacy`
  - `front_desk`
  - `insurance`
  - `department`
  - `administrator`
- **Frontend Compatibility**: Matches the Next.js / Vite React frontend (`d:\Aurex_HMS\frontend`).
- **Safe Error Handling**: Prevents leakage of SQL queries, stack traces, or password hashes.

---

## Quick Setup Guide

### 1. Create and Activate Virtual Environment

From the `backend` folder:

```powershell
cd D:\Aurex_HMS\backend

# Create virtual environment
python -m venv .venv

# Activate in PowerShell
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

### 3. Configure Environment (`.env`)

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Ensure your `.env` contains your MySQL credentials:

```env
DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/aurex
APP_SECRET_KEY=aurex-hospital-management-system-secret-key-2026-production-ready
CSRF_SECRET_KEY=aurex-hospital-csrf-protection-secret-key-2026-unique-hash
FRONTEND_ORIGINS=http://127.0.0.1:3001,http://localhost:3001
COOKIE_SECURE=false
SESSION_TTL_HOURS=8
```

### 4. Seed Demo Accounts (Optional but Recommended)

Seed demo accounts for each role with password `Password123!`:

```powershell
python seed.py
```

Demo accounts created:
| Role | Email | Password |
| :--- | :--- | :--- |
| **Patient** | `patient@aurex.com` | `Password123!` |
| **Doctor** | `doctor@aurex.com` | `Password123!` |
| **Nurse** | `nurse@aurex.com` | `Password123!` |
| **Laboratory** | `lab@aurex.com` | `Password123!` |
| **Pharmacy** | `pharmacy@aurex.com` | `Password123!` |
| **Front Desk** | `frontdesk@aurex.com` | `Password123!` |
| **Insurance** | `insurance@aurex.com` | `Password123!` |
| **Department** | `department@aurex.com` | `Password123!` |
| **Admin** | `admin@aurex.com` | `Password123!` |

### 5. Run the Server

```powershell
python -m uvicorn main:app --reload --port 8001
```

The server starts at `http://127.0.0.1:8001`.
- **Swagger Documentation**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **Health Check**: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

---

## API Endpoints

### 1. Health Checks
- `GET /health` — Check server and database status.
- `GET /health/database` — Check MySQL database status.

### 2. Authentication
- `POST /api/v1/auth/login` — Authenticate user with credentials & role.
  - **Request Body**:
    ```json
    {
      "email": "doctor@aurex.com",
      "password": "Password123!",
      "category": "doctor"
    }
    ```
    *(Also supports `"login_id"` and `"role"` fields)*
  - **Response (200 OK)**:
    ```json
    {
      "id": "uuid-here",
      "full_name": "Dr. Sarah Chen (Doctor)",
      "email": "doctor@aurex.com",
      "role": "doctor",
      "is_active": true,
      "token": "signed-session-token",
      "csrf_token": "random-csrf-token",
      "message": "Login successful"
    }
    ```
  - **Cookies Set**:
    - `hms_session`: HttpOnly signed session cookie.
    - `hms_csrf`: CSRF token for request header verification.

- `GET /api/v1/auth/me` — Return the authenticated user profile.
  - Authenticated via session cookie OR header: `Authorization: Bearer <token>`.
  - **Response (200 OK)**:
    ```json
    {
      "id": "uuid-here",
      "full_name": "Dr. Sarah Chen (Doctor)",
      "email": "doctor@aurex.com",
      "phone_number": "555-0102",
      "role": "doctor",
      "is_active": true,
      "created_at": "2026-10-23T15:16:01"
    }
    ```

- `POST /api/v1/auth/logout` — Invalidate session and clear cookies.
  - **Response (200 OK)**:
    ```json
    {
      "message": "Logged out successfully"
    }
    ```

- `POST /api/v1/auth/register` — Public registration (patients only).

---

## Running Automated Tests

```powershell
python -m pytest -v
```
