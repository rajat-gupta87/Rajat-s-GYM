"""
Dashboard & Calendar Blueprint
Main user-facing routes after login.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from functools import wraps

dash_bp = Blueprint('dash', __name__)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


@dash_bp.route('/dashboard')
@login_required
def user_dashboard():
    from run import query, get_current_user
    uid       = session['user_id']
    today     = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today_day = datetime.now().strftime('%A')

    today_plan    = query("SELECT * FROM workout_plans WHERE user_id=? AND day_name=?", (uid, today_day), one=True)
    yesterday_log = query("SELECT * FROM workout_logs WHERE user_id=? AND date=?",      (uid, yesterday), one=True)
    today_log     = query("SELECT * FROM workout_logs WHERE user_id=? AND date=?",      (uid, today),     one=True)
    all_plans     = query("SELECT * FROM workout_plans WHERE user_id=?",                (uid,))
    recent_logs   = query("SELECT * FROM workout_logs WHERE user_id=? ORDER BY date DESC LIMIT 7", (uid,))
    current_user  = get_current_user()

    return render_template('dashboard.html',
                           today_plan=today_plan,
                           yesterday_log=yesterday_log,
                           today_log=today_log,
                           all_plans=all_plans,
                           recent_logs=recent_logs,
                           today=today,
                           today_day=today_day,
                           current_user=current_user)


@dash_bp.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar_view.html')


@dash_bp.route('/api/calendar/log/<date>')
@login_required
def get_log(date):
    from run import query
    uid  = session['user_id']
    log  = query("SELECT * FROM workout_logs WHERE user_id=? AND date=?", (uid, date), one=True)
    try:
        plan = query("SELECT * FROM workout_plans WHERE user_id=? AND day_name=?",
                     (uid, datetime.strptime(date, '%Y-%m-%d').strftime('%A')), one=True)
    except Exception:
        plan = None

    return jsonify({
        'log': {'id': log['id'], 'notes': log['notes'],
                'completed': bool(log['completed']), 'workout_type': log['workout_type']} if log else None,
        'plan': {'day_name': plan['day_name'], 'workout_type': plan['workout_type'],
                 'exercises': plan['exercises']} if plan else None
    })


@dash_bp.route('/api/calendar/save', methods=['POST'])
@login_required
def save_log():
    from run import query
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


@dash_bp.route('/api/logs/monthly')
@login_required
def monthly_logs():
    from run import query
    uid  = session['user_id']
    logs = query("SELECT date,completed,workout_type FROM workout_logs WHERE user_id=?", (uid,))
    return jsonify([{'date': l['date'], 'completed': bool(l['completed']),
                     'workout_type': l['workout_type']} for l in logs])
