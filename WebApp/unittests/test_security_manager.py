import unittest
from unittest.mock import MagicMock


class TestSecurityManager(unittest.TestCase):
    def setUp(self):
        self.socketio = MagicMock()
        self.manager = SecurityManager(self.socketio, "test_nodes.json")
        self.manager.save_data({})

    def test_handle_security_packet(self):
        packet = {
            "Node1": {
                "sensors": {
                    "security": {"door": "Open", "motion": "No Motion"}
                }
            }
        }
        self.manager.handle_security_packet("Node1", packet["Node1"])
        data = self.manager.load_data()
        self.assertEqual(data["Node1"]["sensors"]["security"]["door"], "Open")


if __name__ == '__main__':
    unittest.main()
