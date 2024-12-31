import json
import time
import paho.mqtt.client as mqtt
import random

# MQTT Broker Configuration
BROKER = "192.168.2.5"  # Replace with your MQTT broker address
PORT = 1883
TOPIC = "home/automation/update"  # Topic to publish updates

# MQTT Client Setup
client = mqtt.Client()

# Simulated Node Data
node_name = "Node1"
mock_data = {
    node_name: {
        "on_alert": False,
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
    else:
        print(f"Failed to connect, return code {rc}")


client.on_connect = on_connect
client.connect(BROKER, PORT, 60)


def send_mock_data():
    alert_toggle = False  # Used to toggle alert status
    while True:
        # Update mock data dynamically
        mock_data[node_name]["sensors"]["thermals"]["temperature"] += random.uniform(-0.5, 0.5)
        mock_data[node_name]["sensors"]["security"]["motion"] = random.choice(["Motion Detected", "No Motion"])
        mock_data[node_name]["sensors"]["security"]["door"] = random.choice(["Open", "Closed"])
        alert_toggle = not alert_toggle
        mock_data[node_name]["on_alert"] = alert_toggle

        # Prepare and send payload
        payload = json.dumps(mock_data)  # Ensure this generates valid JSON
        client.publish(TOPIC, payload)

        print(f"Published: {payload} to topic {TOPIC}")
        time.sleep(5)


try:
    send_mock_data()
except KeyboardInterrupt:
    print("Simulation stopped by user")
    client.disconnect()
