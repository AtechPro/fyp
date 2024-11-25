from flask import Blueprint, jsonify
import paho.mqtt.client as mqtt

mqttbp = Blueprint('mqtt', __name__)

BROKER_ADDRESS = "atechpromqtt"  
BROKER_PORT = 1883  

mqtt_client = mqtt.Client()

def init_mqtt_client():
    try:
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)  
        mqtt_client.loop_start()  
        print(f"Connecting to MQTT broker at {BROKER_ADDRESS}:{BROKER_PORT}")
    except Exception as e:
        print(f"Error connecting to MQTT broker: {str(e)}")

mqtt_client.subscribe("home/#")


received_messages = []


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe("home/#")  # Subscribe after connection
    else:
        print(f"Failed to connect with return code {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    # print(f"Message received: {topic} - {payload}")
    received_messages.append({"topic": topic, "payload": payload})



@mqttbp.route('/mqtt/messages', methods=['GET'])
def get_received_messages():
    return jsonify(received_messages)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message



init_mqtt_client()

@mqttbp.route('/mqtt/subscribe', methods=['POST'])
def subscribe_to_all_devices():
    try:
        mqtt_client.subscribe("home/#")
        return jsonify({"message": "Subscribed to all topics under 'home/#'"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mqttbp.route('/mqtt/unsubscribe', methods=['POST'])
def unsubscribe_from_all():
    try:
        mqtt_client.unsubscribe("home/#")
        return jsonify({"message": "Unsubscribed from all topics under 'home/#'"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
