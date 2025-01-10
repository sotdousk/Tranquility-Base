import json
from threading import Lock


class SecurityManager:
    def __init__(self, socketio, file_path="./data/nodes.json"):
        self.file_path = file_path
        self.socketio = socketio
        self.intrusion_detected = False
        self.data_lock = Lock()

    # Load JSON data
    def load_data(self):
        with self.data_lock:
            print("Calling security load data.")
            with open(self.file_path, "r") as f:
                return json.load(f)

    # Save JSON data
    def save_data(self, data):
        with self.data_lock:
            with open(self.file_path, "w") as f:
                json.dump(data, f, indent=4)

    def handle_security_packet(self, node, node_data):
        print(f"Handling security packet for node: {node}")

        # Load current data
        data = self.load_data()
        print("Extract stored data.")
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
        print("Updating sensors data")
        # Update security sensors data
        data[node]["sensors"]["security"].update(node_data.get("sensors", {}).get("security", {}))
        print("Data exchanged successfully.")
        self.check_for_intrusion(data)
        data["Intrusion_detected"] = self.intrusion_detected
        # Save data and broadcast updates
        self.save_data(data)
        print("Data updated successfully!")

        # In SecurityManager
        self.socketio.emit("update_node", {node: data[node]}, namespace="/security")

        print(f"Updated security data for node {node}")

    def check_for_intrusion(self, data):
        # Check for intrusion
        self.intrusion_detected = any(
            node.get('on_alert') and (
                node["sensors"]["security"]["motion"] == "Motion Detected" or
                node["sensors"]["security"]["door"] == "Open"
            )
            for node_name, node in data.items()
            if node_name not in {"Intrusion_detected", "intrusion_message"}
        )
        return None

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

    def check_intrusion_as_boolean(self):
        data = self.load_data()
        for node_name, details in data.items():
            if node_name not in {"Intrusion_detected", "intrusion_message"}:
                if details.get('on_alert'):
                    self.intrusion_detected = any(
                        details["sensors"]["security"]["motion"] == "Motion Detected" or
                        details["sensors"]["security"]["door"] == "Open"
                    )
                    return True
        return False

    @staticmethod
    def initialize_node(node, data):
        if node not in data:
            data[node] = {
                "on_alert": False,
                "sensors": {
                    "security": {"door": "N/A", "motion": "N/A"},
                    "thermals": {"temperature": "N/A"}
                }
            }
