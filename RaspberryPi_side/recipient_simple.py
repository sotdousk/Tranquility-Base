import signal
import sys
import RPi.GPIO as GPIO
import time

from utilities import button_pin_arm, led_pin_arm, configure_arming_pins

armed = 0


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def button_pressed_callback(channel):
    global armed
    GPIO.output(led_pin_arm, not armed)
    armed = not armed


if __name__ == "__main__":
    configure_arming_pins(button_pin_arm, led_pin_arm)
    
    GPIO.add_event_detect(button_pin_arm, GPIO.RISING, callback=button_pressed_callback, bouncetime=200)
    
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting gently...")
            GPIO.cleanup()
            break
    
    print("Bye!")
    # signal.signal(signal.SIGINT, signal_handler)
    # signal.pause()
    
    
