from flask import Blueprint, render_template, request, flash, jsonify, Flask, redirect, url_for
from flask_login import login_required, LoginManager
import paho.mqtt.client as mqtt
from database.database import User
import time
import threading

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

# Load user for login management
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

mqtt_testing = Blueprint('mqtt_test', __name__, template_folder='mqtt_testing')

# Default MQTT Configuration
DEFAULT_MQTT_BROKER = "localhost"
MQTT_PORT = 1883

mqtt_client = mqtt.Client()

# Global variable for storing flash messages from MQTT callback
mqtt_flash_messages = []

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    """Called when the client connects to the broker."""
    if rc == 0:
        print("Connected to broker")
        mqtt_flash_messages.append(("Successfully connected to MQTT broker!", "success"))
    else:
        print(f"Failed to connect, return code {rc}")
        mqtt_flash_messages.append((f"Failed to connect, return code {rc}", "danger"))

def on_message(client, userdata, message):
    """Callback for when a message is received."""
    print(f"Received message: {message.payload.decode()} on topic {message.topic}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Run MQTT client in a background thread
def start_mqtt_loop():
    mqtt_client.loop_forever()

mqtt_thread = threading.Thread(target=start_mqtt_loop)
mqtt_thread.daemon = True
mqtt_thread.start()

def connect_to_mqtt(broker_ip):
    """Establish connection to MQTT broker."""
    try:
        mqtt_client.connect(broker_ip, MQTT_PORT, 60)
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

@app.after_request
def process_mqtt_flash_messages(response):
    """After every request, process MQTT flash messages."""
    if mqtt_flash_messages:
        for message, category in mqtt_flash_messages:
            flash(message, category)
        mqtt_flash_messages.clear()  # Clear the messages after processing
    return response

@mqtt_testing.route('/mqtt', methods=['GET', 'POST'])
@login_required
def mqtt_test():
    """MQTT Test route."""
    if request.method == 'POST':
        broker_ip = request.form.get('broker_ip', DEFAULT_MQTT_BROKER)
        topic = request.form['topic']
        message = request.form['message']

        # Attempt to connect to the broker
        try:
            mqtt_client.connect(broker_ip, MQTT_PORT, 60)
            mqtt_client.loop_start()
        except Exception as e:
            flash(f"MQTT connection error: {e}", "danger")
            return redirect(url_for('mqtt_test'))

        # Publish a message to the custom topic
        result = mqtt_client.publish(topic, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            flash('Message sent successfully!', 'success')
        else:
            flash('Failed to send message.', 'danger')

    return render_template('mqtt_testing/mqtt_test1.html')

@mqtt_testing.route('/mqtt_test/check_connection', methods=['GET'])
def check_connection():
    """Check MQTT broker connection."""
    broker_ip = request.args.get('broker_ip', DEFAULT_MQTT_BROKER)
    port = int(request.args.get('port', MQTT_PORT))

    try:
        mqtt_client.connect(broker_ip, port, 60)
        connected = True
    except Exception as e:
        print(f"Connection failed: {e}")
        connected = False

    return jsonify({"connected": connected})