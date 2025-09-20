import RPi.GPIO as GPIO
import time
import cv2
import pytesseract
from smbus2 import SMBus

TARGET_CODE = "1234"
DISTANCE_THRESHOLD = 20

TRIG = 23
ECHO = 24
SERVO = 18
RED_LED = 5
GREEN_LED = 6
BUZZER = 16

I2C_ADDR = 0x27
bus = SMBus(1)

def lcd_write_cmd(cmd):
    bus.write_byte(I2C_ADDR, cmd)
    time.sleep(0.01)

def lcd_clear():
    lcd_write_cmd(0x01)

def lcd_message(msg):
    lcd_clear()
    print("LCD:", msg)

def measure_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.0002)
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    while GPIO.input(ECHO) == 0:
        start = time.time()
    while GPIO.input(ECHO) == 1:
        end = time.time()
    duration = end - start
    dist = duration * 17150
    return dist

def set_servo(angle):
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)

def read_plate(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, config="--psm 7 -c tessedit_char_whitelist=0123456789")
    digits = "".join([c for c in text if c.isdigit()])
    return digits

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(SERVO, GPIO.OUT)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

pwm = GPIO.PWM(SERVO, 50)
pwm.start(0)

cap = cv2.VideoCapture(0)

try:
    while True:
        dist = measure_distance()
        print("Distance:", dist)
        if dist <= DISTANCE_THRESHOLD:
            lcd_message("Scanning...")
            ret, frame = cap.read()
            if not ret:
                continue
            digits = read_plate(frame)
            print("Detected:", digits)
            if digits == TARGET_CODE:
                lcd_message("Access Accept")
                GPIO.output(GREEN_LED, 1)
                set_servo(90)
                time.sleep(3)
                GPIO.output(GREEN_LED, 0)
            else:
                lcd_message("Access Deny")
                GPIO.output(RED_LED, 1)
                GPIO.output(BUZZER, 1)
                time.sleep(2)
                GPIO.output(RED_LED, 0)
                GPIO.output(BUZZER, 0)
        time.sleep(1)

except KeyboardInterrupt:
    cap.release()
    pwm.stop()
    GPIO.cleanup()
