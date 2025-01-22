import json
from threading import Lock, Thread
from utils import DEFAULT_JSON


class ThermalManager:
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

        self.socketio.emit("update_node", data)
        print(f"Updated thermals data for node {node}")
        return

    def auto_correct_json(self):
        # Handle a potential corrupted file
        try:
            print("Reading raw content for manual correction...")
            with open(self.file_path, "r") as f:
                raw_content = f.read().strip()

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
            else:
                return True
        except Exception as e:
            print(f"Unexpected error during manual correction: {e}")

            # Fallback to default JSON structure
            print("Falling back to default JSON...")
            self.save_data(DEFAULT_JSON)
            return False
