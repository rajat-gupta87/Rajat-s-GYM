"""
Workout Blueprint
Serves user workout pages and all preserved original templates.
"""
from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps

workout_bp = Blueprint('workout', __name__)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


@workout_bp.route('/workout')
@login_required
def workout():
    from run import query
    plans = query("SELECT * FROM workout_plans WHERE user_id=?", (session['user_id'],))
    return render_template('old/workout.html', plans=plans, session=session)


@workout_bp.route('/diet')
@login_required
def diet():
    return render_template('old/diet.html', session=session)


@workout_bp.route('/planner')
@login_required
def planner():
    return render_template('old/planner.html', session=session)


@workout_bp.route('/weekly_plan')
@login_required
def weekly_plan():
    from run import query
    uid   = session['user_id']
    plans = query("SELECT * FROM workout_plans WHERE user_id=?", (uid,))
    week_titles  = {p['day_name']: p['workout_type']          for p in plans}
    workout_plan = {p['day_name']: p['exercises'].split(',')  for p in plans}
    return render_template('old/weekly_plan.html', plans=plans,
                           week_titles=week_titles, workout_plan=workout_plan, session=session)


@workout_bp.route('/assistant')
@login_required
def assistant():
    return render_template('old/assistant.html', session=session)


@workout_bp.route('/today_workout')
@login_required
def today_workout():
    return render_template('old/today_workout.html', session=session)


@workout_bp.route('/calorie_calc')
@login_required
def calorie_calc():
    return render_template('old/calorie_calc.html', session=session)


@workout_bp.route('/strength')
@login_required
def strength():
    return render_template('old/strength.html', session=session)


@workout_bp.route('/progress')
@login_required
def progress():
    return render_template('old/progress.html', session=session)


@workout_bp.route('/motivation')
@login_required
def motivation():
    return render_template('old/quotes.html', session=session)


@workout_bp.route('/tracker')
@login_required
def tracker():
    return render_template('old/progress.html', session=session)
