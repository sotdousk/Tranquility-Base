import json
import time
from datetime import datetime, timedelta
from threading import Lock, Thread
from utils import DEFAULT_JSON, DEFAULT_HISTORICAL_JSON


class ThermalManager:
    def __init__(self, socketio, file_path="./data/nodes.json",
                 historical_path="./data/thermals_historical.json"):
        self.file_path = file_path
        self.historical_path = historical_path
        self.socketio = socketio
        self.data_lock = Lock()
        self.historical_data = self.load_historical_data()

    # Load JSON data
    def load_data(self):
        with self.data_lock:
            try:
                print("Calling thermals load data.")
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

    def load_historical_data(self):
        """Load historical thermal data."""
        with self.data_lock:
            try:
                with open(self.historical_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.save_historical_data(DEFAULT_HISTORICAL_JSON)
                return DEFAULT_HISTORICAL_JSON

    def save_historical_data(self, data):
        """Save historical thermal data."""
        with self.data_lock:
            with open(self.historical_path, "w") as f:
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
                    "thermals": {"temperature": "N/A", "humidity": "N/A"}
                }
            }

        # Update security sensors data
        data[node]["sensors"]["thermals"].update(node_data.get("sensors", {}).get("thermals", {}))

        thermals = data[node]["sensors"]["thermals"]
        if (thermals["temperature"] is not None) or (thermals["humidity"] is not None):
            self.store_thermal_history(node, thermals)

        # Save data and broadcast updates
        self.save_data(data)

        self.socketio.emit("update_node", data)
        print(f"Updated thermals data for node {node}")
        return

    def store_thermal_history(self, node, thermal_data):
        """Store averaged temperature every 15 minutes and remove old data, for each node."""
        now = datetime.now()
        rounded_timestamp = now.replace(minute=(now.minute // 15) * 15, second=0, microsecond=0).isoformat()
        cutoff_time = (now - timedelta(hours=24)).isoformat()  # 24-hour threshold

        historical_data = self.load_historical_data()

        for thermal in {"temperature", "humidity"}:
            if thermal in thermal_data:  # Ensure data exists
                # Retrieve timestamps and values
                timestamps = historical_data[node][thermal]["timestamp"]
                values = historical_data[node][thermal]["values"]

                # Check id last stored timestamp matches the current interval
                if timestamps and timestamps[-1] == rounded_timestamp:
                    # If we already have a value for this 15-min interval, update the average
                    prev_avg = values[-1]
                    new_avg = (prev_avg + thermal_data[thermal]) / 2
                    historical_data[node][thermal]["values"][-1] = new_avg  # Replace last entry
                else:
                    # Store new entry for this interval
                    timestamps.append(rounded_timestamp)
                    values.append(thermal_data[thermal])

                # Remove outdated data
                while historical_data[node][thermal]["timestamp"] and \
                        historical_data[node][thermal]["timestamp"][0] < cutoff_time:
                    historical_data[node][thermal]["timestamp"].pop(0)
                    historical_data[node][thermal]["values"].pop(0)

        # Save updated historical data
        self.save_historical_data(historical_data)

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
