import RPi.GPIO as GPIO


led_pin_arm = 18
button_pin_arm = 4


def configure_arming_pins(button, led):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(led, GPIO.OUT)
    GPIO.output(led, GPIO.LOW)
