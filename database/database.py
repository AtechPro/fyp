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

class Report(db.Model):
    __tablename__ = 'reports'
    report_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    username = db.Column(db.String(20), nullable=False)
    report_title = db.Column(db.Text, nullable=False)
    report_desc = db.Column(db.Text, nullable=True)
    time = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('reports', lazy=True))

# You can add other models like Scheduler, Automate, Dashboard here as needed
"""
class Device(db.Model):
    __tablename__ = 'devices'
    device_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    mac = db.Column(db.String(17), nullable=False, unique=True)
    ip = db.Column(db.String(15), nullable=False, unique=True)

    user = db.relationship('User', backref=db.backref('devices', lazy=True))

"""
