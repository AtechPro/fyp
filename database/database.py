from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def get_id(self):
        return str(self.userid)
    
    def is_admin(self):
        return self.role == 1

class Feedback(db.Model):
    __tablename__ = 'feedback'
    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    feedback_title = db.Column(db.Text, nullable=False)
    feedback_desc = db.Column(db.Text, nullable=True)
    time = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship('User', backref=db.backref('feedback', lazy=True))


# Other CRUD 
"""

class BackupRestore(db.Model):
    __tablename__ = 'backup_restore'
    backup_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    backup_name = db.Column(db.String(50), nullable=False)
    backup_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship('User', backref=db.backref('backups', lazy=True))


class AutomationRule(db.Model):
    __tablename__ = 'automation_rules'
    rule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_name = db.Column(db.String(50), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    rule_condition = db.Column(db.Text, nullable=False)
    action = db.Column(db.Text, nullable=False)
    user = db.relationship('User', backref=db.backref('automation_rules', lazy=True))


class TimerScheduler(db.Model):
    __tablename__ = 'timer_scheduler'
    timer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    timer_name = db.Column(db.String(50), nullable=False)
    schedule_time = db.Column(db.DateTime, nullable=False)
    action = db.Column(db.Text, nullable=False)
    user = db.relationship('User', backref=db.backref('timers', lazy=True))


class ZoneManagement(db.Model):
    __tablename__ = 'zone_management'
    zone_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    zone_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    user = db.relationship('User', backref=db.backref('zones', lazy=True))



class Device(db.Model):
    __tablename__ = 'devices'
    device_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    mac = db.Column(db.String(17), nullable=False, unique=True)
    ip = db.Column(db.String(15), nullable=False, unique=True)
    user = db.relationship('User', backref=db.backref('devices', lazy=True))


"""
