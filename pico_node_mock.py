import json
import time
import paho.mqtt.client as mqtt
import random

# MQTT Broker Configuration
BROKER = "192.168.2.5"  # Replace with your MQTT broker address
PORT = 1883
TOPIC = "home/automation/update"  # Topic to publish updates


# Simulated Node Data
node_name = "Node1"
mock_data = {
    node_name: {
        "on_alert": False,  # This will be dynamically updated
        "sensors": {
            "security": {
                "door": "Closed",
                "motion": "No Motion"
            },
            "thermals": {
                "temperature": 25.0
            }
        }
    }
}


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")

        # Subscribe to control topic
        control_topic = f"home/automation/control/{node_name}"
        mock_client.subscribe(control_topic)
        print(f"Subscribed to control topic: {control_topic}")
    else:
        print(f"Failed to connect, return code {rc}")


def on_message(client, userdata, message):
    print("Control message received!")
    try:
        raw_payload = message.payload.decode()
        control_data = json.loads(raw_payload)
        print("SOT:", control_data)

        # Update on_alert field dynamically
        if "on_alert" in control_data:
            mock_data[node_name]["on_alert"] = control_data["on_alert"]
            print(f"Updated on_alert for {node_name}: {control_data['on_alert']}")
    except json.JSONDecodeError as e:
        print(f"Malformed control payload: {message.payload}. Error: {e}")


# MQTT Client Setup
mock_client = mqtt.Client()
mock_client.on_connect = on_connect
mock_client.on_message = on_message

mock_client.connect(BROKER, PORT, 60)


def send_mock_data():
    while True:
        # Update mock data dynamically
        mock_data[node_name]["sensors"]["thermals"]["temperature"] += random.uniform(-0.5, 0.5)
        mock_data[node_name]["sensors"]["security"]["motion"] = random.choice(["Motion Detected", "No Motion"])
        mock_data[node_name]["sensors"]["security"]["door"] = random.choice(["Open", "Closed"])

        # Prepare and send payload
        payload = json.dumps(mock_data)  # Ensure this generates valid JSON
        mock_client.publish(TOPIC, payload)

        print(f"Published: {payload} to topic {TOPIC}")
        time.sleep(5)


# Start the MQTT loop in a separate thread
mock_client.loop_start()

try:
    send_mock_data()
except KeyboardInterrupt:
    print("Simulation stopped by user")
    mock_client.disconnect()
