"""
Admin Blueprint
Protected routes for gym management monitoring.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, session
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(fn):
    """Decorator: only admin role may access."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    from run import query
    total_users  = query("SELECT COUNT(*) as c FROM users WHERE role='user'", one=True)['c']
    active_users = query("SELECT COUNT(*) as c FROM login_activity WHERE is_active=1", one=True)['c']
    users        = query("SELECT * FROM users WHERE role='user'")
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
