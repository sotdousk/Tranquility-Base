from machine import Pin
import time
import network
from umqtt.simple import MQTTClient

motion_detected = False  # Global variable to store the state of the pir sensor

def handle_interrupt(pin):
    global motion_detected
    motion_detected = True
    
led = Pin(14, Pin.OUT)  # set GPIO14 (LED) as output
PIR_Interrupt = Pin(13, Pin.IN)  # set GPIO13 (PIR_Interrupt) as input

# Create an object, wlan, which is then used to connect to Wi-Fi acces point.
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("VODAFONE_H268Q-7791", "ES5bcz7FYcTRySxt")

# Attach external interrupt to GPIO13 and rising edge as an external event
PIR_Interrupt.irq(trigger=Pin.IRQ_RISING, handler=handle_interrupt)

def blink_once():
    led.value(1)
    time.sleep(0.5)
    led.value(0)
    time.sleep(0.5)

time.sleep(5)
if wlan.isconnected():
    blink_once()
    
mqtt_server = '192.168.2.8'
client_id = 'listener'
topic_sub = b'MyHouse/testLED'
        
def mqtt_connect():
    client = MQTTClient(client_id, mqtt_server, keepalive=60)
    # client.set_callback(sub_cb)
    client.connect()
    print("Connected to %s MQTT Broker" %(mqtt_server))
    return client

def reconnect():
    print("Failed to connect to MQTT Broker. Reconnecting...")
    machine.reset()
    
try:
    client = mqtt_connect()
except OSError as e:
    reconnect()

time.sleep(3)


while True:
    try:
        if motion_detected:
            print("Motion is detected!")
            client.publish(topic_sub, 'blink')
            led.value(1)
            time.sleep(5)
            led.value(0)
            print("Motion stopped!")
            motion_detected = False
        else:
            led.value(1)
            time.sleep(0.5)
            led.value(0)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Exiting gently...")
        led.value(0)
        break
    
print("Bye...")