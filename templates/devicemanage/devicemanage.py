from flask import Blueprint, jsonify, request, render_template
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import json

# Flask Blueprint
devicemanage_bp = Blueprint('devicemanage', __name__)

# MQTT Configuration
BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883
MQTT_TOPIC = "home/#"
DEVICE_TIMEOUT_SECONDS = 10  # Mark device as offline if no updates within this time

# MQTT Client
mqtt_client = mqtt.Client()

# In-memory storage for devices and sensors
devices = {}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect to MQTT broker with return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("deviceId")
        ip_address = payload.get("ip")

        if not device_id or not ip_address:
            print("Invalid MQTT message: missing deviceId or IP address.")
            return

        # Update or create device in memory
        if device_id not in devices:
            devices[device_id] = {
                "ip_address": ip_address,
                "status": "online",
                "last_seen": datetime.now().isoformat(),
                "sensors": {}
            }
        else:
            devices[device_id]["last_seen"] = datetime.now().isoformat()
            devices[device_id]["status"] = "online"

        # Update or add sensors
        for key, value in payload.items():
            if key not in ["deviceId", "ip"]:
                devices[device_id]["sensors"][key] = {
                    "value": value,
                    "status": "online",
                    "last_seen": datetime.now().isoformat()
                }

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# Check device timeout and mark as offline
def check_device_status():
    now = datetime.now()
    for device_id, device_info in devices.items():
        last_seen = datetime.fromisoformat(device_info["last_seen"])
        if (now - last_seen) > timedelta(seconds=DEVICE_TIMEOUT_SECONDS):
            devices[device_id]["status"] = "offline"

# Flask route to return devices with timeout checks applied
@devicemanage_bp.route('/devices', methods=['GET'])
def get_devices():
    check_device_status()  # Update statuses before returning
    return jsonify(devices)

# Initialize MQTT Client
def init_mqtt_client():
    try:
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)
        mqtt_client.loop_start()
        print(f"Connecting to MQTT broker at {BROKER_ADDRESS}:{BROKER_PORT}")
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")


@devicemanage_bp.route('/devicemanage', methods=['GET'])
def show_device_management():
    return render_template('devicemanage/devicemanage.html')


# Initialize MQTT Client
init_mqtt_client()
