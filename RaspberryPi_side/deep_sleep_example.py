import alarm
import board
import time
import digitalio

print("Waking up...")

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Flash the led
led.value = True
time.sleep(2)
led.value = False

pin_alarm = alarm.pin.PinAlarm(pin=board.D11, value=False, pull=True)

print("Sleeping")
# Exit the program, and then deep sleep until the alarm wakes us. Then restart the program.
alarm.exit_and_deep_sleep_until_alarms(pin_alarm)
