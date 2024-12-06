import requests
from flask import Blueprint, jsonify, request
from datetime import datetime
from database.database import db, Device, Sensor

# Create Blueprint
devicebp = Blueprint('devicemanage', __name__)

### Configuration ###
MQTT_URL = "http://localhost:5000/mqtt/messages"

### Helper Functions ###

# Fetch data from MQTT endpoint
def fetch_mqtt_data():
    try:
        response = requests.get(MQTT_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch MQTT data. Status code: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching MQTT data: {e}")
        return {}

# Add or update a device in the database
def add_or_update_device(device_id, ip_address, user_id=None):
    device = Device.query.filter_by(device_id=device_id).first()
    if not device:
        device = Device(
            device_id=device_id,
            ip_address=ip_address,
            status="online",
            last_seen=datetime.now(),
            userid=user_id
        )
        db.session.add(device)
    else:
        device.ip_address = ip_address
        device.status = "online"
        device.last_seen = datetime.now()
    db.session.commit()

# Add or update a sensor in the database
def add_or_update_sensor(device_id, sensor_type, sensor_name=None):
    sensor = Sensor.query.filter_by(device_id=device_id, sensor_type=sensor_type).first()
    if not sensor:
        sensor = Sensor(
            device_id=device_id,
            sensor_type=sensor_type,
            sensor_name=sensor_name or sensor_type,
            status="online",
            last_seen=datetime.now()
        )
        db.session.add(sensor)
    else:
        sensor.status = "online"
        sensor.last_seen = datetime.now()
    db.session.commit()

### Routes ###

# Fetch all devices and their sensors
@devicebp.route('/devices', methods=['GET', 'POST'])
def get_devices():
    devices = Device.query.all()
    device_list = []
    for device in devices:
        sensors = [
            {
                "sensor_type": sensor.sensor_type,
                "sensor_name": sensor.sensor_name,
                "status": sensor.status,
                "last_seen": sensor.last_seen
            }
            for sensor in device.sensors
        ]
        device_list.append({
            "device_id": device.device_id,
            "ip_address": device.ip_address,
            "status": device.status,
            "last_seen": device.last_seen,
            "userid": device.userid,
            "sensors": sensors
        })
    return jsonify(device_list)

# Add or update a device
@devicebp.route('/devices', methods=['POST'])
def save_device():
    data = request.json
    device_id = data.get('device_id')
    ip_address = data.get('ip_address', 'unknown')
    user_id = data.get('userid')  # Optional user ID for ownership

    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400

    # Fetch data from MQTT
    mqtt_data = fetch_mqtt_data()
    if device_id not in mqtt_data:
        return jsonify({"error": f"No data available for device {device_id}"}), 404

    add_or_update_device(device_id, ip_address, user_id)
    return jsonify({"message": "Device added or updated successfully"}), 201

# Add or update a sensor
@devicebp.route('/sensors', methods=['POST'])
def save_sensor():
    data = request.json
    device_id = data.get('device_id')
    sensor_type = data.get('sensor_type')
    sensor_name = data.get('sensor_name')

    if not device_id or not sensor_type:
        return jsonify({"error": "Device ID and Sensor Type are required"}), 400

    # Fetch data from MQTT
    mqtt_data = fetch_mqtt_data()
    if device_id not in mqtt_data or sensor_type not in mqtt_data[device_id]:
        return jsonify({"error": f"No data available for device {device_id} and sensor {sensor_type}"}), 404

    add_or_update_sensor(device_id, sensor_type, sensor_name)
    return jsonify({"message": "Sensor added or updated successfully"}), 201

# Fetch sensors for a specific device
@devicebp.route('/devices/<device_id>/sensors', methods=['GET'])
def get_device_sensors(device_id):
    device = Device.query.filter_by(device_id=device_id).first()
    if not device:
        return jsonify({"error": f"Device {device_id} not found"}), 404

    sensors = [
        {
            "sensor_type": sensor.sensor_type,
            "sensor_name": sensor.sensor_name,
            "status": sensor.status,
            "last_seen": sensor.last_seen
        }
        for sensor in device.sensors
    ]
    return jsonify({"device_id": device.device_id, "sensors": sensors})
