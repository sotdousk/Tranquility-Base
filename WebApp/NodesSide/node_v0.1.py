import machine
import time
import network
from umqtt.simple import MQTTClient
import ujson

# MQTT Configuration
BROKER = "192.168.2.5"  # This should contain broker's IP
TOPIC = "home/automation/pico"
NODE_NAME = "Node1"

# GPIO Pins
TEMP_SENSOR_PIN = 26  # Pin for temperature sensor (TMP36 on ADC)
DOOR_SENSOR_PIN = 15  # Pin for door switch
MOTION_SENSOR_PIN = 16  # Pin for motion sensor

# Initialize sensors
adc = machine.ADC(TEMP_SENSOR_PIN)
door_sensor = machine.Pin(DOOR_SENSOR_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
motion_sensor = machine.Pin(MOTION_SENSOR_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# WiFi Configuration
WIFI_SSID = "VODAFONE_H268Q-7791"
WIFI_PASSWORD = "ES5bcz7FYcTRySxt"

# MQTT Client
client = MQTTClient(NODE_NAME, BROKER)


# Connect to WiFi
def connect_to_wifi():
	wlan = network.WLAN(network.STA_IF)
	wlan.active(True)
	wlan.connect(WIFI_SSID, WIFI_PASSWORD)
	while not wlan.isconnected():
		print("Trying to connect...")
		time.sleep(1)
	print(f"Connected to WiFi: {wlan.ifconfig()}")


# Publish sensor data
def publish_data():
	temperature = read_temperature()

	payload = {
		NODE_NAME: {
			"alarm": False,  # Adjust as needed, if the alarm status is tracked on the Pico
			"sensors": {
				"temperature": round(temperature, 2),
				"door": "Open" if door_sensor.value() == 1 else "Closed",
				"motion": "Motion Detected" if motion_sensor.value() == 1 else "No Motion"
			}
		}
	}
	# Publish the data to the MQTT topic
	client.publish(TOPIC, ujson.dumps(payload))
	print(f"Data sent: {ujson.dumps(payload)}")


# Read temperature from sensor (TMP36)
def read_temperature():
	# Sensor outputs 10mV per degree Celsius
	voltage = adc.read_u16() * (3.3 / 65535)  # Convert ADC value to voltage
	# Previous implementation: return voltage * 100  # Convert to temperature in Celsius
	degC = (100 * voltage) - 50  # Convert to temperature in Celsius
	return degC


# Interrupt Handlers
def door_change_handler(pin):
	print("Door sensor state changed!")
	publish_data()


def motion_change_handler(pin):
	print("Motion sensor state changed!")
	publish_data()


# Main Logic
def main():
	connect_to_wifi()
	client.connect()

	# Attach Interrupts
	door_sensor.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING, handler=door_change_handler)
	motion_sensor.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING, handler=motion_change_handler)

	# Periodic temperature updates
	while True:
		publish_data()
		time.sleep(10)


try:
	main()
except KeyboardInterrupt:
	print("Program terminated.")

