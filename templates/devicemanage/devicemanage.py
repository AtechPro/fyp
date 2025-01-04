from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import json
from threading import Thread
import time
from database.database import db, Device, Sensor, SensorType

devicemanage_bp = Blueprint('devicemanage', __name__)

# MQTT Configuration
BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883
MQTT_TOPIC = "home/#"
DEVICE_TIMEOUT = 3  # seconds
CHECK_INTERVAL = 3  # seconds

# In-memory device store
devices = {}

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect to MQTT broker with return code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received from MQTT."""
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

        # Update or add sensors from the MQTT payload
        for key, value in payload.items():
            if key not in ["deviceId", "ip"]:
                devices[device_id]["sensors"][key] = {
                    "value": value,
                    "status": "online",
                    "last_seen": datetime.now().isoformat()
                }
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def monitor_device_status():
    """Background task to monitor device status based on last seen time."""
    while True:
        now = datetime.now()
        for device_id, device_info in devices.items():
            last_seen = datetime.fromisoformat(device_info["last_seen"])

            # Check if the device has been offline for too long
            if (now - last_seen) > timedelta(seconds=DEVICE_TIMEOUT):
                if device_info["status"] != "offline":
                    device_info["status"] = "offline"
                    print(f"Device {device_id} marked as offline.")
            else:
                if device_info["status"] != "online":
                    device_info["status"] = "online"
                    print(f"Device {device_id} marked as online.")
        time.sleep(CHECK_INTERVAL)

# Start monitoring device status in the background
status_monitor_thread = Thread(target=monitor_device_status, daemon=True)
status_monitor_thread.start()

def init_mqtt_client():
    """Initialize and start the MQTT client."""
    try:
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

@devicemanage_bp.route('/device')
@login_required
def get_devices():
    """API to fetch device list."""
    user_id = current_user.get_id()
    device_list = []
    for device_id, device_info in devices.items():
        paired_device = Device.query.filter_by(device_id=device_id, userid=user_id).first()

        # Create device info dictionary
        device_data = {
            "device_id": device_id,
            "ip_address": device_info.get("ip_address", "N/A"),
            "status": device_info.get("status", "offline"),
            "last_seen": device_info.get("last_seen"),
            "paired": paired_device is not None,
            "sensors": device_info.get("sensors", []),
            # Add title and description from the paired device if it exists
            "title": paired_device.title if paired_device else None,
            "description": paired_device.description if paired_device else None
        }
        device_list.append(device_data)

    return jsonify(device_list)

@devicemanage_bp.route('/devicemanage')
@login_required
def devicemanage():
    """Render the device management page."""
    device_list = [
        {
            "device_id": device_id,
            "ip_address": device_info["ip_address"],
            "status": device_info["status"],
            "last_seen": device_info["last_seen"],
            "sensors": device_info["sensors"]
        }
        for device_id, device_info in devices.items()
    ]
    return render_template('devicemanage/devicemanage.html', user=current_user, devices=device_list)

@devicemanage_bp.route('/add_device', methods=['POST'])
@login_required
def add_device():
    """API to add a new device and associated sensors."""
    data = request.get_json()
    print("Incoming request data:", data)

    device_id = data.get('device_id')
    title = data.get('title')
    description = data.get('description')
    user_id = current_user.get_id()

    print(f"Processing device: {device_id}, title: {title}, user_id: {user_id}")

    # Check if the device already exists
    if Device.query.filter_by(device_id=device_id).first():
        return jsonify({"error": "Device already exists"}), 400

    # Check if device exists in MQTT memory
    mqtt_device_data = devices.get(device_id)
    if not mqtt_device_data:
        print(f"Warning: Device {device_id} not found in MQTT data")
        
    # Create a new device entry
    new_device = Device(
        device_id=device_id,
        title=title,
        description=description,
        userid=user_id,
        status=True
    )
    db.session.add(new_device)
    print(f"Added new device: {device_id}")

    # Fetch all sensor types from the database
    sensor_types = SensorType.query.all()
    sensor_type_mapping = {st.type_key: st.id for st in sensor_types}
    print("Available sensor types:", sensor_type_mapping)

    # Add a default 'unknown' sensor type if it doesn't exist
    if 'unknown' not in sensor_type_mapping:
        try:
            unknown_sensor_type = SensorType(
                type_key='unknown',
                display_name='Unknown Sensor',
                unit=None,
                states=None
            )
            db.session.add(unknown_sensor_type)
            db.session.flush()
            sensor_type_mapping['unknown'] = unknown_sensor_type.id
            print("Added unknown sensor type")
        except Exception as e:
            print(f"Error adding unknown sensor type: {e}")
            return jsonify({"error": "Failed to create unknown sensor type"}), 500

    def categorize_sensor_type(sensor_key):
        sensor_type_id = sensor_type_mapping.get(sensor_key, sensor_type_mapping.get('unknown'))
        print(f"Categorizing sensor {sensor_key} as type_id: {sensor_type_id}")
        return sensor_type_id

    try:
        # Get sensors from MQTT data if available
        if mqtt_device_data and 'sensors' in mqtt_device_data:
            mqtt_sensors = mqtt_device_data['sensors']
            print(f"Found MQTT sensors for device: {mqtt_sensors}")
            
            for sensor_key, sensor_data in mqtt_sensors.items():
                print(f"Processing MQTT sensor: {sensor_key} with data: {sensor_data}")
                
                sensor_type_id = categorize_sensor_type(sensor_key)
                if sensor_type_id is None:
                    print(f"Error: Failed to categorize sensor type for key: {sensor_key}")
                    continue

                new_sensor = Sensor(
                    device_id=device_id,
                    sensor_key=sensor_key,
                    sensor_type_id=sensor_type_id,
                    value=str(sensor_data.get('value')),
                    status=sensor_data.get('status', 'online'),
                    last_seen=datetime.now(),
                    userid=user_id
                )
                db.session.add(new_sensor)
                print(f"Added sensor: {sensor_key} to device: {device_id}")

        db.session.commit()
        print("Successfully committed all changes to database")
        
        sensor_count = len(mqtt_device_data.get('sensors', {})) if mqtt_device_data else 0
        return jsonify({
            "message": "Device and sensors added successfully",
            "device_id": device_id,
            "sensor_count": sensor_count
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error during sensor creation: {str(e)}")
        return jsonify({"error": f"Failed to save device and sensors: {str(e)}"}), 500

@devicemanage_bp.route('/delete_device/<device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    """API to delete a device and its associated sensors."""
    # Find the device
    device = Device.query.filter_by(device_id=device_id).first()

    if not device:
        return jsonify({"error": "Device not found"}), 404

    try:
        # Delete associated sensors first
        sensors = Sensor.query.filter_by(device_id=device_id).all()
        for sensor in sensors:
            db.session.delete(sensor)

        # Delete the device itself
        db.session.delete(device)
        db.session.commit()

        return jsonify({"message": "Device and sensors deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()  # Rollback transaction in case of an error
        return jsonify({"error": f"Failed to delete device: {str(e)}"}), 500

@devicemanage_bp.route('/edit_device', methods=['POST'])
@login_required
def edit_device():
    """API to edit an existing device."""
    data = request.get_json()
    device_id = data.get('device_id')

    # Check if the device exists
    device = Device.query.filter_by(device_id=device_id).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404

    # Update device fields
    device.title = data.get('title', device.title)  # Update title if provided
    device.description = data.get('description', device.description)  # Update description if provided
    device.status = data.get('status', device.status)  # Update status if provided
    device.last_seen = datetime.now()  # Automatically update last_seen timestamp

    # Commit the changes
    db.session.commit()

    return jsonify({
        "message": "Device updated successfully",
        "device": {
            "device_id": device.device_id,
            "title": device.title,
            "description": device.description,
            "status": device.status,
            "last_seen": device.last_seen
        }
    }), 200

# Initialize MQTT client
init_mqtt_client()