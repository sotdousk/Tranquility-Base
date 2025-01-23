import os
import signal
import sys
import json
from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt

from security import SecurityManager
from thermal import ThermalManager
from flask_socketio import SocketIO


app = Flask(__name__)
# Instantiate the socketio object
socketio = SocketIO()
socketio.init_app(app)
DATA_FILE = "./data/nodes.json"

# MQTT Configuration
TEST_BROKER_IP = "192.168.2.5"
BROKER = "mqtt.eclipseprojects.io"  # Replace with your broker's address
PORT = 1883  # Default MQTT port
TOPIC = "home/automation/#"  # Subscribe to all subtopics under 'home/automation'


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker {TEST_BROKER_IP} with result code {rc}")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: {TOPIC}")
    else:
        print(f"Failed to connect, return code: {rc}")


def on_message(client, userdata, message):
    print("New message arrived!")
    print(f"on_message triggered by topic: {message.topic}")
    try:
        raw_payload = message.payload.decode()
        if not raw_payload.strip():
            print("Empty MQTT payload received. Skipping...")
            return

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as e:
            return

        print(f"Decoded payload: {payload}")
        node = list(payload.keys())[0]
        node_data = payload[node]

        # Determine the type of incoming data
        known_packet = False
        if "security" in node_data.get("sensors", {}):
            known_packet = True
            print("Call handler from security manager.")
            security_manager.handle_security_packet(node, node_data)
        if "thermals" in node_data.get("sensors", {}):
            known_packet = True
            thermals_manager.handle_thermal_packet(node, node_data)

        # Inform on whether the packet has been identified
        if not known_packet:
            print("Unknown type of MQTT packet. Skipping...")

    except Exception as e:
        # TODO: Fix error with trailing }
        print(f"Error in on_message: {e} - trying to autocorrect...")
        data = security_manager.auto_correct_json_with_timeout()
        if data:
            print("Auto-correction succeeded.")
        else:
            print("Auto-correction failed or timed out.")


# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(TEST_BROKER_IP, PORT, 60)

# Start the MQTT client loop in a separate thread
mqtt_client.loop_start()

security_manager = SecurityManager(socketio, mqtt_client, DATA_FILE)
thermals_manager = ThermalManager(socketio, DATA_FILE)


@app.route('/')
def home():
    return render_template('home.html')


# @app.route('/test_endpoint')
# def test_endpoint():
#     data = load_data()  # Assuming this loads the JSON file
#     print(f"Data passed to template: {data}")
#     return render_template('security.html', nodes=data)


@app.route('/security')
def security():
    data = security_manager.load_data()

    # Filter only security-related data
    for node, details in data.items():
        if node not in ["Intrusion_detected", "intrusion_message"]:
            details["sensors"]['security'] = details["sensors"].get('security', {})

    return render_template("security.html",
                           nodes=data)


@app.route('/thermal')
def thermal():
    return "Thermal Comfort page under construction!"  # Replace with your thermal view template later


@app.route('/settings')
def settings():
    return "Settings page under construction!"  # Replace with your settings view template later


@app.route('/reset_intrusion', methods=['POST'])
def reset_intrusion():
    try:
        print("Endpoint for resetting intrusion")
        print("Calling reset_intrusion method...")
        result = security_manager.reset_intrusion()
        print("Reset_intrusion method executed:", result)
        # Notify clients about the reset
        socketio.emit('intrusion_reset', {'status': False})

        return jsonify({"success": True, "message": "Intrusion alarm reset successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {e}"}), 500


@socketio.on("toggle_node")
def handle_toggle_node(data):
    try:
        node_name = data["node"]
        on_alert = data["on_alert"]
        print(f"Toggling alert state for node: {node_name} to {on_alert}")

        # Update the alert state using the SecurityManager
        security_manager.toggle_node_alert(node_name, on_alert)
    except Exception as e:
        print(f"Error handling toggle_node event: {e}")


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
