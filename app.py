from flask import Flask, session, flash
from database.database import db, User, SensorType  # Import SensorType
from view import views
from templates.usermanage.usermanage import usermanage
from templates.feedback.feedback import feedbackbp
from templates.dashboard.dashboard import dashboardbp, init_mqtt_client
from templates.devicemanage.devicemanage import devicemanage_bp
from templates.automationrule.automation import autobp
from templates.zone.zone import zone_bp
from templates.timerscheduler.timer import timerbp
from templates.backuprestore.backuprestore import backup_restore_bp


from flask_login import LoginManager, login_user, logout_user, current_user
from datetime import timedelta
from flask.sessions import SecureCookieSessionInterface
import uuid
from flask_socketio import SocketIO, emit


app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/database.db'  # Database location
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "mysecretkey"  
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['BROKER_ADDRESS'] = "atechpromqtt"
app.config['BROKER_PORT'] = 1883
app.config['MQTT_TOPIC'] = "home/#"

socketio = SocketIO(app, cors_allowed_origins="*")  


app.register_blueprint(views) 
app.register_blueprint(usermanage)
app.register_blueprint(feedbackbp)
app.register_blueprint(devicemanage_bp)
app.register_blueprint(dashboardbp)
app.register_blueprint(zone_bp)
app.register_blueprint(autobp)
app.register_blueprint(timerbp)
app.register_blueprint(backup_restore_bp)
# Initialize the database
db.init_app(app)

# Initialize the Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'views.login'  

class CustomSessionInterface(SecureCookieSessionInterface):
    def save_session(self, *args, **kwargs):
        user = current_user._get_current_object()
        if user and user.is_authenticated:
            session_id = session.get('session_id')
            if session_id and session_id != user.session_id:
                logout_user()
                session.clear()
                flash('You have been logged out due to another login from a different device.', 'warning')
        super(CustomSessionInterface, self).save_session(*args, **kwargs)

app.session_interface = CustomSessionInterface()

def populate_sensor_types():
    sensor_types = [
        {
            'type_key': 'temperature',
            'display_name': 'Temperature Sensor',
            'unit': '°C',
            'states': None
        },
        {
            'type_key': 'humidity',
            'display_name': 'Humidity Sensor',
            'unit': '%',
            'states': None
        },
        {
            'type_key': 'reed_switch',
            'display_name': 'Status Sensor',
            'unit': None,
            'states': ['OPEN', 'CLOSED']
        },
        {
            'type_key': 'photo_interrupter',
            'display_name': 'Status Sensor',
            'unit': None,
            'states': ['CLEAR', 'BLOCKED']
        },
        {
            'type_key': 'relay',
            'display_name': 'Status Sensor',
            'unit': None,
            'states': ['ON', 'OFF']
        },
        {
            'type_key': 'pir',
            'display_name': 'Motion Sensor',
            'unit': None,
            'states': ['MOTION DETECTED', 'NO MOTION']
        },
        {
            'type_key': 'photoresistor',
            'display_name': 'Analog Sensor',
            'unit': 'Lux',
            'states': None
        }
    ]

    for sensor_type_data in sensor_types:
        sensor_type = SensorType.query.filter_by(type_key=sensor_type_data['type_key']).first()
        if not sensor_type:
            sensor_type = SensorType(**sensor_type_data)
            db.session.add(sensor_type)
            print(f"Added sensor type: {sensor_type.type_key}")  # Debugging

    try:
        db.session.commit()
        print("Sensor types populated successfully.")  # Debugging
    except Exception as e:
        db.session.rollback()
        print(f"Failed to populate sensor types: {e}")  # Debugging

def create_initial_user(app):
    """Create the initial admin user and populate sensor types."""
    with app.app_context():
        db.create_all()  # Create all tables

        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():  
            admin_user = User(
                username='admin',
                name='Administrator',
                role=1,  # Admin role
                password='admin'  
            )
            db.session.add(admin_user) 
            db.session.commit()  
            print("Initial admin user created.")
        else:
            print("Admin user already exists.")

        # Populate sensor types
        populate_sensor_types()



@login_manager.user_loader
def load_user(userid):
    return db.session.get(User, int(userid))

if __name__ == '__main__':
    with app.app_context():
        create_initial_user(app)  
        init_mqtt_client() 
    app.run(debug=True, host='0.0.0.0')