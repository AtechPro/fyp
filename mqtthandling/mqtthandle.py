from flask import Blueprint, jsonify
import paho.mqtt.client as mqtt
import json

mqttbp = Blueprint('mqtt', __name__)

BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883

mqtt_client = mqtt.Client()

# Structured data storage
device_messages = {}

def init_mqtt_client():
    try:
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)
        mqtt_client.loop_start()
        print(f"Connecting to MQTT broker at {BROKER_ADDRESS}:{BROKER_PORT}")
    except Exception as e:
        print(f"Error connecting to MQTT broker: {str(e)}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe("home/#")  # Subscribe after connection
    else:
        print(f"Failed to connect with return code {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        # Parse the payload
        payload = json.loads(msg.payload.decode())
        
        # Extract device ID (assuming it's in the payload or topic)
        device_id = payload.get('deviceId') or topic.split('/')[1]
        
        # Categorize messages by device and message type
        if device_id not in device_messages:
            device_messages[device_id] = {
                'sensors': [],
                'status': [],
                'raw_messages': []
            }
        
        # Determine message type and store accordingly
        if 'temperature' in payload or 'reed_switch' in payload:
            device_messages[device_id]['sensors'].append(payload)
        elif 'relay' in payload:
            device_messages[device_id]['status'].append(payload)
        
        # Always keep raw messages
        device_messages[device_id]['raw_messages'].append({
            'topic': topic,
            'payload': payload
        })
        
        #print(f"Processed message for device {device_id}")
    
    except json.JSONDecodeError:
        print(f"Error decoding JSON from topic {topic}")
    except Exception as e:
        print(f"Error processing message: {str(e)}")

@mqttbp.route('/mqtt/devices', methods=['GET'])
def get_all_device_messages():
    return jsonify(device_messages)

@mqttbp.route('/mqtt/device/<device_id>', methods=['GET'])
def get_device_messages(device_id):
    return jsonify(device_messages.get(device_id, {}))

@mqttbp.route('/mqtt/device/<device_id>/sensors', methods=['GET'])
def get_device_sensors(device_id):
    device_data = device_messages.get(device_id, {})
    return jsonify(device_data.get('sensors', []))

@mqttbp.route('/mqtt/device/<device_id>/status', methods=['GET'])
def get_device_status(device_id):
    device_data = device_messages.get(device_id, {})
    return jsonify(device_data.get('status', []))

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

init_mqtt_client()