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

class Device(db.Model):
    __tablename__ = 'devices'
    device_id = db.Column(db.String(50), primary_key=True) 
    ip_address = db.Column(db.String(15), nullable=False)  
    status = db.Column(db.String(10), default="offline")  
    last_seen = db.Column(db.DateTime, nullable=True)  
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=True)  

    # Establish a relationship to the User model
    user = db.relationship('User', backref=db.backref('devices', lazy=True))

class Sensor(db.Model):
    __tablename__ = 'sensors'
    sensor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sensor_type = db.Column(db.String(50), nullable=False)  
    sensor_name = db.Column(db.String(50), nullable=True)  
    status = db.Column(db.String(10), default="offline")  
    last_seen = db.Column(db.DateTime, nullable=True)  
    device_id = db.Column(db.String(50), db.ForeignKey('devices.device_id'), nullable=False)

    # Relationship to Device
    device = db.relationship('Device', backref=db.backref('sensors', lazy=True))
