# 🏋️ SmartGym — AI-Powered Gym Management System

A complete SaaS-style gym management web application built with **Flask** + **PostgreSQL/SQLite**,
featuring AI workout plans, a voice assistant, admin monitoring, and a smart dashboard.

---

## 🚀 Quick Start (SQLite — zero config)

```bash
# 1. Install Flask (that's it!)
pip install flask

# 2. Run
python run.py

# 3. Visit http://localhost:5000
```

**Default admin:** `admin@gym.com` / `admin123`

---

## 🐘 PostgreSQL Setup

```bash
# 1. Install all dependencies
pip install -r requirements.txt

# 2. Create database
createdb smartgym

# 3. Set environment variable
export DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/smartgym"

# 4. Run
python run.py
```

---

## 📁 Project Structure

```
smartgym/
├── run.py                          ← Main Flask app + all routes
├── config.py                       ← Configuration (SQLite / PostgreSQL)
├── requirements.txt                ← Python dependencies
├── .env.example                    ← Environment variable template
│
├── app/
│   ├── __init__.py                 ← App factory (Flask-SQLAlchemy when available)
│   ├── models.py                   ← SQLAlchemy models (User, LoginActivity, etc.)
│   │
│   ├── routes/                     ← Blueprint modules
│   │   ├── auth.py                 ← Authentication blueprint
│   │   ├── dashboard.py            ← User dashboard + calendar API
│   │   ├── admin.py                ← Admin monitoring blueprint
│   │   └── workout.py              ← Workout & legacy pages blueprint
│   │
│   ├── templates/
│   │   ├── base.html               ← Master layout (navbar + voice bar)
│   │   ├── landing.html            ← Public landing page
│   │   ├── login.html              ← User login
│   │   ├── admin_login.html        ← Admin login
│   │   ├── register.html           ← Registration with live BMI preview
│   │   ├── dashboard.html          ← Smart user dashboard
│   │   ├── admin_dashboard.html    ← Admin monitoring panel
│   │   ├── calendar_view.html      ← Interactive workout calendar
│   │   └── old/                    ← ✅ PRESERVED original Rajat templates
│   │       ├── workout.html
│   │       ├── diet.html
│   │       ├── planner.html
│   │       ├── weekly_plan.html
│   │       ├── assistant.html
│   │       ├── calorie_calc.html
│   │       ├── strength.html
│   │       ├── progress.html
│   │       ├── quotes.html
│   │       └── ... (all originals intact)
│   │
│   └── static/
│       └── js/
│           └── voice_assistant.js  ← AI Voice Coach (Web Speech API)
```

---

## 🌐 All Routes

| Route                    | Description                        |
|--------------------------|------------------------------------|
| `/`                      | Public landing page                |
| `/register`              | User registration                  |
| `/login`                 | User login                         |
| `/logout`                | User logout → /login               |
| `/admin/login`           | Admin login                        |
| `/admin/logout`          | Admin logout → /admin/login        |
| `/dashboard`             | Smart user dashboard               |
| `/calendar`              | Clickable workout calendar         |
| `/admin/dashboard`       | Admin monitoring panel             |
| `/workout`               | Workout library (original)         |
| `/diet`                  | Diet planner (original)            |
| `/weekly_plan`           | Weekly routine (original)          |
| `/assistant`             | AI Coach chat (original)           |
| `/calorie_calc`          | Calorie calculator (original)      |
| `/strength`              | Strength test (original)           |
| `/progress`              | Progress tracker (original)        |
| `/motivation`            | Daily motivation quotes (original) |
| `/api/calendar/log/<dt>` | AJAX: get log for date             |
| `/api/calendar/save`     | AJAX: save workout log             |
| `/api/logs/monthly`      | AJAX: all logs (calendar colors)   |

---

## ✨ Features

### 🧠 AI Workout Plan Engine
- 9 unique workout plans (3 goals × 3 experience levels)
- Auto-assigned on registration
- Goals: Weight Loss, Muscle Gain, Maintenance
- Levels: Beginner, Intermediate, Advanced

### 🔐 Role-Based Authentication
- Separate user and admin portals
- Hashed passwords (Werkzeug PBKDF2)
- Session-based auth with login activity tracking
- `login_required` and `admin_required` decorators

### 📊 Admin Dashboard
- Total users + active (currently logged in) count
- Login/logout timestamps for every session
- Real-time workout log monitoring
- Bootstrap table UI with online/offline badges

### 🖥️ Smart User Dashboard
- Yesterday's workout + completion status
- Today's workout plan (no tab switching required)
- Weekly plan overview
- BMI ring, body stats, assigned plan
- Workout streak counter
- Recent log history

### 📅 Workout Calendar
- Click any date to view plan + log workout
- Add/edit notes
- Mark as completed or missed
- AJAX-powered (no page reloads)
- Color-coded: green=done, red=missed

### 🎤 Voice Assistant
- Speech-to-text (Web Speech API)
- Text-to-speech responses
- English / Hindi toggle (Shift+Space shortcut)
- Smart keyword-based AI responses
- Displayed below navbar on every page

### 🗄️ Database Models
- **User**: id, name, email, password, role, age, gender, height, weight, goal, experience_level, workout_days, bmi, assigned_plan
- **LoginActivity**: id, user_id, login_time, logout_time, is_active, ip_address
- **WorkoutPlan**: id, user_id, day_name, workout_type, exercises
- **WorkoutLog**: id, user_id, date, workout_type, notes, completed

---

## 🛡️ Security

- Passwords hashed with `werkzeug.security.generate_password_hash`
- All user routes protected by `@login_required`
- All admin routes protected by `@admin_required`
- Session-based auth (Flask server-side sessions)
- CSRF-safe (POST forms only for mutations)
- SQL injection protected (parameterised queries)

---

Built with ❤️ — Flask · Bootstrap 5 · Web Speech API · SQLite/PostgreSQL
