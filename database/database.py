from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(20), nullable=False)

    # Relationship with Feedback and Device
    feedback = db.relationship('Feedback', cascade='all, delete-orphan', backref='user', lazy=True)
    devices = db.relationship('Device', cascade='all, delete-orphan', backref='user', lazy=True)

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


class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False)
    sensor_key = db.Column(db.String(50), nullable=False)
    sensor_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='online')
    last_seen = db.Column(db.DateTime, default=datetime.now)

    # Relationship with Device
    device = db.relationship('Device', backref=db.backref('sensor_list', cascade='all, delete-orphan', lazy=True))

    def __repr__(self):
        return f"<Sensor {self.sensor_key} of Device {self.device_id}>"


class Device(db.Model):
    __tablename__ = 'devices'

    device_id = db.Column(db.String(50), primary_key=True)
    status = db.Column(db.Boolean, default=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='CASCADE'), nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)

    def add_sensor(self, sensor_key, sensor_type, value=None, status="online"):
        """Helper method to add a sensor to the device."""
        new_sensor = Sensor(
            device_id=self.device_id,
            sensor_key=sensor_key,
            sensor_type=sensor_type,
            value=str(value),
            status=status,
            last_seen=datetime.now()
        )
        db.session.add(new_sensor)

class Zone(db.Model):
    __tablename__ = 'zones'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200), nullable=True)
    sensors = db.relationship('ZoneSensor', backref='zone', cascade='all, delete-orphan', lazy=True)

class ZoneSensor(db.Model):
    __tablename__ = 'zone_sensors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id', ondelete='CASCADE'), nullable=False)
