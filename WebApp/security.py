import json
from threading import Lock


class SecurityManager:
    def __init__(self, socketio, file_path="./data/nodes.json"):
        self.file_path = file_path
        self.socketio = socketio
        self.data_lock = Lock()

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
            with open(self.file_path, "w") as f:
                json.dump(data, f, indent=4)

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
                    "thermals": {"temperature": "N/A"}
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

    @staticmethod
    def check_for_intrusion(data):
        # Preserve the current reset_by_user state
        reset_by_user = data["Intrusion_detected"].get("reset_by_user", True)
        intrusion_detected = data["Intrusion_detected"].get("status", False)
        nodes_detected = data['Intrusion_detected'].get('nodes_detected', [])
        print(f"Current reset_by_user: {reset_by_user}")

        # intrusion_detected = False
        # nodes_detected = []

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

        self.save_data(data)
        self.socketio.emit("update_node", data)
        print(f"Intrusion reset. New state: {data['Intrusion_detected']}")

    def toggle_node_alert(self, node_name, on_alert):
        data = self.load_data()
        if node_name in data:
            data[node_name]["on_alert"] = on_alert
            self.save_data(data)

            # TODO: Leave for now
            # # Publish the new state to MQTT
            # publish_synch_on_alert(node, "on_alert", data[node]["on_alert"])

            # Emit the update via Socket.IO
            self.socketio.emit('update_node', {node_name: data[node_name]})
        else:
            print(f"Node {node_name} not found. Unable to toggle alert.")
        return None

    def auto_correct_json(self):
        try:
            with open(self.file_path, "r") as file:
                content = file.read()

            # Auto-correct logic: strip extra braces or fix common issues
            content = content.strip()
            if content.endswith("}}"):
                content = content[:-1]  # Remove the extra closing brace

            # Try parsing again
            return json.loads(content)
        except Exception as e:
            print(f"Auto-correction failed: {e}")
            print("Falling back to default JSON.")
            self.save_data(DEFAULT_JSON)
            return DEFAULT_JSON


DEFAULT_JSON = {
    "Node1": {
        "on_alert": False,
        "sensors": {
            "security": {
                "door": "Closed",
                "motion": "No Motion"
            },
            "thermals": {
                "temperature": 16.4
            }
        }
    },
    "Node2": {
        "on_alert": False,
        "sensors": {
            "security": {
                "door": "Closed",
                "motion": "No Motion"
            },
            "thermals": None
        }
    },
    "Intrusion_detected": {
        "status": False,
        "nodes_detected": [],
        "reset_by_user": True
    }
}