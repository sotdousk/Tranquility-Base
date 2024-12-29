import os
import json
from flask import Flask, render_template
import paho.mqtt.client as mqtt
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret!"
socketio = SocketIO(app)

invasion_detected = False

DATA_FILE = "./data/nodes.json"
# MQTT Configuration
TEST_BROKER_IP = "192.168.2.5"
BROKER = "mqtt.eclipseprojects.io"  # Replace with your broker's address
PORT = 1883  # Default MQTT port
TOPIC = "home/automation/#"  # Subscribe to all subtopics under 'home/automation'


# Load and Save JSON Data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as file:
        # data = json.load(file)
        raw_data = json.load(file)
        return raw_data


def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker {TEST_BROKER_IP} with result code: {rc}")
        client.subscribe(TOPIC)
    else:
        print(f"Failed to connect, return code: {rc}")
    return rc


# Broadcast new sensor data via WebSocket
def on_message(client, userdata, message):
    try:
        # Decode the message payload
        payload = json.loads(message.payload.decode())
        node = list(payload.keys())[0]
        node_data = payload[node]
        print(f"MQTT Message received from {node}, on topic {message.topic}: {payload}")

        # Load existing data from the JSON file
        data = load_data()
        print(data)
        data[node] = node_data
        print(data)

        save_data(data)
        print(f"Node {node} updated successfully: {node_data}")

        # Broadcast updated data to clients
        socketio.emit("update_node", {node: node_data})

    except json.JSONDecodeError:
        print("Failed to decode MQTT message payload as JSON")
    except Exception as e:
        print(f"Error in on_message: {e}")


def check_intrusion():
    global invasion_detected
    data = load_data()
    msg = ""
    for key in data:
        if key != "Intrusion_detected":
            node_name = key
            if 'motion' in data[node_name]['sensors']:
                if (data[node_name]['on_alert']) and (data[node_name]['sensors']['motion'] == 'Motion Detected'):
                    invasion_detected = True
                    if msg == "":
                        msg = f"Invasion detected in {node_name} - Motion: Motion Detected"
                    else:
                        msg += f"<br>Invasion detected in {node_name} - Motion: Motion Detected"
            if 'door' in data[node_name]['sensors']:
                if (data[node_name]['on_alert']) and (data[node_name]['sensors']['door'] == 'Open'):
                    invasion_detected = True
                    if msg == "":
                        msg = f"Invasion detected in {node_name} - Door: Open"
                    else:
                        msg += f"<br>Invasion detected in {node_name} - Door: Open"
    if msg == "":
        msg = "All Clear. No Intrusions Detected."
        invasion_detected = False
    return msg


# MQTT Client Setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT, 60)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/security')
def security():
    data = load_data()
    check_result = check_intrusion()
    for node, details in data.items():
        print(node, details)
    return render_template("security.html", nodes=data, message=check_result)


@app.route('/thermal')
def thermal():
    return "Thermal Comfort page under construction!"  # Replace with your thermal view template later


@app.route('/settings')
def settings():
    return "Settings page under construction!"  # Replace with your settings view template later


if __name__ == "__main__":
    app.run(debug=True)
