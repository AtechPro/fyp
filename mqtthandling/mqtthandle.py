from flask import Blueprint, jsonify, request
import paho.mqtt.client as mqtt
import json
import time

mqttbp = Blueprint('mqtt', __name__)

BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883
mqtt_client = mqtt.Client()

last_known_state = {}
is_broker_connected = False 


MAX_MESSAGE_AGE = 10


def init_mqtt_client():
    try:
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)
        mqtt_client.loop_start()
        print(f"Connecting to MQTT broker at {BROKER_ADDRESS}:{BROKER_PORT}")
    except Exception as e:
        print(f"Error connecting to MQTT broker: {str(e)}")


def on_connect(client, userdata, flags, rc):
    global is_broker_connected
    if rc == 0:
        print("Connected to MQTT broker.")
        is_broker_connected = True
        client.subscribe("home/#")  
    else:
        print(f"Failed to connect with return code {rc}")


def on_disconnect(client, userdata, rc):
    global is_broker_connected
    is_broker_connected = False
    print("Disconnected from MQTT broker.")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()  
        topic = msg.topic
        timestamp = time.time()
        process_message(topic, payload, timestamp)
    except Exception as e:
        print(f"Error processing message: {str(e)}")


def process_message(topic, payload, timestamp):
    global last_known_state
    try:
        if "sensors" in topic:
            data = json.loads(payload)
            device_id = data.get("deviceId")
            if device_id:
                # Store message with timestamp
                last_known_state[device_id] = {
                    "data": data,
                    "topic": topic,
                    "timestamp": timestamp
                }
    except Exception as e:
        print(f"Error processing message: {str(e)}")

# Route to get all sensor data (last known state of all devices)
@mqttbp.route('/mqtt/message', methods=['GET'])
def get_raw_messages():
    # Filter messages based on MAX_MESSAGE_AGE
    current_time = time.time()
    filtered_data = {
        device_id: details["data"]
        for device_id, details in last_known_state.items()
        if current_time - details["timestamp"] <= MAX_MESSAGE_AGE
    }
    return jsonify(filtered_data)

# Route to get specific sensor data for a device and sensor type
@mqttbp.route('/mqtt/message/<device_id>/<sensor_type>', methods=['GET'])
def get_sensor_data(device_id, sensor_type):
    if device_id in last_known_state:
        device_data = last_known_state[device_id]["data"]
        
        # Check if the requested sensor exists in the device's data
        sensor_data = device_data.get(sensor_type)
        
        if sensor_data is not None:
            return jsonify({sensor_type: sensor_data})
        else:
            return jsonify({"error": f"{sensor_type} data not available for device {device_id}"}), 404
    else:
        return jsonify({"error": f"Device {device_id} not found"}), 404

# Initialize MQTT client
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message

# Connect to the MQTT broker
init_mqtt_client()
