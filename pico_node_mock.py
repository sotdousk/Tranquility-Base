import json
import time
import paho.mqtt.client as mqtt

# MQTT Broker Configuration
BROKER = "192.168.2.5"  # Replace with your MQTT broker address
PORT = 1883
TOPIC = "home/automation/update"  # Topic to publish updates

# MQTT Client Setup
client = mqtt.Client()

# Simulated Node Data
node_name = "Node1"  # Name of the mock sensor node
mock_data = {
    node_name: {
        "sensors": {
            "temperature": 30.8,  # Example initial temperature
            "door": "Open",       # Example initial door status
            "motion": "Motion Detected"  # Example initial motion status
        }
    }
}


# MQTT Connection Callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
    else:
        print(f"Failed to connect, return code {rc}")


# Attach the connection callback
client.on_connect = on_connect

# Connect to the MQTT broker
client.connect(BROKER, PORT, 60)


# Function to simulate sending MQTT messages
def send_mock_data():
    while True:
        # Update the mock data dynamically
        node_data = mock_data[node_name]
        node_data["sensors"]["temperature"] += 0.05  # Increment temperature slightly
        node_data["sensors"]["motion"] = (
            "No Motion" if node_data["sensors"]["motion"] == "Motion Detected" else "Motion Detected"
        )  # Toggle motion status
        node_data["sensors"]["door"] = (
            "Closed" if node_data["sensors"]["door"] == "Open" else "Open"
        )  # Toggle door status

        # Prepare payload and publish it
        payload = json.dumps(mock_data)
        client.publish(TOPIC, payload)
        print(f"Published: {payload} to topic {TOPIC}")

        # Wait before sending the next update
        time.sleep(5)


# Run the mock data sender
try:
    send_mock_data()
except KeyboardInterrupt:
    print("Stopped by user")
    client.disconnect()
