import os
import signal
import sys
import json
from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt
from flask_socketio import SocketIO

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

        if "sensors" not in node_data or "security" not in node_data["sensors"]:
            print(f"Missing security sensors data for node: {node}")
        else:
            print(f"Security sensors data for node: {node} formatted as expected.")

        # Load JSON file
        data = load_data()

        # Add/update node data without overwriting `on_alert`
        if node not in data:
            print(f"Node {node} not found. Initializing default values.")
            data[node] = {
                "on_alert": False,
                "sensors": {
                    "security": {"door": "N/A", "motion": "N/A"},
                    "thermals": {"temperature": "N/A"},
                },
            }

        # Update node's sensors without overwriting the `on_alert` field
        if node in data:
            node_data["on_alert"] = data[node].get("on_alert", False)
        data[node] = node_data

        # Check for intrusions
        print("Check for intrusions")
        intrusion_detected = False
        for node_name, details in data.items():
            if node_name != "Intrusion_detected" and details["on_alert"]:
                node_security = details["sensors"]["security"]
                if node_security["motion"] == "Motion Detected" or node_security["door"] == "Open":
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


# MQTT Publish Function to synch the on_alert value
def publish_synch_on_alert(node_name, field, value):
    control_topic = f"home/automation/control/{node_name}"
    payload = json.dumps({field: value})
    mqtt_client.publish(control_topic, payload)
    print(f"Published {field}: {value} to {control_topic}")


def check_intrusion():
    global invasion_detected
    data = load_data()
    msg = ""

    # Reset the invasion flag before evaluating
    invasion_detected = False

    # Evaluate intrusion status
    for node, details in data.items():
        # Skip non-node entries like "Intrusion_detected
        if node == "Intrusion_detected":
            continue

        # Ensure the 'sensors' key exists and contains 'security' data
        sensors = details.get('sensors', {}).get('security', {})
        on_alert = details.get('on_alert', False)

        # Check motion sensor
        if on_alert and sensors.get('motion') == "Motion Detected":
            invasion_detected = True
            msg += f"Invasion detected in {node} - Motion: Motion Detected<br>"

        # Check door sensor
        if on_alert and sensors.get('door') == "Open":
            invasion_detected = True
            msg += f"Invasion detected in {node} - Door: Open<br>"

    # Log invasion status
    if invasion_detected:
        print("Invasion detected!")
    else:
        print("No invasion detected...")
    # Persist and broadcast the state
    data["Intrusion_detected"] = invasion_detected
    save_data(data)

    socketio.emit("intrusion_status", {"Intrusion_detected": invasion_detected, "message": msg})
    print(f"Broadcasting intrusion status: {invasion_detected} - {msg}")

    return msg or "All Clear. No Intrusions Detected."


@socketio.on("reset_intrusion")
def reset_intrusion():
    try:
        data = load_data()
        data["Intrusion_detected"] = False  # Reset the intrusion state
        save_data(data)
        socketio.emit("update_node", data)  # Notify clients about the reset
        print("Intrusion alarm reset successfully.")
    except Exception as e:
        print(f"Error resetting intrusion alarm: {e}")


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
    global invasion_detected
    data = load_data()
    check_result = check_intrusion()

    # Filter only security-related data
    for node, details in data.items():
        if node != "Intrusion_detected":
            details["sensors"] = details["sensors"].get('security', {})
            # Log the intrusion status and message
            print(f"Intrusion message: {check_result}")
    return render_template("security.html",
                           nodes=data,
                           intrusion_message=check_result,
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

        # Publish the new state to MQTT
        publish_synch_on_alert(node, "on_alert", data[node]["on_alert"])

        # Emit the update via Socket.IO
        socketio.emit('update_node', {node: data[node]})

        return jsonify({"message": f"Alarm for {node} is now {'Active' if data[node]['on_alert'] else 'Stand-by'}"}), \
               200
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
                publish_synch_on_alert(node, "on_alert", enable)
        save_data(data)

        # Emit the update via Socket.IO
        socketio.emit('update_all', {'on_alert': enable})

        return jsonify({"message": f"All alarms {'enabled' if enable else 'disabled'} successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/save_node_status", methods=["POST"])
def save_node_status():
    data = request.json
    node_name = data.get("node")
    on_alert = data.get("on_alert")
    print("SOT:", on_alert)

    # Update the JSON data
    with open("./data/nodes.json", "r+") as f:
        nodes_data = json.load(f)
        if node_name in nodes_data:
            nodes_data[node_name]["on_alert"] = on_alert
            publish_synch_on_alert(node_name, "on_alert", on_alert)

        # # Save the updated data back to the JSON file
        # f.seek(0)
        # json.dump(nodes_data, f, indent=4)
        # f.truncate()
    save_data(nodes_data)

    print("SOT:", nodes_data)
    return jsonify({"success": True})


@app.route("/api/save_global_status", methods=["POST"])
def save_global_status():
    data = request.json
    on_alert = data.get("on_alert")

    with open("./data/data.json", "r+") as f:
        nodes_data = json.load(f)
        for node_name, node_data in nodes_data.items():
            if node_name != "Intrusion_detected":
                node_data["on_alert"] = on_alert
                publish_synch_on_alert(node_name, "on_alert", on_alert)
        # f.seek(0)
        # json.dump(nodes_data, f, indent=4)
        # f.truncate()
        save_data(nodes_data)

    return jsonify({"success": True})


@app.route('/api/get_intrusion_status', methods=["GET"])
def get_intrusion_status():
    global invasion_detected
    intrusion_message = check_intrusion()   # Get the latest intrusion message
    return {
        "intrusion_detected": invasion_detected,
        "intrusion_message": intrusion_message
    }


@app.route("/reset_intrusion", methods=["POST"])
def reset_intrusion():
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

# TODO: 2. Based on whether an intrusion has been detected or not, the Intrusion Detected Alert \
#  changes color but the message remains the same "All clear. No intrusion detected."
# TODO: 3. Add a Reset Button
# REVIEW: Global toggle does not work as expected - Active/Standby remains unchanged and nodes do not get notified
