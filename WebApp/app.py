import os
import signal
import sys
import json
from flask import Flask, render_template, request, jsonify
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
        print(f"Connected to MQTT broker {TEST_BROKER_IP} with result code {rc}")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: {TOPIC}")
    else:
        print(f"Failed to connect, return code: {rc}")


def validate_data(data):
    for node, details in data.items():
        if node != "Intrusion_detected":
            if "sensors" not in details:
                details["sensors"] = {}
            if "security" not in details["sensors"]:
                details["sensors"]["security"] = {"door": "N/A", "motion": "N/A"}
    return data


# Broadcast new sensor data via WebSocket
def on_message(client, userdata, message):
    print("New message arrived!")
    try:
        # Debug the raw payload before decoding
        print(f"Raw MQTT payload: {message.payload}")

        raw_payload = message.payload.decode()
        if not raw_payload.strip():
            print("Empty MQTT payload received. Skipping...")
            return

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as e:
            print(f"Malformed JSON payload: {raw_payload}. Error: {e}")
            return
        print(f"Decoded payload: {payload}")
        node = list(payload.keys())[0]
        node_data = payload[node]

        print(f"Received MQTT data for {node}: {node_data}")
        if "sensors" not in node_data or "security" not in node_data["sensors"]:
            print(f"Missing security sensors data for node: {node}")
        else:
            print(f"Security sensors data for node: {node} formatted as expected.")

        # Load JSON file
        data = load_data()
        data[node] = node_data

        # Check for intrusions
        intrusion_detected = False
        for node, details in data.items():
            if node != "Intrusion_detected":
                if "security" not in details["sensors"]:
                    details["sensors"]["security"] = {"door": "N/A", "motion": "N/A"}
                if details["on_alert"]:
                    if details["sensors"]['security']["motion"] == "Motion Detected" or \
                         details["sensors"]['security']["door"] == "Open":
                        intrusion_detected = True

        # Update and broadcast data
        data["Intrusion_detected"] = intrusion_detected
        data = validate_data(data)
        save_data(data)
        # Broadcast to clients
        socketio.emit("update_node", data)
        print(f"Broadcasting: {data}")

    except Exception as e:
        print(f"Error in on_message: {e}")


def check_intrusion():
    global invasion_detected
    data = load_data()
    msg = ""
    invasion_detected = False  # Reset the state before checking

    for node, details in data.items():
        if node != "Intrusion_detected":
            if 'motion' in details['sensors']:
                if details.get('on_alert') and details['sensors']['motion'] == "Motion Detected":
                    invasion_detected = True
                    msg += f"Invasion detected in {node} - Motion: Motion Detected<br>"
            if 'door' in details['sensors']:
                if details.get('on_alert') and details['sensors']['door'] == "Open":
                    invasion_detected = True
                    msg += f"Invasion detected in {node} - Door: Open<br>"

    if not invasion_detected:
        msg = "All Clear. No Intrusions Detected."

    # Update JSON file and broadcast state
    data["Intrusion_detected"] = invasion_detected
    save_data(data)
    socketio.emit("intrusion_status", {"Intrusion_detected": invasion_detected, "message": msg})
    return msg


# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(TEST_BROKER_IP, PORT, 60)

# Start the MQTT client loop in a separate thread
mqtt_client.loop_start()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/security')
def security():
    data = load_data()
    check_result = check_intrusion()

    # Filter only security-related data
    for node, details in data.items():
        if node != "Intrusion_detected":
            details["sensors"] = details["sensors"].get('security', {})
    return render_template("security.html",
                           nodes=data,
                           message=check_result,
                           intrusion_detected=invasion_detected
                           )


@app.route('/thermal')
def thermal():
    return "Thermal Comfort page under construction!"  # Replace with your thermal view template later


@app.route('/settings')
def settings():
    return "Settings page under construction!"  # Replace with your settings view template later


@app.route("/api/toggle_alarm", methods=["POST"])
def toggle_alarm():
    data = load_data()
    request_data = request.get_json()
    node = request_data.get("node")
    if node in data:
        # Toggle the alarm state
        data[node]["on_alert"] = not data[node]["on_alert"]
        save_data(data)  # Persist changes to JSON file

        # Emit the update via Socket.IO
        socketio.emit('update_node', {node: data[node]})

        return jsonify({"message": f"Alarm for {node} is now {'Active' if data[node]['on_alert'] else 'Stand-by'}"}), 200
    return jsonify({"error": "Node not found"}), 404


@app.route('/api/toggle_all_alarms', methods=['POST'])
def toggle_all_alarms():
    try:
        data = load_data()
        request_data = request.get_json()
        enable = request_data.get("enable")
        print(enable)
        if enable is None:
            return jsonify({"error": "Missing 'enable' field in request payload."}), 400

        # Update all nodes and persist changes
        for node in data:
            if node != "Intrusion_detected":
                data[node]["on_alert"] = enable
        save_data(data)

        # Emit the update via Socket.IO
        socketio.emit('update_all', {'on_alert': enable})

        return jsonify({"message": f"All alarms {'enabled' if enable else 'disabled'} successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reset_alarm", methods=["POST"])
def reset_alarm():
    global invasion_detected
    invasion_detected = False

    # Notify all clients that the alarm has been reset
    socketio.emit("alarm_status", {"status": "Everything is ok..."})
    return jsonify({"message": "Alarm reset successfully."})

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
    socketio.run(app, debug=True, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)

    # try:
    #     # Run Flask app
    #     app.run(host='0.0.0.0', debug=True)
    # except KeyboardInterrupt:
    #     shutdown_handler(None, None)
