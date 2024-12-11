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

    # Attributes
    device_id = db.Column(db.String(50), primary_key=True)  # Unique device identifier
    ip_address = db.Column(db.String(15), nullable=False)  # Device IP
    status = db.Column(db.String(10), default="offline")  # Device status (online/offline)
    last_seen = db.Column(db.DateTime, nullable=True)  # Last time device reported
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=True)  # Foreign key to User

    # Relationships
    user = db.relationship('User', backref=db.backref('devices', lazy=True))  # Link to the User model
    sensors = db.relationship('Sensor', backref='device', lazy=True)  # Link to associated sensors

    def __repr__(self):
        return f"<Device {self.device_id}, Status: {self.status}, Last Seen: {self.last_seen}>"

class Sensor(db.Model):
    __tablename__ = 'sensors'

    # Attributes
    sensor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Unique sensor identifier
    sensor_type = db.Column(db.String(50), nullable=False)  # Type of sensor (e.g., temperature, humidity)
    sensor_name = db.Column(db.String(50), nullable=True)  # User-defined name for the sensor
    status = db.Column(db.String(10), default="offline")  # Sensor status
    last_seen = db.Column(db.DateTime, nullable=True)  # Last time sensor reported
    value = db.Column(db.String(255), nullable=True)  # Optional: Store the last reported value

    # Relationships
    device_id = db.Column(db.String(50), db.ForeignKey('devices.device_id'), nullable=False)  # Link to a device

    def __repr__(self):
        return f"<Sensor {self.sensor_id}, Type: {self.sensor_type}, Device: {self.device_id}>"

