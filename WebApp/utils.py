
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