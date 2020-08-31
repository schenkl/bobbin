#!/usr/bin/python3

import time
import board
import atexit
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper as stepper
import serial
import pdb
import threading
import RPi.GPIO as GPIO
from flask import Flask, render_template, request
import os

#global variables from web page to all other threads
STANDBY = 0
START = 1
RUN = 2
RESET = 3

LEFT = 1
RIGHT = 2
STOP = 0

motor1 = STANDBY
motor2 = STANDBY

M1_rotations = 0
M2_rotations = 0
M1_speed = 10
M2_speed = 20
M1_direction = STOP
M2_direction = STOP


#lcd section
Port = '/dev/ttyAMA0'

#contro sequences to LCD display: all start with 0xfe
#       0x42 display on
#       0x46 display off
#       0x99 brightness same as 0x98
#       0x50 set contrast 180-220 are good values  also 0x91
#       0x51 auto scroll on
#       0x52 auto scroll off
#       0x58 clear screen
#       0x40 splash screen
#       0x47 place cursor
#       0x48 home cursor
#       0x4c move cursor backone space
#       0x4d as above?
#       0x4a underline text
#       0x4b turn off underline text
#       0x53 blinking cursor on
#       0x54 bkinking cursor off
#       0xd0 set background color (3 numbers 0-255) RGB
#       0xd1 set lcd display size
#


Serial_comm = -1

def lcd_thread():
	global M1_speed,M2_speed,M1_rotations,M2_rotations
	print("lcd_thread starting")
	while True:
		print("lcd_thread running")
		#print('lcd_thread M1_rotations = ',M1_rotations)
		report_M1_rotations(M1_rotations)
		time.sleep(10)
	return

def M1_thread():		#string positioner
	global M1_speed,M2_speed,M1_rotations,M2_rotations,M1_direction,M2_direction
	print("M1_thread starting")
	while True:
		#print("test_thread running")
		time.sleep(1)
		print('M1_thread:loop M1_direction = ',M1_direction)
		if M1_direction != STOP:
			print('Turning on M1 in direction: ',M1_direction)
			time.sleep(3)
			M1_direction = STOP
			print('M1_tread turning off M1_direction to STOP',M1_direction)
	return

def M2_thread():		#bobbin spinner
	global M1_speed,M2_speed,M1_rotations,M2_rotations
	print("M2_thread starting")
	while True:
		#print("test_thread running")
		time.sleep(1)
		#M1_rotations = M1_rotations + 1
	return


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

def lcd_init():         #screen on, cursor at 1,1 cursor off
        global Serial_comm,Ser
        if (Serial_comm == 1):
                Ser.write('\xfe\x42')
                Ser.write('\xfe\x48')
                Ser.write('\xfe\x54')
                Ser.write('\xfe\x4b')


def report_M1_rotations(val):
	global M1_rotations
	print('report_M1_rotations : ', M1_rotations)
	return


#flask section...
app = Flask(__name__)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#define sensors GPIOs
button = 20
senPIR = 16
#define actuators GPIOs
ledRed = 13
ledYlw = 19
ledGrn = 26
#initialize GPIO status variables
buttonSts = 0
senPIRSts = 0
ledRedSts = 0
ledYlwSts = 0
ledGrnSts = 0
# Define button and PIR sensor pins as an input
GPIO.setup(button, GPIO.IN)   
GPIO.setup(senPIR, GPIO.IN)
# Define led pins as output
GPIO.setup(ledRed, GPIO.OUT)   
GPIO.setup(ledYlw, GPIO.OUT) 
GPIO.setup(ledGrn, GPIO.OUT) 
# turn leds OFF 
GPIO.output(ledRed, GPIO.LOW)
GPIO.output(ledYlw, GPIO.LOW)
GPIO.output(ledGrn, GPIO.LOW)
	
#@app.route("/", methods=['POST', 'GET'])
#def index():
	# Read GPIO Status
	#buttonSts = GPIO.input(button)
	#senPIRSts = GPIO.input(senPIR)
	#ledRedSts = GPIO.input(ledRed)
	#ledYlwSts = GPIO.input(ledYlw)
	#ledGrnSts = GPIO.input(ledGrn)
	#templateData = {
      		#'button'  : buttonSts,
      		#'senPIR'  : senPIRSts,
      		#'ledRed'  : ledRedSts,
      		#'ledYlw'  : ledYlwSts,
      		#'ledGrn'  : ledGrnSts,
      	#}
	#return render_template('index.html')
	
@app.route("/", methods=['POST', 'GET'])
def submit(): 
	global M1_rotations,M1_direction
	if request.method == "POST":
		if request.form.get("calibrate"):
			print('calibrate')
			#M1_rotations = 1000
		elif request.form.get("start_winding"):
			print('start_winding')
			#M1_rotations = 1000
		elif request.form.get("reboot"):
			print('request to reboot')
			os.system("sudo reboot")
		elif request.form.get("shutdown"):
			print('request to shutdown')
			os.system("sudo shutdown -h now")
		elif request.form.get("left"):
			print('request to move left')
			M1_direction = LEFT
			print('setting M1_direction to ',M1_direction)
		elif request.form.get("right"):
			print('request to move right')
			M1_direction = RIGHT
		elif request.form.get("stop"):
			print('request to stop')
			M1_direction = STOP
	elif request.method == "GET":
			# do something
			print('request.method')
			#M1_rotations = 1000
	return render_template('index.html')


#@app.route("/calibrate")
#def calibrate():
	#calibrate_position()
	#return render_template('index.html')

#@app.route("/<deviceName>/<action>")
#def action(deviceName, action):
	#if deviceName == 'ledRed':
		#actuator = ledRed
	#if deviceName == 'ledYlw':
		#actuator = ledYlw
	#if deviceName == 'ledGrn':
		#actuator = ledGrn
   #
	#if action == "on":
		#GPIO.output(actuator, GPIO.HIGH)
	#if action == "off":
		#GPIO.output(actuator, GPIO.LOW)
		     #
	#buttonSts = GPIO.input(button)
	#senPIRSts = GPIO.input(senPIR)
	#ledRedSts = GPIO.input(ledRed)
	#ledYlwSts = GPIO.input(ledYlw)
	#ledGrnSts = GPIO.input(ledGrn)
   #
	#templateData = {
	 	#'button'  : buttonSts,
      		#'senPIR'  : senPIRSts,
      		#'ledRed'  : ledRedSts,
      		#'ledYlw'  : ledYlwSts,
      		#'ledGrn'  : ledGrnSts,
	#}
	#return render_template('index.html', **templateData)
#
#def calibrate_position():
	#print("Moving M2")


#def flask_thread():
	#t3 = app.run(host='0.0.0.0', port=5000, debug=False)
	#t3.start()


if __name__ == "__main__":
	#flask_thread()
	#print('starting lcd_thread')
	t = threading.Thread(target=lcd_thread)
	t.start()
	print('starting test_thread')
	t2 = threading.Thread(target=M1_thread)
	t2.start()
	t4 = threading.Thread(target=M2_thread)
	t4.start()
	print('starting thread ',app)
	print("starting web server")
	t3 = threading.Thread(app.run(host='0.0.0.0', port=5000, debug=False))
	t3.start()
	#app.run(host='0.0.0.0', port=5000, debug=True)
	print('main thread')
	while(True):
		print('Main_thread')
		time.sleep(5)
