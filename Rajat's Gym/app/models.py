"""
SmartGym Database Models
Uses Flask-SQLAlchemy ORM with full PostgreSQL support.
"""
from datetime import datetime

try:
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import UserMixin
    from . import db

    class User(UserMixin, db.Model):
        __tablename__ = 'users'
        id               = db.Column(db.Integer, primary_key=True)
        name             = db.Column(db.String(120), nullable=False)
        email            = db.Column(db.String(150), unique=True, nullable=False)
        password         = db.Column(db.String(256), nullable=False)
        role             = db.Column(db.String(20), default='user')
        age              = db.Column(db.Integer)
        gender           = db.Column(db.String(15))
        height           = db.Column(db.Float)     # cm
        weight           = db.Column(db.Float)     # kg
        goal             = db.Column(db.String(60))
        experience_level = db.Column(db.String(30))
        workout_days     = db.Column(db.Integer, default=3)
        bmi              = db.Column(db.Float)
        assigned_plan    = db.Column(db.Text)
        created_at       = db.Column(db.DateTime, default=datetime.utcnow)

        # Relationships
        login_activities = db.relationship('LoginActivity', backref='user', lazy=True, cascade='all, delete')
        workout_plans    = db.relationship('WorkoutPlan',   backref='user', lazy=True, cascade='all, delete')
        workout_logs     = db.relationship('WorkoutLog',    backref='user', lazy=True, cascade='all, delete')

        def __repr__(self):
            return f'<User {self.email}>'

        @property
        def bmi_category(self):
            if not self.bmi:
                return 'Unknown'
            if self.bmi < 18.5:
                return 'Underweight'
            elif self.bmi < 25:
                return 'Normal'
            elif self.bmi < 30:
                return 'Overweight'
            return 'Obese'


    class LoginActivity(db.Model):
        __tablename__ = 'login_activity'
        id          = db.Column(db.Integer, primary_key=True)
        user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        login_time  = db.Column(db.DateTime, default=datetime.utcnow)
        logout_time = db.Column(db.DateTime, nullable=True)
        is_active   = db.Column(db.Boolean, default=True)
        ip_address  = db.Column(db.String(50), nullable=True)

        def __repr__(self):
            return f'<LoginActivity user={self.user_id} active={self.is_active}>'


    class WorkoutPlan(db.Model):
        __tablename__ = 'workout_plans'
        id           = db.Column(db.Integer, primary_key=True)
        user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        day_name     = db.Column(db.String(20))   # "Monday"
        workout_type = db.Column(db.String(80))   # "Push Day"
        exercises    = db.Column(db.Text)          # CSV of exercises

        def __repr__(self):
            return f'<WorkoutPlan {self.day_name} – {self.workout_type}>'

        @property
        def exercise_list(self):
            return [e.strip() for e in (self.exercises or '').split(',') if e.strip()]


    class WorkoutLog(db.Model):
        __tablename__ = 'workout_logs'
        id           = db.Column(db.Integer, primary_key=True)
        user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
        date         = db.Column(db.String(20))        # YYYY-MM-DD
        workout_type = db.Column(db.String(80))
        notes        = db.Column(db.Text)
        completed    = db.Column(db.Boolean, default=False)
        created_at   = db.Column(db.DateTime, default=datetime.utcnow)

        def __repr__(self):
            return f'<WorkoutLog {self.date} completed={self.completed}>'
        
    class Progress(db.Model):
        __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), default=lambda: datetime.utcnow().strftime("%Y-%m-%d"))

    user = db.relationship("User", backref=db.backref("progress_entries", lazy=True))

    def __repr__(self):
        return f"<Progress {self.date} - {self.weight}kg>"
    
except ImportError:
    # Stub classes for when Flask-SQLAlchemy is not installed
    class User: pass
    class LoginActivity: pass
    class WorkoutPlan: pass
    class WorkoutLog: pass
    class Progress: pass