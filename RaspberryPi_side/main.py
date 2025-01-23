import machine
import time
import network
from machine import Pin
from umqtt.simple import MQTTClient
import ujson


class Node:
    def __init__(self, name, broker, wifi_ssid, wifi_password, temp_pin, door_pin, motion_pin, led_pin, mqtt_topic,
                 mqtt_subscr):
        self.name = name
        self.broker = broker
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password
        self.temp_pin = temp_pin
        self.door_pin = door_pin
        self.motion_pin = motion_pin
        self.led_pin = Pin(led_pin, Pin.OUT)
        self.mqtt_topic = mqtt_topic
        self.mqtt_subscr = mqtt_subscr
        self.on_alert_state = False
        self.client = None

        # Initialize sensors
        self.adc = machine.ADC(self.temp_pin)
        self.door_sensor = Pin(self.door_pin, Pin.IN, Pin.PULL_DOWN)
        self.motion_sensor = Pin(self.motion_pin, Pin.IN, Pin.PULL_DOWN)

    def connect_to_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.wifi_ssid, self.wifi_password)
        while not wlan.isconnected():
            print("Trying to connect to WiFi...")
            time.sleep(1)
        print(f"Connected to WiFi: {wlan.ifconfig()}")

    def on_message(self, topic, msg):
        try:
            print(f"Received message on topic {topic}: {msg}")
            payload = ujson.loads(msg.decode("utf-8"))

            # Update on_alert state for this node
            if self.name in payload:
                self.on_alert_state = payload[self.name]["on_alert"]

                # Perform action based on the new state
                if self.on_alert_state:
                    print("Node is now ACTIVE. Enabling alert mechanism.")
                    self.led_pin.on()
                else:
                    print("Node is now on STANDBY. Disabling alert mechanism.")
                    self.led_pin.off()
            else:
                print(f"No relevant data for this node ({self.name}). Skipping...")
        except Exception as e:
            print(f"Error processing message: {e}")

    def init_mqtt(self):
        self.client = MQTTClient(self.name, self.broker)
        self.client.set_callback(self.on_message)
        self.client.connect()
        print(f"Connected to MQTT broker at {self.broker}")
        self.client.subscribe(self.mqtt_subscr)
        print(f"Subscribed to topic: {self.mqtt_subscr}")

    def read_temperature(self):
        voltage = self.adc.read_u16() * (3.3 / 65535)
        deg_c = (100 * voltage) - 50
        return deg_c

    def publish_data(self):
        temperature = self.read_temperature()

        payload = {
            self.name: {
                "on_alert": self.on_alert_state,
                "sensors": {
                    "security": {
                        "door": "Open" if self.door_sensor.value() == 1 else "Closed",
                        "motion": "Motion Detected" if self.motion_sensor.value() == 1 else "No Motion"
                    },
                    "thermals": {
                        "temperature": round(temperature, 2)
                    }
                }
            }
        }
        self.client.publish(self.mqtt_topic, ujson.dumps(payload))
        print(f"Data sent: {ujson.dumps(payload)}")

    def door_change_handler(self, pin):
        print("Door sensor state changed!")
        self.publish_data()

    def motion_change_handler(self, pin):
        print("Motion sensor state changed!")
        self.publish_data()

    def start(self):
        # Connect to WiFi
        self.connect_to_wifi()

        # Initialize MQTT
        self.init_mqtt()

        # Attach Interrupts
        self.door_sensor.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.door_change_handler)
        self.motion_sensor.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.motion_change_handler)

        # Main loop for periodic updates
        try:
            while True:
                for i in range(5):
                    self.client.check_msg()  # Process incoming MQTT messages
                    time.sleep(1)
                self.publish_data()
                # time.sleep(5)  # Adjust frequency as needed
        except KeyboardInterrupt:
            print("Program terminated.")


# Configuration
node_config = {
    "name": "Node1",
    "broker": "192.168.2.5",
    "wifi_ssid": "VODAFONE_H268Q-7791",
    "wifi_password": "ES5bcz7FYcTRySxt",
    "temp_pin": 26,
    "door_pin": 15,
    "motion_pin": 16,
    "led_pin": 14,
    "mqtt_topic": "home/automation/node_report/node1",
    "mqtt_subscr": "home/automation/update/on_alert/Node1",
}

# Create and start the node
node = Node(**node_config)
node.start()
