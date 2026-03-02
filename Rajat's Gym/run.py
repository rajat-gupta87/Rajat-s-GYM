"""
SmartGym — AI-Powered Gym Management System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Requirements: Flask + Werkzeug (pip install flask)
Optional:     Flask-SQLAlchemy + psycopg2-binary for PostgreSQL

Quick start:
    pip install flask
    python run.py
    → http://localhost:5000

Default admin: admin@gym.com / admin123
"""

import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash, g)

# ═══════════════════════════════════════════════════════════════════════════════
# APP SETUP
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(
    __name__,
    template_folder='app/templates',
    static_folder='app/static',
)
app.secret_key = os.environ.get('SECRET_KEY', 'smartgym_rajat_secret_2024_xyz')

DB_PATH = os.path.join(os.path.dirname(__file__), 'smartgym.db')


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE LAYER  (SQLite default, PostgreSQL via DATABASE_URL)
# ═══════════════════════════════════════════════════════════════════════════════

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()


def query(sql, params=(), one=False, commit=False):
    db = get_db()
    cur = db.execute(sql, params)
    if commit:
        db.commit()
        return cur.lastrowid
    return cur.fetchone() if one else cur.fetchall()


def init_db():
    """Create all tables and seed default admin."""
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
    PRAGMA journal_mode=WAL;

    CREATE TABLE IF NOT EXISTS users (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT    NOT NULL,
        email            TEXT    UNIQUE NOT NULL,
        password         TEXT    NOT NULL,
        role             TEXT    DEFAULT 'user',
        age              INTEGER,
        gender           TEXT,
        height           REAL,
        weight           REAL,
        goal             TEXT,
        experience_level TEXT,
        workout_days     INTEGER DEFAULT 3,
        bmi              REAL,
        assigned_plan    TEXT,
        created_at       TEXT    DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS login_activity (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id),
        login_time  TEXT,
        logout_time TEXT,
        is_active   INTEGER DEFAULT 1,
        ip_address  TEXT
    );

    CREATE TABLE IF NOT EXISTS workout_plans (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL REFERENCES users(id),
        day_name     TEXT,
        workout_type TEXT,
        exercises    TEXT
    );

    CREATE TABLE IF NOT EXISTS workout_logs (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL REFERENCES users(id),
        date         TEXT,
        workout_type TEXT,
        notes        TEXT,
        completed    INTEGER DEFAULT 0,
        created_at   TEXT    DEFAULT (datetime('now'))
    );
                     
    CREATE TABLE IF NOT EXISTS progress (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER NOT NULL REFERENCES users(id),
    weight   REAL,
    date     TEXT
    );
                     
    """)
    db.commit()

    if not db.execute("SELECT id FROM users WHERE role='admin'").fetchone():
        db.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            ('Admin', 'admin@gym.com', generate_password_hash('admin123'), 'admin')
        )
        db.commit()
    db.close()


init_db()


# ═══════════════════════════════════════════════════════════════════════════════
# AI WORKOUT PLAN ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

WORKOUT_PLANS = {
    # ── Weight Loss ─────────────────────────────────────────────────────────
    ('weight_loss', 'Beginner'): [
        ('Monday',    'Cardio',         'Brisk Walk 30min, Jump Rope 10min, Stretching 10min'),
        ('Wednesday', 'Full Body',      'Bodyweight Squats 3x15, Push-ups 3x10, Plank 3x30s, Glute Bridge 3x15'),
        ('Friday',    'Cardio + Core',  'Jogging 20min, Crunches 3x20, Leg Raises 3x15, Mountain Climbers 3x20'),
    ],
    ('weight_loss', 'Intermediate'): [
        ('Monday',    'HIIT Cardio',    'Burpees 4x15, Jump Squats 4x15, Mountain Climbers 4x20, High Knees 4x30s'),
        ('Tuesday',   'Upper Body',     'DB Press 4x12, DB Rows 4x12, Shoulder Press 3x12, Tricep Dips 3x12'),
        ('Thursday',  'Lower Body',     'Deadlifts 4x10, Lunges 4x12, Leg Press 3x15, Calf Raises 3x20'),
        ('Saturday',  'Active Recovery','Yoga 30min, Light Walk 20min, Stretching 15min'),
    ],
    ('weight_loss', 'Advanced'): [
        ('Monday',    'Push',           'Bench Press 5x5, Incline DB Press 4x10, Tricep Dips 3x12, Cable Flyes 3x15'),
        ('Tuesday',   'Pull',           'Pull-ups 5x8, Barbell Rows 4x8, Face Pulls 4x15, Bicep Curls 4x12'),
        ('Wednesday', 'HIIT',           'Sprints 6x100m, Box Jumps 4x10, Battle Ropes 4x30s, KB Swings 4x15'),
        ('Friday',    'Legs + Cardio',  'Squats 5x5, Romanian Deadlift 4x8, Calf Raises 4x20, Bike 15min'),
        ('Saturday',  'Cardio',         'Run 5km, Cycling 20min, Core Circuit 15min'),
    ],

    # ── Muscle Gain ──────────────────────────────────────────────────────────
    ('muscle_gain', 'Beginner'): [
        ('Monday',    'Push',           'Push-ups 4x12, DB Shoulder Press 3x10, Tricep Extensions 3x12, Lateral Raises 3x12'),
        ('Wednesday', 'Pull',           'DB Rows 4x10, Face Pulls 3x15, Bicep Curls 3x12, Hammer Curls 3x12'),
        ('Friday',    'Legs',           'Goblet Squats 4x12, Lunges 3x12, Glute Bridge 3x15, Calf Raises 3x20'),
    ],
    ('muscle_gain', 'Intermediate'): [
        ('Monday',    'Chest + Triceps','Bench Press 4x8, Incline Press 4x10, Cable Flyes 3x12, Skull Crushers 3x12'),
        ('Tuesday',   'Back + Biceps',  'Deadlift 4x6, Pull-ups 4x8, DB Rows 4x10, Hammer Curls 3x12'),
        ('Thursday',  'Shoulders',      'OHP 4x8, Lateral Raises 4x15, Front Raises 3x12, Rear Delt Flyes 3x15'),
        ('Friday',    'Legs',           'Squats 4x8, Leg Press 4x12, Romanian DL 3x10, Calf Raises 4x20'),
    ],
    ('muscle_gain', 'Advanced'): [
        ('Monday',    'Push Heavy',     'Bench Press 5x5, OHP 4x6, Dips 4x10, Cable Flyes 3x15, Tricep Work 3x12'),
        ('Tuesday',   'Pull Heavy',     'Weighted Pull-ups 5x5, Barbell Rows 4x6, Face Pulls 4x15, Curls 4x12'),
        ('Wednesday', 'Legs Heavy',     'Back Squat 5x5, Romanian DL 4x8, Leg Press 3x15, Hack Squat 3x10'),
        ('Friday',    'Push Volume',    'Incline Press 4x12, DB Shoulder Press 4x12, Tricep Pushdown 4x15, Lateral Raises 4x15'),
        ('Saturday',  'Pull Volume',    'Lat Pulldown 4x12, Cable Rows 4x12, Face Pulls 3x20, Bicep Curls 4x15'),
    ],

    # ── Maintenance ──────────────────────────────────────────────────────────
    ('maintenance', 'Beginner'): [
        ('Monday',    'Full Body A',    'Squats 3x10, Push-ups 3x10, DB Rows 3x10, Plank 3x30s'),
        ('Thursday',  'Full Body B',    'Lunges 3x10, DB Press 3x10, Face Pulls 3x12, Dead Bug 3x10'),
    ],
    ('maintenance', 'Intermediate'): [
        ('Monday',    'Upper Body',     'Bench Press 3x10, OHP 3x10, Rows 3x10, Pull-ups 3x8, Curls 3x12'),
        ('Wednesday', 'Lower Body',     'Squats 3x10, Deadlifts 3x8, Lunges 3x10, Calf Raises 3x15'),
        ('Friday',    'Full Body',      'Clean & Press 3x8, Step-ups 3x12, Core Work 15min, Mobility 10min'),
    ],
    ('maintenance', 'Advanced'): [
        ('Monday',    'Push',           'Bench 4x8, OHP 4x8, Dips 3x12, Lateral Raises 3x15'),
        ('Tuesday',   'Pull',           'Deadlift 4x5, Pull-ups 4x8, Rows 4x10, Face Pulls 3x15'),
        ('Thursday',  'Legs',           'Squats 4x8, RDL 4x8, Leg Curl 3x12, Calf Raises 4x15'),
        ('Saturday',  'Sport/Cardio',   'Swimming/Cycling/Sport 45min, Stretching 15min'),
    ],
}


def assign_plan(user_id, goal, experience):
    """Assign AI-generated workout plan based on goal and experience."""
    # Map goal
    g = (goal or '').lower()
    if 'loss' in g or 'fat' in g or 'slim' in g or 'cut' in g:
        goal_key = 'weight_loss'
    elif 'muscle' in g or 'bulk' in g or 'gain' in g or 'mass' in g:
        goal_key = 'muscle_gain'
    else:
        goal_key = 'maintenance'

    # Map experience
    e = (experience or '').lower()
    if 'inter' in e:
        exp_key = 'Intermediate'
    elif 'adv' in e or 'expert' in e:
        exp_key = 'Advanced'
    else:
        exp_key = 'Beginner'

    days = WORKOUT_PLANS.get((goal_key, exp_key),
                             WORKOUT_PLANS[('maintenance', 'Beginner')])
    plan_label = f"{goal_key.replace('_', ' ').title()} · {exp_key}"

    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM workout_plans WHERE user_id=?", (user_id,))
    for day_name, wtype, exercises in days:
        conn.execute(
            "INSERT INTO workout_plans(user_id,day_name,workout_type,exercises) VALUES(?,?,?,?)",
            (user_id, day_name, wtype, exercises)
        )
    conn.execute("UPDATE users SET assigned_plan=? WHERE id=?", (plan_label, user_id))
    conn.commit()
    conn.close()
    return plan_label


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH DECORATORS
# ═══════════════════════════════════════════════════════════════════════════════

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return fn(*args, **kwargs)
    return wrapper


def get_current_user():
    if 'user_id' not in session:
        return None
    return get_db().execute(
        "SELECT * FROM users WHERE id=?", (session['user_id'],)
    ).fetchone()


@app.context_processor
def inject_globals():
    return {'current_user': get_current_user(), 'session': session}


def _mark_logout():
    act_id = session.get('login_activity_id')
    if act_id:
        query("UPDATE login_activity SET logout_time=?, is_active=0 WHERE id=?",
              (datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), act_id), commit=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        age      = request.form.get('age', type=int)
        gender   = request.form.get('gender', '')
        height   = request.form.get('height', type=float)
        weight   = request.form.get('weight', type=float)
        goal     = request.form.get('goal', '')
        exp      = request.form.get('experience', '')
        w_days   = request.form.get('workout_days', 3, type=int)

        if not all([name, email, password]):
            flash('Please fill all required fields.', 'danger')
            return render_template('register.html')

        if query("SELECT id FROM users WHERE email=?", (email,), one=True):
            flash('Email already registered. Please login.', 'danger')
            return render_template('register.html')

        bmi = round(weight / ((height / 100) ** 2), 1) if (height and weight) else None

        uid = query(
            "INSERT INTO users(name,email,password,role,age,gender,height,weight,"
            "goal,experience_level,workout_days,bmi) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (name, email, generate_password_hash(password), 'user',
             age, gender, height, weight, goal, exp, w_days, bmi),
            commit=True
        )
        assign_plan(uid, goal, exp)
        flash(f'Welcome, {name}! Your personalised workout plan is ready. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id') and session.get('role') == 'user':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = query("SELECT * FROM users WHERE email=? AND role='user'", (email,), one=True)

        if user and check_password_hash(user['password'], password):
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['role']      = 'user'
            act_id = query(
                "INSERT INTO login_activity(user_id,login_time,is_active,ip_address) VALUES(?,?,1,?)",
                (user['id'], datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                 request.remote_addr), commit=True
            )
            session['login_activity_id'] = act_id
            return redirect(url_for('dashboard'))

        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    _mark_logout()
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        admin    = query("SELECT * FROM users WHERE email=? AND role='admin'", (email,), one=True)

        if admin and check_password_hash(admin['password'], password):
            session['user_id']   = admin['id']
            session['user_name'] = admin['name']
            session['role']      = 'admin'
            act_id = query(
                "INSERT INTO login_activity(user_id,login_time,is_active,ip_address) VALUES(?,?,1,?)",
                (admin['id'], datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                 request.remote_addr), commit=True
            )
            session['login_activity_id'] = act_id
            return redirect(url_for('admin_dashboard'))

        flash('Invalid admin credentials.', 'danger')
    return render_template('admin_login.html')


@app.route('/admin/logout')
@admin_required
def admin_logout():
    _mark_logout()
    session.clear()
    return redirect(url_for('admin_login'))


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_users  = query("SELECT COUNT(*) as c FROM users WHERE role='user'", one=True)['c']
    active_users = query("SELECT COUNT(*) as c FROM login_activity WHERE is_active=1", one=True)['c']
    users        = query("SELECT * FROM users WHERE role='user' ORDER BY created_at DESC")
    login_history = query("""
        SELECT la.*, u.name as user_name
        FROM login_activity la JOIN users u ON la.user_id=u.id
        ORDER BY la.login_time DESC LIMIT 50
    """)
    recent_logs = query("""
        SELECT wl.*, u.name as user_name
        FROM workout_logs wl JOIN users u ON wl.user_id=u.id
        ORDER BY wl.date DESC LIMIT 20
    """)
    users_with_status = []
    for u in users:
        is_online = bool(query(
            "SELECT id FROM login_activity WHERE user_id=? AND is_active=1 LIMIT 1",
            (u['id'],), one=True
        ))
        users_with_status.append({'user': dict(u), 'is_online': is_online})

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           active_users=active_users,
                           users_with_status=users_with_status,
                           login_history=login_history,
                           recent_logs=recent_logs)


# ═══════════════════════════════════════════════════════════════════════════════
# USER DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    uid       = session['user_id']
    today     = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today_day = datetime.now().strftime('%A')

    today_plan    = query("SELECT * FROM workout_plans WHERE user_id=? AND day_name=?", (uid, today_day), one=True)
    yesterday_log = query("SELECT * FROM workout_logs WHERE user_id=? AND date=?",      (uid, yesterday), one=True)
    today_log     = query("SELECT * FROM workout_logs WHERE user_id=? AND date=?",      (uid, today),     one=True)
    all_plans     = query("SELECT * FROM workout_plans WHERE user_id=?",                (uid,))
    recent_logs   = query("SELECT * FROM workout_logs WHERE user_id=? ORDER BY date DESC LIMIT 7", (uid,))

    # Stats
    total_logged   = query("SELECT COUNT(*) as c FROM workout_logs WHERE user_id=?",              (uid,), one=True)['c']
    total_done     = query("SELECT COUNT(*) as c FROM workout_logs WHERE user_id=? AND completed=1", (uid,), one=True)['c']
    streak         = _calculate_streak(uid)

    return render_template('dashboard.html',
                           today_plan=today_plan,
                           yesterday_log=yesterday_log,
                           today_log=today_log,
                           all_plans=all_plans,
                           recent_logs=recent_logs,
                           today=today,
                           today_day=today_day,
                           total_logged=total_logged,
                           total_done=total_done,
                           streak=streak)


def _calculate_streak(user_id):
    """Calculate current consecutive completed workout days."""
    logs = query(
        "SELECT date FROM workout_logs WHERE user_id=? AND completed=1 ORDER BY date DESC",
        (user_id,)
    )
    if not logs:
        return 0
    streak  = 0
    current = datetime.now().date()
    for log in logs:
        log_date = datetime.strptime(log['date'], '%Y-%m-%d').date()
        if log_date == current or log_date == current - timedelta(days=streak):
            streak += 1
            current = log_date - timedelta(days=1)
        else:
            break
    return streak


# ═══════════════════════════════════════════════════════════════════════════════
# CALENDAR & AJAX API
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar_view.html')


@app.route('/api/calendar/log/<date>')
@login_required
def get_log(date):
    uid  = session['user_id']
    log  = query("SELECT * FROM workout_logs WHERE user_id=? AND date=?", (uid, date), one=True)
    try:
        plan = query("SELECT * FROM workout_plans WHERE user_id=? AND day_name=?",
                     (uid, datetime.strptime(date, '%Y-%m-%d').strftime('%A')), one=True)
    except Exception:
        plan = None

    return jsonify({
        'log': {
            'id': log['id'], 'notes': log['notes'],
            'completed': bool(log['completed']),
            'workout_type': log['workout_type'],
        } if log else None,
        'plan': {
            'day_name': plan['day_name'],
            'workout_type': plan['workout_type'],
            'exercises': plan['exercises'],
        } if plan else None,
    })


@app.route('/api/calendar/save', methods=['POST'])
@login_required
def save_log():
    uid          = session['user_id']
    data         = request.json
    date         = data.get('date')
    notes        = data.get('notes', '')
    completed    = 1 if data.get('completed') else 0
    workout_type = data.get('workout_type', '')

    existing = query("SELECT id FROM workout_logs WHERE user_id=? AND date=?", (uid, date), one=True)
    if existing:
        query("UPDATE workout_logs SET notes=?,completed=?,workout_type=? WHERE id=?",
              (notes, completed, workout_type, existing['id']), commit=True)
    else:
        query("INSERT INTO workout_logs(user_id,date,notes,completed,workout_type) VALUES(?,?,?,?,?)",
              (uid, date, notes, completed, workout_type), commit=True)
    return jsonify({'status': 'ok'})


@app.route('/api/logs/monthly')
@login_required
def monthly_logs():
    uid  = session['user_id']
    logs = query("SELECT date,completed,workout_type FROM workout_logs WHERE user_id=?", (uid,))
    return jsonify([{
        'date': l['date'],
        'completed': bool(l['completed']),
        'workout_type': l['workout_type'],
    } for l in logs])


# ═══════════════════════════════════════════════════════════════════════════════
# PRESERVED ORIGINAL PAGES  (Rajat's templates)
# ═══════════════════════════════════════════════════════════════════════════════

# @app.route('/workout')
# @login_required
# def workout():
#     uid   = session['user_id']
#     plans = query("SELECT * FROM workout_plans WHERE user_id=?", (uid,))
#     return render_template('old/workout.html', plans=plans, session=session)

# ---------------- WORKOUT DIAGNOSIS ----------------

def get_workout_plan(goal):
    """Return list of workout lines based on goal keyword."""
    plans = {
        "fat_loss": [
            "Day 1: Full Body HIIT (20–30 min)",
            "Day 2: Brisk Walk + Core Work",
            "Day 3: Upper Body Dumbbells",
            "Day 4: Rest / Mobility",
            "Day 5: Cardio + Abs",
            "Day 6: Lower Body Strength",
            "Day 7: Light Walk / Yoga"
        ],
        "muscle_gain": [
            "Day 1: Chest + Triceps",
            "Day 2: Back + Biceps",
            "Day 3: Heavy Legs",
            "Day 4: Shoulders + Abs",
            "Day 5: Full Upper Body Pump",
            "Day 6: Legs + Glutes",
            "Day 7: Rest / Stretch"
        ],
        "strength": [
            "Day 1: Squats + Core",
            "Day 2: Bench Press + Push Movements",
            "Day 3: Deadlifts + Posterior Chain",
            "Day 4: Overhead Press + Pull-ups",
            "Day 5: Farmer Walk / Carries",
            "Day 6–7: Rest / Mobility"
        ],
        "beginner": [
            "Day 1: Full Body (Bodyweight)",
            "Day 2: Walk 30 mins",
            "Day 3: Full Body (Light Dumbbells)",
            "Day 4: Rest",
            "Day 5: Full Body (Repeat)",
            "Day 6: Walk + Core",
            "Day 7: Rest"
        ],
        "home": [
            "Pushups / Incline Pushups",
            "Bodyweight Squats",
            "Glute Bridges",
            "Plank 3 x 30 sec",
            "Mountain Climbers",
            "Skipping / High Knees (10–15 min)"
        ]
    }
    return plans.get(goal, [])

# ------------- WORKOUT RECOMMENDATION --------------

@app.route("/workout", methods=["GET", "POST"])
@login_required
def workout():
    plan = None
    goal = None
    if request.method == "POST":
        goal = request.form.get("goal")
        plan = get_workout_plan(goal)
    return render_template("workout.html", goal=goal, plan=plan)


# @app.route('/diet')
# @login_required
# def diet():
#     return render_template('old/diet.html', session=session)

# ------------- DIET RECOMMENDATION -----------------

def get_diet_plan(dtype):
    """Return diet plan list based on diet type."""
    if dtype == "veg":
        return [
            "Breakfast: Oats + Milk + Banana",
            "Mid: Sprouts Salad",
            "Lunch: 2 Roti + Dal + Sabzi + Curd",
            "Snack: Fruit + Nuts",
            "Dinner: Paneer / Soya + Salad"
        ]
    if dtype == "nonveg":
        return [
            "Breakfast: Eggs + Toast + Fruit",
            "Mid: Yogurt + Nuts",
            "Lunch: Chicken + Rice + Veggies",
            "Snack: Whey / Milk + Fruit",
            "Dinner: Fish / Chicken + Salad"
        ]
    if dtype == "fast_fatloss":
        return [
            "Low-carb Breakfast (Egg/Oats)",
            "No sugar drinks / No cold drinks",
            "High protein each meal",
            "Evening: Green tea + nuts",
            "Night: Light dinner (soup/salad + protein)"
        ]
    if dtype == "high_protein":
        return [
            "Every meal: 20–30g protein",
            "Include Paneer/Tofu/Eggs/Chicken",
            "Add Greek Yogurt / Curd daily",
            "Nuts & Seeds between meals"
        ]
    if dtype == "budget":
        return [
            "Chana, Rajma, Dal as main protein",
            "Seasonal fruits only",
            "Simple roti + sabzi + dal pattern",
            "Avoid packaged food & cold drinks"
        ]
    return []

# ------------- DIET RECOMMENDATION ROUTE -------------

@app.route("/diet", methods=["GET", "POST"])
@login_required
def diet():
    dtype = None
    plan = None
    if request.method == "POST":
        dtype = request.form.get("diet_type")
        plan = get_diet_plan(dtype)
    return render_template("diet.html", dtype=dtype, plan=plan)


# @app.route('/planner')
# @login_required
# def planner():
#     return render_template('old/planner.html', session=session)

# ------------- AI STYLE WEEKLY PLANNER -------------

def calculate_bmi(weight, height_cm):
    try:
        h_m = height_cm / 100
        bmi = weight / (h_m * h_m)
    except Exception:
        return None, None

    if bmi < 18.5:
        status = "Underweight"
    elif bmi < 25:
        status = "Healthy"
    elif bmi < 30:
        status = "Overweight"
    else:
        status = "Obese"
    return round(bmi, 1), status

# ------------- WEEKLY PLANNER ROUTE -----------------

@app.route("/planner", methods=["GET", "POST"])
@login_required
def planner():
    info = None
    if request.method == "POST":
        try:
            weight = float(request.form["weight"])
            height = float(request.form["height"])
        except ValueError:
            weight = height = 0.0

        bmi, status = calculate_bmi(weight, height)
        if bmi is not None:
            if status == "Underweight":
                cal = "2200–2600 kcal/day"
                protein = "1.6–2g per kg bodyweight"
            elif status == "Healthy":
                cal = "2000–2400 kcal/day"
                protein = "1.4–1.8g per kg"
            elif status == "Overweight":
                cal = "1500–1900 kcal/day (fat loss focus)"
                protein = "1.6–2g per kg"
            else:
                cal = "1400–1700 kcal/day (strict fat loss)"
                protein = "1.8–2.2g per kg"

            water = "3–4 Litres / day"

            info = {
                "bmi": bmi,
                "status": status,
                "calories": cal,
                "protein": protein,
                "water": water
            }

    return render_template("planner.html", info=info)



# @app.route('/weekly_plan')
# @login_required
# def weekly_plan():
#     uid          = session['user_id']
#     plans        = query("SELECT * FROM workout_plans WHERE user_id=?", (uid,))
#     week_titles  = {p['day_name']: p['workout_type']         for p in plans}
#     workout_plan = {p['day_name']: p['exercises'].split(',') for p in plans}
#     return render_template('old/weekly_plan.html', plans=plans,
#                            week_titles=week_titles, workout_plan=workout_plan,
#                            session=session)

# ================= Weekly Workout Chart =================
@app.route("/weekly_plan")
@login_required
def weekly_plan():
    level = request.args.get("level", session.get("level", "beginner"))

    # SAVE user preference
    session["level"] = level  

    # Titles visible on cards
    week_titles = {
        "Monday": "Chest + Triceps",
        "Tuesday": "Back + Biceps",
        "Wednesday": "Leg Strength",
        "Thursday": "Shoulders + Abs",
        "Friday": "Upper Body Pump",
        "Saturday": "HIIT + Core",
        "Sunday": "Recovery & Stretch"
    }

    # Full exercises for modal
    plans = {
        "beginner": {
    "Monday": [
        "Pushups – 3×10",
        "Incline Pushups – 3×12",
        "Bodyweight Squats – 3×15",
        "Glute Bridge – 3×15",
        "Plank – 30 sec",
        "Dumbbell Chest Press (if available) – 3×12"
    ],

    "Tuesday": [
        "Brisk Walk – 20–30 min",
        "Arm Circles – 2×20",
        "Hip Mobility Routine – 5 min",
        "Child Pose Stretch – 40 sec",
        "Hamstring Stretch – 40 sec"
    ],

    "Wednesday": [
        "Dumbbell Shoulder Press – 3×12",
        "One-Arm Dumbbell Row – 3×12 each side",
        "Bicep Curl – 3×12",
        "Tricep Dips on chair – 3×12",
        "Reverse Snow Angels – 3×15",
        "Front Raise (Light DB) – 3×12"
    ],

    "Thursday": [
        "Rest Day + Light Activity",
        "Cat-Cow Stretch – 10 reps",
        "Cobra Stretch – 40 sec",
        "Neck Mobility – 10 reps",
        "Shoulder Stretch – 30 sec"
    ],

    "Friday": [
        "Lunges – 3×12",
        "Sumo Squats – 3×15",
        "Glute Kickback – 3×15",
        "Calf Raises – 3×20",
        "Wall Sit – 30 sec",
        "Hip Thrust – 3×12",
        "Side Leg Raises – 3×15"
    ],

    "Saturday": [
        "Low Intensity Jog – 5 min",
        "Mountain Climbers – 3×20",
        "Crunches – 3×15",
        "Leg Raises – 3×12",
        "Russian Twist – 3×20",
        "Bicycle Crunch – 3×15"
    ],

    "Sunday": [
        "Yoga Flow – 10 min",
        "Deep Breathing – 5 min",
        "Ankle Mobility – 10 reps",
        "Full Body Stretch – 5 min"
    ]
},

        

        "intermediate": {
    "Monday": [
        "Bench Press – 4×8",
        "Incline Dumbbell Press – 4×10",
        "Pushups – 3×15",
        "Chest Fly (DB) – 3×12",
        "Tricep Dips – 3×12",
        "Overhead Tricep Extension – 3×12"
    ],

    "Tuesday": [
        "Pull-Ups / Assisted – 3×8",
        "Lat Pulldown – 4×10",
        "One-Arm Dumbbell Row – 3×12 each side",
        "Seated Row – 3×12",
        "Bicep Curl – 3×12",
        "Hammer Curl – 3×10"
    ],

    "Wednesday": [
        "Barbell Squat – 4×8",
        "Dumbbell Lunges – 3×12",
        "Leg Press – 4×12",
        "Romanian Deadlift – 3×10",
        "Calf Raises – 4×20",
        "Glute Bridge – 3×15"
    ],

    "Thursday": [
        "Shoulder Press – 4×10",
        "Lateral Raise – 3×15",
        "Front Raise – 3×12",
        "Reverse Fly – 3×12",
        "Plank – 45 sec",
        "Hanging Knee Raise – 3×12"
    ],

    "Friday": [
        "Upper Body Circuit",
        "Pushups – 20 reps",
        "Bent Over Row – 15 reps",
        "Arnold Press – 12 reps",
        "Curls – 12 reps",
        "Repeat circuit × 3"
    ],

    "Saturday": [
        "HIIT: 20s ON / 20s OFF × 10 rounds",
        "Mountain Climbers",
        "Jump Squats",
        "Burpees",
        "High Knees",
        "Core Finisher: Leg Raises – 3×12"
    ],

    "Sunday": [
        "Recovery Walk – 20 min",
        "Full Body Stretch – 10 min",
        "Foam Roll (if available) – 5 min",
        "Light Yoga Flow – 8 min"
    ]
},

       "advanced": {
    "Monday": [
        "Heavy Bench Press – 5×5",
        "Weighted Dips – 4×6",
        "Incline Barbell Press – 4×8",
        "Cable Fly – 3×12",
        "Close-Grip Bench – 3×8",
        "Skull Crushers – 3×10",
        "Pushups Burnout – max reps"
    ],

    "Tuesday": [
        "Deadlift – 5×5",
        "Weighted Pull-Ups – 4×6",
        "Barbell Row – 4×8",
        "T-Bar Row – 3×10",
        "Face Pulls – 3×15",
        "Barbell Curl – 3×10",
        "Alternating DB Curl – 3×12"
    ],

    "Wednesday": [
        "Back Squat – 5×5",
        "Bulgarian Split Squat – 4×8",
        "Romanian Deadlift – 4×8",
        "Leg Extension – 3×15",
        "Hamstring Curl – 3×15",
        "Calf Raises – 4×20",
        "Glute Hip Thrust – 4×10"
    ],

    "Thursday": [
        "Overhead Press – 5×5",
        "Arnold Press – 4×10",
        "Lateral Raise – 4×15",
        "Rear Delt Row – 3×12",
        "Barbell Shrugs – 3×12",
        "Hanging Leg Raise – 4×12",
        "Weighted Plank – 45 sec"
    ],

    "Friday": [
        "Push-Pull Hybrid Volume",
        "Incline DB Press – 4×12",
        "Chin-Ups – 4×10",
        "Cable Row – 3×12",
        "Side Lateral Raise – 3×15",
        "Concentration Curl – 3×12",
        "Tricep Rope Pushdown – 3×15"
    ],

    "Saturday": [
        "Conditioning Day",
        "HIIT (20 min)",
        "Sled Push or Sprint – 6 rounds",
        "Burpees – 3×15",
        "Core Circuit: Plank, Russian Twist, Toe Touch – 3 rounds",
        "Farmer Carry – 3×45 sec"
    ],

    "Sunday": [
        "Active Recovery",
        "Slow Yoga 15 min",
        "Mobility Sequence – 10 min",
        "Light Walk / Cycling – 20 min"
    ]
}

    }

    return render_template(
        "weekly_plan.html",
        level=level,
        week_titles=week_titles,
        workout_plan=plans[level]
    )



# @app.route('/assistant')
# @login_required
# def assistant():
#     return render_template('old/assistant.html', session=session)

# ===================== SAVAGE AI FITNESS COACH =======================
from difflib import SequenceMatcher

def update_context(ctx, text):
    """User ka data (weight/height/goal/place/level) memory me store kare."""
    t = text.lower()

    # weight detect (e.g. 70kg)
    for part in t.split():
        if "kg" in part:
            try:
                w = float(part.replace("kg", ""))
                ctx["weight"] = w
            except:
                pass

    # height detect (e.g. 170cm)
    for part in t.split():
        if "cm" in part:
            try:
                h = float(part.replace("cm", ""))
                ctx["height"] = h
            except:
                pass

    # goal detect
    if any(w in t for w in ["fat", "cut", "shred"]):
        ctx["goal"] = "fat_loss"
    if any(w in t for w in ["muscle", "bulk", "size"]):
        ctx["goal"] = "muscle_gain"
    if any(w in t for w in ["strength", "strong", "power"]):
        ctx["goal"] = "strength"

    # place detect
    if "home" in t or "no gym" in t:
        ctx["place"] = "home"
    if "gym" in t:
        ctx["place"] = "gym"

    # level detect
    if "beginner" in t or "new" in t or "start" in t:
        ctx["level"] = "beginner"
    if "intermediate" in t or "average" in t:
        ctx["level"] = "intermediate"
    if "advanced" in t or "pro" in t or "beast" in t:
        ctx["level"] = "advanced"

    return ctx


def build_plan(ctx):
    """Context ke base par proper savage plan banaye."""
    w = ctx.get("weight")
    h = ctx.get("height")
    goal = ctx.get("goal")
    place = ctx.get("place")
    level = ctx.get("level")

    lines = []

    # BMI / calories
    if w and h:
        h_m = h / 100
        bmi = round(w / (h_m * h_m), 2)
        lines.append(f"📊 BMI = {bmi}")
        if bmi < 18.5:
            lines.append("Status: Underweight — bulk clean karo, bhai.")
            calories = f"{int(w*35)}–{int(w*40)} kcal/day"
        elif bmi < 25:
            lines.append("Status: Normal — perfect time to chase strength & muscle.")
            calories = f"{int(w*30)}–{int(w*33)} kcal/day"
        else:
            lines.append("Status: Overweight — fat cut kare bina excuse ke.")
            calories = f"{int(w*22)}–{int(w*26)} kcal/day"

        protein = f"{round(w*1.8)} g protein/day"
        water   = "3–4L water/day"
        lines.append(f"🔥 Calories Target: {calories}")
        lines.append(f"💪 Protein Target: {protein}")
        lines.append(f"💧 Water Target: {water}")

    # Workout plan
    if goal:
        lines.append("──────── WORKOUT PLAN ────────")
        gym = (place == "gym")
        if goal == "fat_loss":
            if gym:
                lines += [
                    "Day 1: HIIT + Full Body Circuit",
                    "Day 2: Incline walk 30 min + Core",
                    "Day 3: Weights (Upper Body) + 15 min cardio",
                    "Day 4: Rest / Light walk",
                    "Day 5: Legs + 10 min stair master",
                    "Day 6: HIIT 20 min + Abs",
                    "Day 7: Stretching / Mobility"
                ]
            else:
                lines += [
                    "Day 1: HIIT (Burpees, Jumping Jacks, Mountain Climbers)",
                    "Day 2: Brisk walk 40 min",
                    "Day 3: Home Full Body (Pushup/Squat/Lunges/Plank)",
                    "Day 4: Rest + Stretching",
                    "Day 5: HIIT 15–20 min",
                    "Day 6: Core + Walk 30 min",
                    "Day 7: Yoga / Mobility"
                ]
        elif goal == "muscle_gain":
            if gym:
                lines += [
                    "Day 1: Push (Chest+Shoulder+Triceps)",
                    "Day 2: Pull (Back+Biceps)",
                    "Day 3: Legs (Quads+Hams+Glutes)",
                    "Day 4: Rest / Walk",
                    "Day 5: Push (Heavier)",
                    "Day 6: Pull (Heavy + Rows)",
                    "Day 7: Legs + Calves"
                ]
            else:
                lines += [
                    "Day 1: Pushups variations + Dips / Chair dips",
                    "Day 2: Squats + Lunges + Glute Bridge",
                    "Day 3: Pike pushups + Plank",
                    "Day 4: Rest / Walk",
                    "Day 5: Repeat Day1",
                    "Day 6: Repeat Day2",
                    "Day 7: Light stretching"
                ]
        elif goal == "strength":
            lines += [
                "Day 1: Heavy Squat + Core",
                "Day 2: Heavy Bench + Push accessories",
                "Day 3: Rest / Mobility",
                "Day 4: Heavy Deadlift + Rows",
                "Day 5: Overhead Press + Pullups",
                "Day 6: Accessories / Weak point training",
                "Day 7: Full recovery"
            ]

    # Diet hints
    if goal:
        lines.append("──────── DIET CHECKLIST ────────")
        if goal == "fat_loss":
            lines += [
                "• Roti 3 se zyada mat, rice quantity control.",
                "• Har meal me protein fix (Egg/Paneer/Chicken/Curd).",
                "• Cold drink, chips, bakery = straight ban 🚫"
            ]
        else:
            lines += [
                "• Har meal me solid protein (Egg/Paneer/Chicken/Tofu).",
                "• Ghar ka normal khana, junk minimal.",
                "• Soya/Paneer/Curd/Chana as daily add-ons."
            ]

    if not lines:
        lines.append("Pehle apna weight, height, goal bata — phir main full plan phod ke dunga 💥")

    lines.append("\nNo excuses now. Start today, not ‘kal se’. 🔥")
    return "\n".join(lines)


def savage_ai_reply(ctx, text):
    t = text.lower().strip()

    # reset
    if "reset" in t or "clear" in t:
        ctx.clear()
        return ctx, "Context clear kar diya. Ab fresh se start karte hain. Weight, height, goal bata 💪"

    # greetings
    if any(word in t for word in ["hello","hi","hey","yo","namaste"]):
        if not ctx:
            return ctx, "Sun champion 👊 — weight (kg), height (cm) aur goal (fat loss / muscle / strength) bata."
        else:
            return ctx, "Bata ab aage kya scene hai? Diet, workout ya progress?"

    # update context from message
    ctx = update_context(ctx, t)

    # quick Q/A shortcuts
    if "bmi" in t and (ctx.get("weight") and ctx.get("height")):
        return ctx, build_plan(ctx)

    if "diet" in t and ctx.get("goal"):
        return ctx, build_plan(ctx)

    if "workout" in t or "plan" in t or "routine" in t:
        return ctx, build_plan(ctx)

    # generic: if enough info, give full plan
    if ctx.get("weight") and ctx.get("height") and ctx.get("goal"):
        return ctx, build_plan(ctx)

    # else ask for missing pieces
    missing = []
    if not ctx.get("weight"):
        missing.append("weight (kg)")
    if not ctx.get("height"):
        missing.append("height (cm)")
    if not ctx.get("goal"):
        missing.append("goal (fat loss / muscle / strength)")
    if missing:
        return ctx, "Thoda clear bata 👉 " + ", ".join(missing) + " — phir pura savage plan dunga."

    # fallback
    return ctx, "Fitness ke bare me kuch bhi puch — fat loss, muscle, diet, BMI. Seedha bol, घुमा मत 🙂"

#=============== assistant =======================
@app.route("/assistant", methods=["GET", "POST"])
@login_required
def assistant():
    # session-based memory
    chat = session.get("chat_history", [])
    ctx  = session.get("coach_ctx", {})

    if request.method == "POST":
        user_msg = request.form.get("question", "").strip()
        if user_msg:
            # user msg add karo
            chat.append({"sender": "user", "text": user_msg})

            # ai reply
            ctx, ai_text = savage_ai_reply(ctx, user_msg)
            chat.append({"sender": "ai", "text": ai_text})

            # save back to session
            session["chat_history"] = chat
            session["coach_ctx"] = ctx

    return render_template("assistant.html", chat=chat)



# @app.route('/today_workout')
# @login_required
# def today_workout():
#     return render_template('old/today_workout.html', session=session)

# ================= Today Workout (auto day) =================
def today_schedule():
    """Har din ka simple gym split (example)."""
    return {
        "Monday": "Chest + Triceps 🔥 (Bench Press, Pushups, Cable Flyes)",
        "Tuesday": "Back + Biceps 💪 (Lat Pulldown, Rows, Curls)",
        "Wednesday": "Leg Day 🦵 (Squats, Lunges, Leg Press)",
        "Thursday": "Shoulders + Abs 🧠 (Shoulder Press, Lateral Raises, Planks)",
        "Friday": "Full Upper Body ⚡ (Compound + Isolation Mix)",
        "Saturday": "Cardio + Core ❤️‍🔥 (Treadmill / Cycling + Abs Circuit)",
        "Sunday": "Active Rest 😴 (Walk, Stretching, Mobility)"
    }


@app.route("/today_workout")
@login_required
def today_workout():

    import datetime
    today = datetime.datetime.now().strftime("%A")

    # Your full workout dictionary defined earlier
    from workout_data import workouts   # where beginner/intermediate/advanced stored

    beginner = workouts["beginner"][today]
    intermediate = workouts["intermediate"][today]
    advanced = workouts["advanced"][today]

    return render_template(
        "today_workout.html",
        today=today,
        beginner=beginner,
        intermediate=intermediate,
        advanced=advanced
    )



# @app.route('/calorie_calc')
# @login_required
# def calorie_calc():
#     return render_template('old/calorie_calc.html', session=session)

# ================= Calories + Protein Calculator =================

@app.route("/calorie_calc", methods=["GET","POST"])
@login_required
def calorie_calc():

    if request.method == "POST":
        weight = float(request.form['weight'])

        # Height Input Mode
        mode = request.form['mode']

        # --- CM Input ---
        if mode == "cm":
            height_cm = float(request.form['height_cm'])
            height_m = height_cm / 100   # convert → meters

        # --- FEET + INCH Input ---
        else:
            feet = float(request.form['height_ft'])
            inch = float(request.form['height_in'])
            height_m = ((feet * 12) + inch) * 0.0254   # convert → meters

        # CALCULATIONS
        bmi = round(weight / (height_m * height_m), 2)
        calories = round(weight * 30)        # avg maintenance kcal
        protein = round(weight * 1.8)        # athlete recommended (gm/day)

        return render_template("calorie_calc.html",
                               bmi=bmi, cal=calories, pro=protein,
                               weight=weight)
    
    return render_template("calorie_calc.html")



# @app.route('/strength')
# @login_required
# def strength():
#     return render_template('old/strength.html', session=session)

# ================= STRENGTH TEST =================

def evaluate_strength(pushups, squats, plank):
    score = 0

    # Pushups (Max considered = 40)
    score += min(pushups, 40) * 0.4 

    # Squats (Max considered = 60)
    score += min(squats, 60) * 0.3

    # Plank seconds (Max considered = 120 sec)
    score += min(plank, 120) * 0.3
    
    percentage = round(score, 2)

    if percentage < 40:
        level = "Beginner 🟢"
    elif percentage < 75:
        level = "Intermediate 🟡"
    else:
        level = "Beast Mode 🔥"

    return percentage, level

# ------------- STRENGTH TEST ROUTE -----------------

@app.route("/strength", methods=["GET","POST"])
@login_required
def strength():
    result = None
    if request.method == "POST":
        pushups = int(request.form["pushups"])
        squats  = int(request.form["squats"])
        plank   = int(request.form["plank"])
        
        result = evaluate_strength(pushups, squats, plank)

    return render_template("strength.html", result=result)


# @app.route('/progress')
# @login_required
# def progress():
#     return render_template('old/progress.html', session=session)

# ================= Progress Graph & Tracker =================
@app.route("/progress", methods=["GET","POST"])
@login_required
def progress():

    uid = session["user_id"]

    # SAVE ENTRY
    if request.method == "POST":
        weight_str = request.form.get('weight', '').strip()
        if weight_str:
            try:
                weight = float(weight_str)
                today = datetime.today().strftime("%Y-%m-%d")

                query(
                    "INSERT INTO progress(user_id, weight, date) VALUES (?,?,?)",
                    (uid, weight, today),
                    commit=True
                )

            except ValueError:
                pass

    # LOAD DATA
    rows = query(
        "SELECT date, weight FROM progress WHERE user_id=? ORDER BY date",
        (uid,)
    )

    dates = [r["date"] for r in rows]
    weights = [r["weight"] for r in rows]

    progress_pct = None
    if len(weights) >= 2 and weights[0] != 0:
        start = weights[0]
        latest = weights[-1]
        progress_pct = round(((latest - start) / start) * 100, 2)

    return render_template(
        "progress.html",
        weights=weights,
        dates=dates,
        progress=progress_pct
    )


# ================= HOME WORKOUT =================

@app.route("/home_workout", methods=["GET", "POST"])
@login_required
def home_workout():

    # Default level
    level = "beginner"

    if request.method == "POST":
        level = request.form.get("level", "beginner").lower()

    HOME_WORKOUTS = {
        "beginner": [
            "Pushups 3x10",
            "Bodyweight Squats 3x15",
            "Glute Bridge 3x15",
            "Plank 3x30 sec",
            "Jumping Jacks 3x20"
        ],
        "intermediate": [
            "Diamond Pushups 4x12",
            "Walking Lunges 4x15",
            "Pike Pushups 4x10",
            "Plank 4x45 sec",
            "Mountain Climbers 4x30 sec"
        ],
        "advanced": [
            "Clap Pushups 5x15",
            "Jump Squats 5x20",
            "Bulgarian Split Squats 4x12",
            "Handstand Hold 4x30 sec",
            "Burpees 5x20"
        ]
    }

    workouts = HOME_WORKOUTS.get(level, HOME_WORKOUTS["beginner"])

    return render_template(
        "home_workout.html",
        level=level.capitalize(),
        workouts=workouts
    )
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
