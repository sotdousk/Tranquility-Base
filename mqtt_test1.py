# An Introduction to MQTT, by Tim Richardson
# Import the paho-mqtt client library.
import time
import paho.mqtt.client as paho
from time import sleep
import sys

mqtt_server = '192.168.2.5'
topic_pub = "home/automation/#"

client = paho.Client()

if client.connect(mqtt_server, 1883, 60) != 0:
    print("Couldn't connect to the mqtt broker")
    sys.exit(1)

# client.publish(topic_pub, "Hi, paho mqtt client works fine!", 0)
client.publish(topic_pub, "LED Off", 0)
client.disconnect()

# client_id = 'test_sender'
#
# client = mqtt.Client(client_id)
# print(f"Client: {client}")
# client.connect(mqtt_server)
#
# time.sleep(5)
#
# for _ in range(5):
# 	msg = 'on'
# 	print(msg)
# 	client.publish(topic_pub, msg)
# 	time.sleep(1)
# 	msg = 'off'
# 	print(msg)
# 	client.publish(topic_pub, msg)
# 	time.sleep(1)
