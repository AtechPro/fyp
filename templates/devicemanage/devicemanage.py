from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user

devicemanage_bp = Blueprint('devicemanage', __name__, template_folder='templates')

# Temporary in-memory device storage (to be replaced by database)
devices = []

# Route to list devices (with authentication)
@devicemanage_bp.route('/devices')
@login_required
def list_devices():
    """Display all devices"""
    return render_template('devicemanage/devicemanage.html', devices=devices)

# Route to add a device (with authentication)
@devicemanage_bp.route('/add_device', methods=['POST'])
@login_required
def add_device():
    """Add a new device by IP address"""
    ip_address = request.form.get('ip_address')

    # Check if the IP address is provided
    if not ip_address:
        flash('IP address is required', 'error')
        return redirect(url_for('devicemanage.list_devices'))

    # Add device to in-memory list
    device = {"ip_address": ip_address, "status": "pending"}
    devices.append(device)
    flash(f'Device with IP {ip_address} added successfully!', 'success')
    return redirect(url_for('devicemanage.list_devices'))

# Route to remove a device (with authentication)
@devicemanage_bp.route('/remove_device/<ip_address>', methods=['POST'])
@login_required
def remove_device(ip_address):
    """Remove a device"""
    global devices
    devices = [device for device in devices if device["ip_address"] != ip_address]
    flash(f'Device with IP {ip_address} removed successfully!', 'success')
    return redirect(url_for('devicemanage.list_devices'))
