from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required
import paho.mqtt.client as mqtt
import time

mqtt_testing = Blueprint('mqtt_test', __name__, template_folder='mqtt_testing')

# Default MQTT Configuration
DEFAULT_MQTT_BROKER = "localhost"
MQTT_PORT = 1883

mqtt_client = mqtt.Client()

def on_connect(client, _, __, rc):
    if rc == 0:
        print("Connected to broker")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(_, __, message):
    print(f"Received message: {message.payload.decode()} on topic {message.topic}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

@mqtt_testing.route('/mqtt', methods=['GET', 'POST'])
@login_required
def mqtt_test():
    global mqtt_client

    if request.method == 'POST':
        broker_ip = request.form.get('broker_ip', DEFAULT_MQTT_BROKER)
        topic = request.form['topic']
        message = request.form['message']

        # Connect to specified broker IP
        mqtt_client.connect(broker_ip, MQTT_PORT, 60)

        # Publish a message to the custom topic
        result = mqtt_client.publish(topic, message)
        if result[0] == 0:
            flash('Message sent successfully!', 'success')
        else:
            flash('Failed to send message.', 'error')

    # Run the MQTT loop in a non-blocking way
    mqtt_client.loop_start()
    time.sleep(1)
    mqtt_client.loop_stop()

    return render_template('mqtt_testing/mqtt_test1.html')

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