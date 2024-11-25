from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from database.database import db

# Device Management Blueprint
devicebp = Blueprint('device', __name__)


devices = {}  

# Route: View All Devices
@devicebp.route('/devices', methods=['GET'])
@login_required
def view_devices():
    return render_template('device/devices.html', devices=devices)


# Route: Register a Device (Page + Action)
@devicebp.route('/devices/register', methods=['GET', 'POST'])
@login_required
def register_device():
    if request.method == 'POST':
        device_id = request.form.get('device_id')
        name = request.form.get('name')

        if not device_id or not name:
            flash("Device ID and Name are required.", "error")
            return redirect(url_for('device.register_device'))

        if device_id in devices:
            flash(f"Device {device_id} is already registered.", "error")
            return redirect(url_for('device.register_device'))

        # Register the device
        devices[device_id] = {"name": name, "status": "active"}

        # Subscribe to the device's topics using the MQTT blueprint
        mqtt_response = request.post(f"http://localhost:5000/mqtt/subscribe/{device_id}")
        if mqtt_response.status_code != 200:
            flash("Failed to subscribe to device topics.", "error")
            devices.pop(device_id)  # Rollback
            return redirect(url_for('device.register_device'))

        flash(f"Device {name} ({device_id}) successfully registered.", "success")
        return redirect(url_for('device.view_devices'))

    return render_template('device/register_device.html')


# Route: Unregister a Device
@devicebp.route('/devices/unregister/<device_id>', methods=['POST'])
@login_required
def unregister_device(device_id):
    if device_id not in devices:
        flash(f"Device {device_id} not found.", "error")
        return redirect(url_for('device.view_devices'))

    # Unregister the device
    devices.pop(device_id)

    # Unsubscribe from the device's topics using MQTT blueprint
    mqtt_response = request.post(f"http://localhost:5000/mqtt/unsubscribe/{device_id}")
    if mqtt_response.status_code != 200:
        flash("Failed to unsubscribe from device topics.", "error")
        return redirect(url_for('device.view_devices'))

    flash(f"Device {device_id} successfully unregistered.", "success")
    return redirect(url_for('device.view_devices'))
