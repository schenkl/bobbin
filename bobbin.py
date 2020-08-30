#!/usr/bin/python3

import time
import board
import atexit
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper as stepper
import serial
import pdb
from flask import Flask, render_template, request
from threading import Thread
import RPi.GPIO as GPIO




Port = '/dev/ttyAMA0'

#contro sequences to LCD display: all start with 0xfe
#	0x42 display on
#	0x46 display off
#	0x99 brightness same as 0x98
#	0x50 set contrast 180-220 are good values  also 0x91
#	0x51 auto scroll on
#	0x52 auto scroll off
#	0x58 clear screen
#	0x40 splash screen
#	0x47 place cursor
#	0x48 home cursor
#	0x4c move cursor backone space
#	0x4d as above?
#	0x4a underline text
#	0x4b turn off underline text
#	0x53 blinking cursor on
#	0x54 bkinking cursor off
#	0xd0 set background color (3 numbers 0-255) RGB
#	0xd1 set lcd display size
#


Serial_comm = -1

kit = MotorKit(i2c=board.I2C())

#add second board....at address 0x61
#from adafruit_motorkit import MotorKit
# Initialise the first hat on the default address
#kit1 = MotorKit()
# Initialise the second hat on a different address
#kit2 = MotorKit(address=0x61)


def turnOffMotors():
	kit.stepper1.release()
	kit.stepper2.release()

atexit.register(turnOffMotors)


def connect():
	global Ser,Port
	#pdb.set_trace()
	print('trying to connect to: ',Port)
	try:
		Ser = serial.Serial(Port,115200, timeout=1)
		Serial_comm = 1
		print('Successful connection to ',Port);
		print(Ser)
	except:
		print("Unable to connect to port: ",Port)
		Serial_comm = -1
	return

def lcd_on():
	global Serial_comm, Ser
	if (Serial_comm == 1):
		Ser.write('\xfe\x01')

def lcd_off():
	global Serial_comm,Ser
	if (Serial_comm == 1):
		Ser.write('\xfe\x08')

def lcd_init():		#screen on, cursor at 1,1 cursor off
	global Serial_comm,Ser
	if (Serial_comm == 1):
		Ser.write('\xfe\x42')
		Ser.write('\xfe\x48')
		Ser.write('\xfe\x54')
		Ser.write('\xfe\x4b')


app = Flask(__name__)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#define actuators GPIOs
ledRed = 13
ledYlw = 19
ledGrn = 26
#initialize GPIO status variables
ledRedSts = 0
ledYlwSts = 0
ledGrnSts = 0
# Define led pins as output
GPIO.setup(ledRed, GPIO.OUT)
GPIO.setup(ledYlw, GPIO.OUT)
GPIO.setup(ledGrn, GPIO.OUT)
# turn leds OFF
GPIO.output(ledRed, GPIO.LOW)
GPIO.output(ledYlw, GPIO.LOW)
GPIO.output(ledGrn, GPIO.LOW)


#Flask- web page code running is separate thread
def index():
        # Read Sensors Status
        ledRedSts = GPIO.input(ledRed)
        ledYlwSts = GPIO.input(ledYlw)
        ledGrnSts = GPIO.input(ledGrn)
        templateData = {
              'title' : 'GPIO output Status!',
              'ledRed'  : ledRedSts,
              'ledYlw'  : ledYlwSts,
              'ledGrn'  : ledGrnSts,
        }
        return render_template('index.html', **templateData)


@app.route("/<deviceName>/<action>")
def action(deviceName, action):
        if deviceName == 'ledRed':
                actuator = ledRed
        if deviceName == 'ledYlw':
                actuator = ledYlw
        if deviceName == 'ledGrn':
                actuator = ledGrn

        if action == "on":
                GPIO.output(actuator, GPIO.HIGH)
        if action == "off":
                GPIO.output(actuator, GPIO.LOW)

        ledRedSts = GPIO.input(ledRed)
        ledYlwSts = GPIO.input(ledYlw)
        ledGrnSts = GPIO.input(ledGrn)

        templateData = {
              'ledRed'  : ledRedSts,
              'ledYlw'  : ledYlwSts,
              'ledGrn'  : ledGrnSts,
        }
        return render_template('index.html', **templateData)

if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=5000, debug=True)
    #t = Thread(target=app.run, args=('0.0.0.0'),
			#kwargs = {"port=5000": "debug=True"})
    t = Thread(target=Flask(bobbin), args=('0.0.0.0'),
			kwargs = {"port=5000": "debug=True"})
    print('starting thread ',app)
    t.start

