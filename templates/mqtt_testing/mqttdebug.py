from flask import Blueprint, render_template, request, flash
from flask_login import login_required
import paho.mqtt.client as mqtt
import time

mqtt_testing = Blueprint('mqtt_test', __name__, template_folder='mqtt_testing')

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
DEFAULT_LED_TOPIC = "esp/d3/led"
DEFAULT_INFRARED_TOPIC = "esp/d4/infrared"

# MQTT Client Setup
mqtt_client = mqtt.Client()

# Define callback functions for MQTT events
def on_connect(client, _, __, rc):
    if rc == 0:
        print("Connected to broker")
        client.subscribe(DEFAULT_LED_TOPIC)
        client.subscribe(DEFAULT_INFRARED_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(_, __, message):
    print(f"Received message: {message.payload.decode()} on topic {message.topic}")

# Assign callbacks
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to the broker
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

@mqtt_testing.route('/mqtt', methods=['GET', 'POST'])
@login_required
def mqtt_test():
    if request.method == 'POST':
        message = request.form['message']
        topic = request.form['topic']

        # Publish a message to the selected topic
        result = mqtt_client.publish(topic, message)

        if result[0] == 0:
            flash('Message sent successfully!', 'success')
        else:
            flash('Failed to send message.', 'error')

    # Loop the MQTT client in a non-blocking way
    mqtt_client.loop_start()
    time.sleep(1)  # Let the loop run for a second
    mqtt_client.loop_stop()

    return render_template('mqtt_testing/mqtt_test1.html')

@mqtt_testing.teardown_app_request
def shutdown_mqtt_client(_=None):
    mqtt_client.disconnect()
