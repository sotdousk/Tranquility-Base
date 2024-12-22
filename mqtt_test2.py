# An Introduction to MQTT, by Tim Richardson
# Import the paho-mqtt client library.
import time

import paho.mqtt.client as mqtt
from time import sleep
import threading

mqtt_server = '192.168.2.8'

cmnd_topic = "house/cmnd/#"
response_topic = "house/response/"
connected_topic = "house/connected/"
status_topic = "house/status/"
keepalive = 120
states = ["on", "off"]

client_id = 'Tester'


def on_message(client, userdata, msg):
	topic = msg.topic
	m_decode = str(msg.payload.decode("utf-8", "ingore"))
	message_handler(client, topic, m_decode)


def message_handler(client, topic, msg):
	print("topic:", topic)
	print("msg:", msg)
	topics = topic.split("/")
	topic_len = len(topics)
	print("in message handler")
	if topics[1] == "cmnd":
		object_name = topics[2]
		print("found:", object_name)
		print("topics len =", topic_len)
		if topic_len == 4:
			command_value = topics[3].upper()
			print("command value is", command_value)
		if topic_len == 5:
			command_value = topics[4].upper()
			print("command value is", command_value)
			command = topics[3].upper()
			print("command is", command)
			print()
			if (command_value == states[0].upper()) or (command_value == states[1].upper()):
				if update_status(client, object_name, command_value):
					send_response(client, object_name, command_value)


def on_log(client, userdata, level, buf):
	print("log: ", buf)


def update_status(client, object_name, command):
	client.sensor_status_old = client.sensor_status  # save old status here
	client.sensor_status = command
	topic = status_topic + object_name
	client.publish(topic, command)
	return True


def send_response(client, object_name, command):
	topic = response_topic + object_name
	client.publish(topic, command)


def on_connect(client, userdata, flags, rc):
	if rc == 0:
		client.connected_flag = True
		client.bad_connection_flag = False
		client.publish(connected_topic, 1, retain=True)
		client.subscribe(cmnd_topic)
	else:
		client.bad_connection_flag = True
		client.connected_flag = False


def send_heartbeat(client, cnt):
	client.publish(status_topic + "tester1/alive/", cnt)


if __name__ == "__main__":
	# Create an MQTT Client – the client ID must be unique
	client = mqtt.Client(client_id)
	# Connect the client
	client.connect(mqtt_server)
	print("Connected to %s MQTT Broker" % mqtt_server)
	time.sleep(1)
	client.on_message = on_message
	client.on_log = on_log  # set client logging
	time.sleep(1)
	# Subscribe to a topic
	client.subscribe("house/#")
	# Start listening for a message on the subscribed topics
	client.loop_start()
	print("Waiting for a message to be sent")
	# Wait forever
	counter_b, counter_s = 0, 0
	while True:
		sleep(1)
		counter_s += 1
		if counter_s == 60:
			print("Send a heartbeat. Counter:", counter_b)
			send_heartbeat(client, counter_b)
			counter_b += 1
			counter_s = 0
	# 	cmnd = input("press 'p_on' or 'p_off' to  publish a turn-on/off command\n")
	# 	if cmnd == "p_on":
	# 		client.publish("house/cmnd/led/power/on")
	# 	elif cmnd == "p_off":
	# 		client.publish("house/cmnd/led/power/off")
	# 	else:
	# 		pass




