from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user


device = Blueprint('device', __name__)


@device.route('/temperature')
def temperature():
    return render_template('temperature.html')

@device.route('/mqtt_com')
def mqtt_com():
    return render_template('com.html')