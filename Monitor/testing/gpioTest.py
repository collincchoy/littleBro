import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

#GPIO Setup
GPIO.setup(18, GPIO.OUT) #Red
GPIO.setup(23, GPIO.OUT) #Green
GPIO.setup(24, GPIO.OUT) #Blue

#set all to low to start
GPIO.output(18, GPIO.LOW)
GPIO.output(23, GPIO.LOW)
GPIO.output(24, GPIO.LOW)

#cycle through the three colors
#with 5 second delays in between
#red
GPIO.output(18, GPIO.HIGH)
time.sleep(5)

#green
GPIO.output(18, GPIO.LOW)
GPIO.output(23, GPIO.HIGH)
time.sleep(5)

#blue
GPIO.output(23, GPIO.LOW)
GPIO.output(24, GPIO.HIGH)
time.sleep(5)

GPIO.output(24, GPIO.LOW)
GPIO.cleanup()

#endfile



