"""
Authentication Blueprint
Handles: register, login, logout, admin login/logout
"""
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_db():
    """Return the db interface (sqlite or SQLAlchemy)."""
    try:
        from app import db
        return 'sqlalchemy', db
    except Exception:
        return 'sqlite', None


def _mark_logout():
    from flask import session as s
    from run import query
    act_id = s.get('login_activity_id')
    if act_id:
        query("UPDATE login_activity SET logout_time=?, is_active=0 WHERE id=?",
              (datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), act_id), commit=True)


# ─── Routes ───────────────────────────────────────────────────────────────────

@auth_bp.route('/')
def landing():
    return render_template('landing.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        from run import query, assign_plan
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

        if query("SELECT id FROM users WHERE email=?", (email,), one=True):
            flash('Email already registered.', 'danger')
            return render_template('register.html')

        bmi = round(weight / ((height / 100) ** 2), 1) if height and weight else None

        uid = query(
            "INSERT INTO users(name,email,password,role,age,gender,height,weight,goal,"
            "experience_level,workout_days,bmi) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (name, email, generate_password_hash(password), 'user',
             age, gender, height, weight, goal, exp, w_days, bmi),
            commit=True
        )
        assign_plan(uid, goal, exp)
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from run import query
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = query("SELECT * FROM users WHERE email=? AND role='user'", (email,), one=True)

        if user and check_password_hash(user['password'], password):
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['role']      = 'user'
            act_id = query(
                "INSERT INTO login_activity(user_id,login_time,is_active) VALUES(?,?,1)",
                (user['id'], datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')), commit=True
            )
            session['login_activity_id'] = act_id
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    _mark_logout()
    session.clear()
    return redirect(url_for('login'))


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        from run import query
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        admin    = query("SELECT * FROM users WHERE email=? AND role='admin'", (email,), one=True)

        if admin and check_password_hash(admin['password'], password):
            session['user_id']   = admin['id']
            session['user_name'] = admin['name']
            session['role']      = 'admin'
            act_id = query(
                "INSERT INTO login_activity(user_id,login_time,is_active) VALUES(?,?,1)",
                (admin['id'], datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')), commit=True
            )
            session['login_activity_id'] = act_id
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('admin_login.html')


@auth_bp.route('/admin/logout')
def admin_logout():
    _mark_logout()
    session.clear()
    return redirect(url_for('admin_login'))
