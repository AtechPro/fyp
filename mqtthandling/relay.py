from flask import Blueprint, jsonify, request
import paho.mqtt.client as mqtt
import json

relaybp = Blueprint('relay', __name__)

BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883

relaybp = Blueprint('relay', __name__)

# MQTT Broker Configuration
BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883

# Helper function to send relay commands
def send_relay_command(device_id, relay_state):
    try:
        # Initialize MQTT client
        client = mqtt.Client()
        client.connect(BROKER_ADDRESS, BROKER_PORT, 60)

        # Define topic and payload
        topic = f"home/{device_id}/relay/command"
        if relay_state.lower() == "on":
            payload = "ON"
        elif relay_state.lower() == "off":
            payload = "OFF"
        else:
            raise ValueError("Invalid relay state. Must be 'on' or 'off'.")

        # Publish to the topic
        client.publish(topic, payload)
        client.disconnect()

        print(f"Relay command sent: Topic {topic}, Payload {payload}")
        return True
    except Exception as e:
        print(f"Error sending relay command: {str(e)}")
        return False

# Route to control relay via GET
@relaybp.route('/relay/<device_id>/<relay_state>', methods=['GET'])
def control_relay(device_id, relay_state):
    if relay_state.lower() not in ["on", "off"]:
        return jsonify({"error": "Invalid relay state. Use 'on' or 'off'."}), 400

    if send_relay_command(device_id, relay_state):
        return jsonify({"message": f"Relay command sent to {device_id} with state {relay_state}."})
    else:
        return jsonify({"error": "Failed to send relay command."}), 500

