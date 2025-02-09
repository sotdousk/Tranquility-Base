import json
from utils import DEFAULT_JSON
from threading import Lock, Thread
from gpiozero import LED


class SecurityManager:
    def __init__(self, socketio, mqtt_client, file_path="./data/nodes.json"):
        self.file_path = file_path
        self.socketio = socketio
        self.mqtt_client = mqtt_client
        self.data_lock = Lock()
        self.alarmLED = 4

    # Load JSON data
    def load_data(self):
        with self.data_lock:
            try:
                print("Calling security load data.")
                with open(self.file_path, "r") as f:
                    print("Loading data from file")
                    data = json.load(f)
                    print(f"Data loaded: {data}")
                    return data
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print("Attempting to auto-correct...")
                return self.auto_correct_json()
            except FileNotFoundError:
                print(f"JSON file not found. Creating default JSON.")
                self.save_data(DEFAULT_JSON)
                return DEFAULT_JSON

    # Save JSON data
    def save_data(self, data):
        with self.data_lock:
            try:
                with open(self.file_path, "w") as f:
                    json.dump(data, f, indent=4)  # This ensures valid JSON formatting
                print("Data saved successfully!")
            except Exception as e:
                print(f"Error saving JSON: {e}")

    def handle_security_packet(self, node, node_data):
        print(f"Handling security packet for node: {node}")

        # Load current data
        data = self.load_data()

        # Ensure the node exists in data
        if node not in data:
            print("Node not found. Initializing...")
            data[node] = {
                "on_alert": False,
                "sensors": {
                    "security": {"door": "N/A", "motion": "N/A"},
                    "thermals": {"temperature": "N/A", "humidity": "N/A"}
                }
            }

        # Update security sensors data
        data[node]["sensors"]["security"].update(node_data.get("sensors", {}).get("security", {}))

        # Check for intrusion
        data = self.check_for_intrusion(data)

        # Save data and broadcast updates
        self.save_data(data)
        # self.socketio.emit("update_node", {node: data[node]}, namespace="/security")
        self.socketio.emit("update_node", data)
        print(f"Updated security data for node {node}")
        return

    def check_for_intrusion(self, data):
        # Preserve the current reset_by_user state
        reset_by_user = data["Intrusion_detected"].get("reset_by_user", True)
        intrusion_detected = data["Intrusion_detected"].get("status", False)
        nodes_detected = data['Intrusion_detected'].get('nodes_detected', [])
        print(f"Current reset_by_user: {reset_by_user}")

        # Check for intrusion
        for node_name, details in data.items():
            if node_name not in {"Intrusion_detected"} and details.get("on_alert"):
                security = details.get("sensors", {}).get("security", {})
                if security.get("motion") == "Motion Detected" or security.get("door") == "Open":
                    intrusion_detected = True
                    reset_by_user = False
                    if node_name not in nodes_detected:
                        nodes_detected.append(node_name)

        # Update only status and nodes_detected, preserve reset_by_user
        data["Intrusion_detected"] = {
            "status": intrusion_detected,
            "nodes_detected": nodes_detected,
            "reset_by_user": reset_by_user  # Preserve the value
        }
        
        if data["Intrusion_detected"]["status"]:
            self.alarmLED.on()

        print(f"Updated Intrusion_detected: {data['Intrusion_detected']}")
        return data

    def reset_intrusion(self):
        print("Entered reset_intrusion method")
        data = self.load_data()
        print(f"Resetting intrusion. Current state: {data['Intrusion_detected']}")

        # Reset manually
        data["Intrusion_detected"] = {
            "status": False,
            "nodes_detected": [],
            "reset_by_user": True  # Explicitly set to True
        }
        
        # Turn alarm LED off
        self.alarmLED.off()

        self.save_data(data)
        self.socketio.emit("update_node", data)
        print(f"Intrusion reset. New state: {data['Intrusion_detected']}")

    def publish_sync_on_alert(self, node_name, new_state):
        # Prepare the MQTT payload to publish the update
        payload = json.dumps({
            node_name: {
                "on_alert": new_state
            }
        })
        # Publish the MQTT message to notify the node
        mqtt_topic = f"home/automation/update/on_alert/{node_name}"
        self.mqtt_client.publish(mqtt_topic, payload)
        print(f"MQTT message published for {node_name}: {payload}")

    def toggle_node_alert(self, node_name, on_alert):
        data = self.load_data()
        if node_name in data:
            data[node_name]["on_alert"] = on_alert
            self.save_data(data)

            # Publish the new state to MQTT
            self.publish_sync_on_alert(node_name, on_alert)
            print(f"{node_name} notified successfully.")

            # Emit the update via Socket.IO
            self.socketio.emit('update_node', {node_name: data[node_name]})
        else:
            print(f"Node {node_name} not found. Unable to toggle alert.")
        return None

    def auto_correct_json(self):
        # Handle a potential corrupted file
        try:
            print("Reading raw content for manual correction...")
            with open(self.file_path, "r") as f:
                raw_content = f.read().strip()
            # Replace single quotes with double quotes (only if the content is malformed)
            raw_content = raw_content.replace("'", '"')
            # Attempt to fix malformed JSON
            if raw_content.endswith("}}"):
                print("Found issue with double angle brackets.")
                raw_content = raw_content[:-1]  # Remove the extra closing brace

            # Parse the corrected content
            content = json.loads(raw_content)
            print("Corrected JSON parsed successfully. Writing back to file...")
            self.save_data(content)
            print("Auto-correction successful!")
            return True
        except Exception as e:
            print(f"Unexpected error during manual correction: {e}")

            # Fallback to default JSON structure
            print("Falling back to default JSON...")
            self.save_data(DEFAULT_JSON)
            return False

    def auto_correct_json_with_timeout(self, timeout=5):
        result = [None]  # Mutable object to store the result across threads

        def target():
            try:
                result[0] = self.auto_correct_json()
            except Exception as e:
                print(f"Error in auto-correction thread: {e}")

        thread = Thread(target=target)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            print("Auto-correction timed out. Using default JSON.")
            return DEFAULT_JSON

        return result[0]
