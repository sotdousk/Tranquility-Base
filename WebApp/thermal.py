import json


class ThermalManager:
    def __init__(self, socketio, file_path="./data/nodes.json"):
        self.file_path = file_path
        self.socketio = socketio

    # Load JSON data
    def load_data(self):
        with open(self.file_path, "r") as f:
            return json.load(f)

    # Save JSON data
    def save_data(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def handle_thermal_packet(self, node, node_data):
        print(f"Handling thermal packet for node: {node}")

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
        data[node]["sensors"]["thermals"].update(node_data.get("sensors", {}).get("thermals", {}))

        # Save data and broadcast updates
        self.save_data(data)
        print("Data updated successfully!")

        self.socketio.emit("update_node", data)

        print(f"Updated security data for node {node}")

