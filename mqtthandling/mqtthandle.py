from flask import Blueprint, jsonify, request
import paho.mqtt.client as mqtt
import json
import time

mqttbp = Blueprint('mqtt', __name__)

# Configuration
BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883
MAX_MESSAGE_AGE = 10


mqtt_client = mqtt.Client()
last_known_state = {}


def init_mqtt_client():
    try:
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)
        mqtt_client.loop_start()
        print(f"Connecting to MQTT broker at {BROKER_ADDRESS}:{BROKER_PORT}")
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe("home/#")
    else:
        print(f"Failed to connect with return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())  
        topic = msg.topic
        device_id = payload.get("deviceId")
        if device_id:
            last_known_state[device_id] = {
                "data": payload,
                "timestamp": time.time()
            }
    except Exception as e:
        print(f"Error processing message: {e}")


@mqttbp.route('/mqtt/message', methods=['GET'])
def get_messages():
    current_time = time.time()
    filtered_data = {
        device_id: details["data"]
        for device_id, details in last_known_state.items()
        if current_time - details["timestamp"] <= MAX_MESSAGE_AGE
    }
    return jsonify(filtered_data)

@mqttbp.route('/mqtt/message/<device_id>/<sensor_type>', methods=['GET'])
def get_sensor(device_id, sensor_type):
    device_data = last_known_state.get(device_id, {}).get("data", {})
    if sensor_type in device_data:
        return jsonify({sensor_type: device_data[sensor_type]})
    return jsonify({"error": f"{sensor_type} data not available for device {device_id}"}), 404


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to the Broker
init_mqtt_client()
