from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

# User Model
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    userid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    session_id = db.Column(db.String(100), nullable=True)  # Add session_id field

    # Relationships
    feedback = db.relationship('Feedback', cascade='all, delete-orphan', backref='user', lazy=True)
    devices = db.relationship('Device', cascade='all, delete-orphan', backref='user', lazy=True)
    sensors = db.relationship('Sensor', cascade='all, delete-orphan', backref='user', lazy=True)
    zones = db.relationship('Zone', cascade='all, delete-orphan', backref='user', lazy=True)
    automation_rules = db.relationship('AutomationRule', cascade='all, delete-orphan', backref='user', lazy=True)


    def get_id(self):
        return str(self.userid)

    def is_admin(self):
        return self.role == 1


# Feedback Model
class Feedback(db.Model):
    __tablename__ = 'feedback'
    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    feedback_title = db.Column(db.Text, nullable=False)
    feedback_desc = db.Column(db.Text, nullable=True)
    time = db.Column(db.DateTime, default=db.func.current_timestamp())


# SensorType Model (New)
class SensorType(db.Model):
    __tablename__ = 'sensor_types'

    id = db.Column(db.Integer, primary_key=True)
    type_key = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'temperature', 'humidity'
    display_name = db.Column(db.String(100), nullable=False)  # e.g., 'Temperature Sensor'
    unit = db.Column(db.String(20), nullable=True)  # e.g., '°C', '%'
    states = db.Column(db.JSON, nullable=True)  # e.g., ['OPEN', 'CLOSED'] for status sensors

    def __repr__(self):
        return f"<SensorType {self.type_key}>"


# Sensor Model
class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False)
    sensor_key = db.Column(db.String(50), nullable=False)
    sensor_type_id = db.Column(db.Integer, db.ForeignKey('sensor_types.id'), nullable=False)  # Foreign key to SensorType
    value = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='online')
    last_seen = db.Column(db.DateTime, default=datetime.now)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='CASCADE'), nullable=False)
    

    # Relationships
    device = db.relationship('Device', backref=db.backref('sensor_list', cascade='all, delete-orphan', lazy=True))
    sensor_type = db.relationship('SensorType', backref=db.backref('sensors', lazy=True))
    automation_rules = db.relationship('AutomationRule', backref=db.backref('sensor', lazy=True), cascade='all, delete-orphan')
    def __repr__(self):
        return f"<Sensor {self.sensor_key} of Device {self.device_id}>"


# Device Model
class Device(db.Model):
    __tablename__ = 'devices'

    device_id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(100), nullable=True)  # New field for device title
    description = db.Column(db.Text, nullable=True)  # New field for device description
    status = db.Column(db.Boolean, default=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='CASCADE'), nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)

    def add_sensor(self, sensor_key, sensor_type_id, value=None, status="online"):
        """Helper method to add a sensor to the device."""
        new_sensor = Sensor(
            device_id=self.device_id,
            sensor_key=sensor_key,
            sensor_type_id=sensor_type_id,
            value=str(value),
            status=status,
            last_seen=datetime.now(),
            userid=self.userid
        )
        db.session.add(new_sensor)

    def __repr__(self):
        return f"<Device {self.device_id} - {self.title}>"


def add_sensor_to_device(device_id, sensor_key, sensor_type_id, value=None, status="online"):
    device = Device.query.filter_by(device_id=device_id).first()
    if device:
        new_sensor = Sensor(
            device_id=device.device_id,
            sensor_key=sensor_key,
            sensor_type_id=sensor_type_id,
            value=str(value),
            status=status,
            last_seen=datetime.now(),
            userid=device.userid
        )
        db.session.add(new_sensor)
        db.session.commit()  # Commit the session to save changes to the database
    else:
        print(f"Device with id {device_id} not found")


# Zone Model
class Zone(db.Model):
    __tablename__ = 'zones'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200), nullable=True)
    sensors = db.relationship('ZoneSensor', backref='zone', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f"<Zone {self.name}>"


# ZoneSensor Model
class ZoneSensor(db.Model):
    __tablename__ = 'zone_sensors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f"<ZoneSensor {self.id}>"


class DashboardTile(db.Model):
    __tablename__ = 'dashboard_tiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid', ondelete='CASCADE'), nullable=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('dashboard_tiles', cascade='all, delete-orphan', lazy=True))
    sensor = db.relationship('Sensor', backref=db.backref('dashboard_tiles', cascade='all, delete-orphan', lazy=True))


class AutomationRule(db.Model):
    __tablename__ = 'automation_rules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    sensor_type_id = db.Column(db.Integer, db.ForeignKey('sensor_types.id'), nullable=False)
    condition = db.Column(db.String(50), nullable=False)  # GREATER_THAN, LESS_THAN, EQUALS
    threshold = db.Column(db.String(100), nullable=False)  # Threshold value or state
    relay_device_id = db.Column(db.String(100), nullable=False)  # Device to control
    action = db.Column(db.String(10), nullable=False)  # ON or OFF
    enabled = db.Column(db.Boolean, default=True)  # Rule is active or not
    auto_description = db.Column(db.String(200), nullable=True)  # Auto-generated description
    auto_title = db.Column(db.String(100), nullable=True)  # Auto-generated title

    def __repr__(self):
        return f"<AutomationRule(id={self.id}, sensor_id={self.sensor_id}, relay_device_id={self.relay_device_id}, action={self.action})>"
    
    def as_dict(self):
        return {
            "rule_id": self.id,
            "user_id": self.user_id,
            "sensor_id": self.sensor_id,
            "sensor_type_id": self.sensor_type_id,
            "condition": self.condition,
            "threshold": self.threshold,
            "relay_device_id": self.relay_device_id,
            "action": self.action,
            "enabled": self.enabled,
            "auto_title": self.auto_title,
            "auto_description": self.auto_description,
        }