from flask import Blueprint, render_template, request, flash, jsonify, Flask, redirect, url_for
from flask_login import login_required, LoginManager
import paho.mqtt.client as mqtt
from database.database import User
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

# Global variable for storing received messages
received_messages = {}
# Global variable to queue flash messages from MQTT callback
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
    """Called when a message is received on a subscribed topic."""
    global received_messages
    print(f"Received message on {message.topic}: {message.payload.decode()}")
    # Store the message in the dictionary with the topic as the key
    received_messages[message.topic] = message.payload.decode()

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def connect_to_mqtt(broker_ip):
    """Establish connection to MQTT broker."""
    try:
        mqtt_client.connect(broker_ip, MQTT_PORT, 60)
        mqtt_client.loop_start()  # Start the loop to handle communication in the background
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def publish_message(topic, payload):
    """Publish a message to a specific topic."""
    result = mqtt_client.publish(topic, payload)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        flash("Message sent successfully!", "success")
    else:
        flash("Failed to send message.", "danger")

def subscribe_to_topic(topic):
    """Subscribe to a topic."""
    mqtt_client.subscribe(topic)
    flash(f"Subscribed to topic: {topic}", "info")

@app.after_request
def process_mqtt_flash_messages(response):
    """After every request, process any MQTT flash messages and add them to the session."""
    if mqtt_flash_messages:
        for message, category in mqtt_flash_messages:
            flash(message, category)
        mqtt_flash_messages.clear()  # Clear the messages after processing
    return response

@mqtt_testing.route('/mqtt', methods=['GET', 'POST'])
@login_required
def mqtt_test():
    global mqtt_client, received_messages

    if request.method == 'POST':
        broker_ip = request.form.get('broker_ip', DEFAULT_MQTT_BROKER)
        publish_topic = request.form['topic']
        message = request.form['message']

        subscribe_topic = request.form.get('subscribe_topic', None)

        # Check if the broker is already connected
        if not mqtt_client.is_connected():
            if not connect_to_mqtt(broker_ip):
                flash("Could not connect to the broker.", "danger")
                return render_template('mqtt_testing/mqtt_test1.html', received_messages=received_messages)

        # Publish the message
        publish_message(publish_topic, message)

        if subscribe_topic:
            # Subscribe to the topic if provided
            subscribe_to_topic(subscribe_topic)

    # Return template with the received messages
    return render_template('mqtt_testing/mqtt_test1.html', received_messages=received_messages)


@mqtt_testing.route('/mqtt/test2', methods=['GET'])
@login_required
def mqtt_test2():
    global received_messages

    # Ensure the MQTT client is connected
    if not mqtt_client.is_connected():
        flash("MQTT broker is not connected. Please connect to the broker first.", "danger")
        return render_template('mqtt_testing/mqtt_test2.html', topic=None, message=None)

    topic = request.args.get('topic', None)
    message = received_messages.get(topic, None)  # Get the last received message for the topic
    
    return render_template('mqtt_testing/mqtt_test2.html', topic=topic, message=message)


@mqtt_testing.route('/mqtt_test/check_connection', methods=['GET'])
def check_connection():
    broker_ip = request.args.get('broker_ip', DEFAULT_MQTT_BROKER)
    port = int(request.args.get('port', MQTT_PORT))  # Default to MQTT_PORT if not provided

    try:
        # Attempt to connect to the broker with the provided IP and port
        mqtt_client.connect(broker_ip, port, 60)
        mqtt_client.loop_start()  # Start the loop to maintain the connection
        flash("Successfully connected to the MQTT broker!", "success")
    except Exception as e:
        print(f"Connection failed: {e}")
        flash(f"Connection failed: {e}", "danger")
        return redirect(url_for('mqtt_test.mqtt_test2'))

    # Redirect to the /mqtt/test2 route on successful connection
    return redirect(url_for('mqtt_test.mqtt_test2'))


# Teardown MQTT client (disconnect when done)
@mqtt_testing.teardown_app_request
def shutdown_mqtt_client(_=None):
    mqtt_client.disconnect()
