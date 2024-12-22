import signal
import sys
import os
import json
from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
from flask_socketio import SocketIO, emit
import threading

file_lock = threading.Lock()

app = Flask(__name__)

# Initialize Flask-SocketIO
socketio = SocketIO(app)

DATA_FILE = "data/nodes.json"

# MQTT Configuration
TEST_BROKER_IP = "192.168.2.5"
BROKER = "mqtt.eclipseprojects.io"  # Replace with your broker's address
PORT = 1883  # Default MQTT port
TOPIC = "home/automation/#"  # Subscribe to all subtopics under 'home/automation'


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker {TEST_BROKER_IP} with result code: {rc}")
        client.subscribe(TOPIC)
    else:
        print(f"Failed to connect, return code: {rc}")


# Broadcast new sensor data via WebSocket
def on_message(client, userdata, message):
    try:
        # Decode the message payload
        payload = json.loads(message.payload.decode())
        print(f"MQTT Message received on topic {message.topic}: {payload}")

        # Ensure the payload contains the "node" key
        # node = payload.get("node")
        node = list(payload.keys())[0]
        print(f"Node: {node}")
        if not node:
            print("Error: 'node' key is missing from the payload")
            return  # Exit if "node" key is missing

        # Load existing data from the JSON file
        with file_lock:
            data = load_data()
            print(f"Load Data: {data}")

            # Check if the node exists; if not, initialize it
            if node not in data:
                data[node] = {"alarm": False, "sensors": {}}

            # Update sensor data
            if "sensors" in payload[node]:
                print("Update sensor data")
                data[node]["sensors"].update(payload[node]["sensors"])
                if "temperature" in data[node]["sensors"]:
                    data[node]["sensors"]["temperature"] = round(data[node]["sensors"]["temperature"], 2)

            # # Update alarm state if provided
            # if "alarm" in payload[node]:
            #     print("Update alarm data")
            #     data[node]["alarm"] = payload[node]["alarm"]

            # Save the updated data to the JSON file
            save_data(data)

        # Emit the updated node data to all connected clients via Socket.IO
        socketio.emit('update_node', {node: data[node]})
        print(f"Node '{node}' updated successfully and broadcast to clients.")

    except json.JSONDecodeError:
        print("Failed to decode MQTT message payload as JSON")
    except Exception as e:
        print(f"Error in on_message: {e}")


# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(TEST_BROKER_IP, PORT, 60)


@socketio.on('connect')
def handle_connect():
    print("Client connected to Socket.IO")


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
    print("Data saved to JSON:", data)


def validate_nodes(nodes):
    if not isinstance(nodes, dict):
        raise ValueError("Invalid nodes data: Root element must be a dictionary.")
    for node, data in nodes.items():
        if not isinstance(data, dict) or "alarm" not in data or "sensors" not in data:
            raise ValueError(f"Invalid node data for {node}: Missing required keys.")


@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", data=data)


# Flask route to expose sensor data via an API
@app.route("/api/sensors", methods=["GET"])
def get_sensor_data():
    data = load_data()
    return jsonify(data)


@app.route("/sensors")
def sensors():
    data = load_data()
    # Determine if all alarms are enabled
    all_alarms_enabled = all(node["alarm"] for node in data.values())
    return render_template("sensors.html", data=data, all_alarms_enabled=all_alarms_enabled)


@app.route("/api/toggle_alarm", methods=["POST"])
def toggle_alarm():
    with file_lock:  # Ensure thread safety
        data = load_data()
        request_data = request.get_json()
        node = request_data.get("node")
        if node in data:
            # Toggle the alarm state
            data[node]["alarm"] = not data[node]["alarm"]
            save_data(data)  # Persist changes to JSON file

            # Emit the update via Socket.IO
            socketio.emit('update_node', {node: data[node]})

            return jsonify({"message": f"Alarm for {node} is now {'enabled' if data[node]['alarm'] else 'disabled'}"}), 200
        return jsonify({"error": "Node not found"}), 404


@app.route('/api/toggle_all_alarms', methods=['POST'])
def toggle_all_alarms():
    with file_lock:  # Ensure thread safety
        try:
            data = load_data()
            request_data = request.get_json()
            enable = request_data.get("enable")

            if enable is None:
                return jsonify({"error": "Missing 'enable' field in request payload."}), 400

            # Update all nodes and persist changes
            for node in data:
                data[node]["alarm"] = enable
            save_data(data)

            # Emit the update via Socket.IO
            socketio.emit('update_all', {'alarm': enable})

            return jsonify({"message": f"All alarms {'enabled' if enable else 'disabled'} successfully!"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


# Graceful shutdown function
def shutdown_handler(signal_received, frame):
    print("\nShutting down gracefully...")
    mqtt_client.disconnect()
    mqtt_client.loop_stop()
    sys.exit(0)


# Bind the shutdown handler to signals
signal.signal(signal.SIGINT, shutdown_handler)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, shutdown_handler)  # Handle termination signals


if __name__ == "__main__":
    # Run MQTT client in a separate thread
    def mqtt_loop():
        mqtt_client.loop_forever()

    # Run Flask app with SockectIO
    threading.Thread(target=mqtt_loop).start()
    # socketio.run(app, debug=True, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)

    try:
        # Run Flask app
        app.run(debug=True)
    except KeyboardInterrupt:
        shutdown_handler(None, None)
