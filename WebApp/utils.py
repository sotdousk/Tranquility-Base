import datetime

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
                "door": "Closed"
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

DEFAULT_HISTORICAL_JSON = {
    "Node1": {
        "temperature": {
            "timestamp": datetime.datetime.now(),
            "values": 0.0
        },
        "humidity": {
            "timestamp": datetime.datetime.now(),
            "values": 0.0
        }
    },
    "Node2": {
        "temperature": {
            "timestamp": datetime.datetime.now(),
            "values": 0.0
        },
        "humidity": {
            "timestamp": datetime.datetime.now(),
            "values": 0.0
        }
    }
}
