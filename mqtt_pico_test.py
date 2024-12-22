from machine import Pin
import time
import network
from umqtt.simple import MQTTClient


LED = machine.Pin(16, machine.Pin.OUT)

# Create an object, wlan, which is then used to connect to Wi-Fi acces point.
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("VODAFONE_H268Q-7791", "ES5bcz7FYcTRySxt")

def blink_once():
    LED.value(1)
    time.sleep(0.5)
    LED.value(0)
    time.sleep(0.5)

time.sleep(3)
if wlan.isconnected():
    blink_once()
    
print("Bye")