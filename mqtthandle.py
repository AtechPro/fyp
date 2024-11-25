from flask import Blueprint, request, jsonify
import paho.mqtt.client as mqtt

# Create MQTT blueprint
mqttbp = Blueprint('mqtt', __name__)


BROKER_ADDRESS = "atechpromqtt"  
BROKER_PORT = 1883  


mqtt_client = mqtt.Client()


subscribed_devices = set()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
    else:
        print(f"Failed to connect with return code {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"Message received on topic '{topic}': {payload}")

    
    if "sensors" in topic:
        handle_sensor_data(topic, payload)
    elif "relay/status" in topic:
        handle_relay_status(topic, payload)


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


def handle_sensor_data(topic, payload):
    print(f"Processing sensor data from {topic}: {payload}")
    # Add logic for storing or analyzing sensor data



def handle_relay_status(topic, payload):
    print(f"Processing relay status from {topic}: {payload}")
   


# Route: Subscribe to a Device's Topics
@mqttbp.route('/mqtt/subscribe/<device_id>', methods=['POST'])
def subscribe_to_device(device_id):
    try:
        if device_id in subscribed_devices:
            return jsonify({"message": f"Device {device_id} already subscribed."}), 200

        # Dynamically subscribe to the device's topics
        sensor_topic = f"home/{device_id}/sensors"
        relay_status_topic = f"home/{device_id}/relay/status"

        mqtt_client.subscribe(sensor_topic)
        mqtt_client.subscribe(relay_status_topic)

        subscribed_devices.add(device_id)
        return jsonify({
            "success": True,
            "subscribed_topics": [sensor_topic, relay_status_topic]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Publish to a Device's Relay Command Topic
@mqttbp.route('/mqtt/publish/<device_id>/relay/command', methods=['POST'])
def publish_relay_command(device_id):
    try:
        data = request.json
        command = data.get('command')  # Expected: ON/OFF
        if not command:
            return jsonify({"error": "Command is required"}), 400

        relay_command_topic = f"home/{device_id}/relay/command"
        mqtt_client.publish(relay_command_topic, command)

        return jsonify({
            "success": True,
            "topic": relay_command_topic,
            "command": command
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Unsubscribe a Device
@mqttbp.route('/mqtt/unsubscribe/<device_id>', methods=['POST'])
def unsubscribe_device(device_id):
    try:
        if device_id not in subscribed_devices:
            return jsonify({"message": f"Device {device_id} is not subscribed."}), 400

        # Unsubscribe from the device's topics
        sensor_topic = f"home/{device_id}/sensors"
        relay_status_topic = f"home/{device_id}/relay/status"

        mqtt_client.unsubscribe(sensor_topic)
        mqtt_client.unsubscribe(relay_status_topic)

        subscribed_devices.remove(device_id)
        return jsonify({
            "success": True,
            "unsubscribed_topics": [sensor_topic, relay_status_topic]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# MQTT Client Initialization
def init_mqtt_client():
    try:
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)  # Connect to the broker
        mqtt_client.loop_start()  # Start the network loop
        print(f"Connecting to MQTT broker at {BROKER_ADDRESS}:{BROKER_PORT}")
    except Exception as e:
        print(f"Error connecting to MQTT broker: {str(e)}")


# Initialize the MQTT client when the blueprint is loaded
init_mqtt_client()
