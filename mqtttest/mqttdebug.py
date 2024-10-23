from flask import Blueprint, render_template, request, flash
from flask_login import login_required
import paho.mqtt.client as mqtt
import time

mqtt_testing = Blueprint('mqtt_test', __name__)

# MQTT Configuration
MQTT_BROKER = "localhost"  # Change to your MQTT broker address
MQTT_PORT = 1883
MQTT_TOPIC = "test/topic"

# MQTT Client Setup
mqtt_client = mqtt.Client()

# Define callback functions for MQTT events
def on_connect(client, _, __, rc):  # Replace unused parameters with _
    if rc == 0:
        print("Connected to broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(_, __, message):  # Replace unused parameters with _
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
        
        # Publish a message to the MQTT broker
        result = mqtt_client.publish(MQTT_TOPIC, message)
        
        if result[0] == 0:
            flash('Message sent successfully!', 'success')
        else:
            flash('Failed to send message.', 'error')

    # Loop the MQTT client in a non-blocking way
    mqtt_client.loop_start()
    time.sleep(1)  # Let the loop run for a second
    mqtt_client.loop_stop()

    return render_template('mqtttest.html')

# Clean up and disconnect the MQTT client on app context shutdown
@mqtt_testing.teardown_app_request
def shutdown_mqtt_client(_=None):  # Replace unused exception with _
    mqtt_client.disconnect()
