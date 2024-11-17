from flask import Blueprint, render_template, request, flash, jsonify, Flask
from flask_login import login_required, LoginManager
from database.database import User
import paho.mqtt.client as mqtt
import threading

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

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

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, message):
    global received_messages
    print(f"Received message on {message.topic}: {message.payload.decode()}")
    # Store the message in the dictionary with the topic as the key
    received_messages[message.topic] = message.payload.decode()


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Start MQTT client loop in a background thread
def start_mqtt_loop():
    mqtt_client.loop_forever()

@mqtt_testing.route('/mqtt', methods=['GET', 'POST'])
@login_required
def mqtt_test():
    global mqtt_client, received_messages

    if request.method == 'POST':
        broker_ip = request.form.get('broker_ip', DEFAULT_MQTT_BROKER)
        publish_topic = request.form['topic']
        message = request.form['message']
        subscribe_topic = request.form['subscribe_topic']

        # Connect to the MQTT broker
        mqtt_client.connect(broker_ip, MQTT_PORT, 60)

        # Publish the message
        result = mqtt_client.publish(publish_topic, message)
        if result[0] == 0:
            flash('Message sent successfully!', 'success')
        else:
            flash('Failed to send message.', 'danger')

        # Subscribe to the specified topic
        mqtt_client.subscribe(subscribe_topic)
        flash(f"Subscribed to topic: {subscribe_topic}", 'info')

        # Start the MQTT loop in a separate thread if not already running
        threading.Thread(target=start_mqtt_loop, daemon=True).start()

    # Pass received messages to the template
    return render_template('mqtt_testing/mqtt_test1.html', received_messages=received_messages)

print("Current received messages:", received_messages)



@mqtt_testing.teardown_app_request
def shutdown_mqtt_client(_=None):
    mqtt_client.disconnect()

@mqtt_testing.route('/mqtt_test/check_connection', methods=['GET'])
def check_connection():
    broker_ip = request.args.get('broker_ip', DEFAULT_MQTT_BROKER)
    try:
        # Attempt to connect to the broker
        mqtt_client.connect(broker_ip, MQTT_PORT, 60)
        connected = True
    except Exception as e:
        print(f"Connection failed: {e}")
        connected = False
    return jsonify({"connected": connected})
