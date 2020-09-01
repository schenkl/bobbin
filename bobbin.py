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

kit2 = MotorKit(address=0x61)
kit = MotorKit(i2c=board.I2C())


#global variables from web page to all other threads
STANDBY = 0
START = 1
RUN = 2
RESET = 3
SHUTDOWN = 4

LEFT = 1
RIGHT = 2
STOP = 0

M1_SLEEP_TIME = 0.5
M1_STEPS = 10
FULL_BOBIN = 100	#how many turns to fill the bobin....

#Motor_states
WINDING = 2
CALIBRATING = 1

M1_rotations = 0
M2_rotations = 0
M1_direction = STOP
M2_direction = STOP
M1_state = STANDBY
M2_state = STANDBY

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    kit.stepper2.release()
    kit2.stepper2.release()
    kit.stepper1.release()
    kit2.stepper1.release()
    M1_state = STANDBY
    M2_state = STANDBY

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
	global M1_speed,M2_speed,M1_rotations,M2_rotations,M1_state,M2_state
	print("lcd_thread starting")
	while True:
		print("lcd_thread running")
		#print('lcd_thread M1_rotations = ',M1_rotations)
		#report_M1_rotations(M1_rotations)
		time.sleep(10)
	return

def M1_thread():		#string positioner
	global M1_speed,M2_speed,M1_rotations,M2_rotations,M1_direction,M2_direction,M1_state,M2_state
	print("M1_thread starting")
	while True:
		#print("test_thread running")
		#time.sleep(1)
		#print('M1_thread:loop M1_direction = ',M1_direction)
		#if M1_direction != STOP:
			#print('Turning on M1 in direction: ',M1_direction)
			##time.sleep(3)
			#for i in range (200):
				#kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)			
				#kit2.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)			
			#M1_direction = STOP
			#turnOffMotors()
			#print('M1_tread turning off M1_direction to STOP',M1_direction)
		if M1_state == WINDING:
			print('M1_rotations = ',M1_rotations)
			M1_rotations = M1_rotations + (M1_STEPS / 100)
			time.sleep(M1_SLEEP_TIME)
			for i in range (M1_STEPS):
				if (M1_rotations < 10):
					kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)			
				else:
					kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)			
				if (M1_rotations > 20):
					M1_rotations = 0
		if M1_state == SHUTDOWN:
			turnOffMotors()
			
	#return

def M2_thread():		#bobbin spinner
	global M1_speed,M2_speed,M1_rotations,M2_rotations,M1_state,M2_state
	print("M2_thread starting")
	while True:
		#print("test_thread running")
		if M2_state == WINDING:
			M2_rotations = M2_rotations + 1
			for i in range (200):	#1 turn of the motor ?3 turns of string
				kit2.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)			
			if M2_rotations > FULL_BOBIN:	#stop both motors
				M2_state = SHUTDOWN
				M1_state = SHUTDOWN
		if M2_state == SHUTDOWN:
			turnOffMotors()
	#return


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
	
	
@app.route("/", methods=['POST', 'GET'])
def submit(): 
	global M1_rotations,M1_direction,M1_state,M2_state,M1_rotations,M1_direction
	if request.method == "POST":
		if request.form.get("calibrate"):
			print('calibrate')
		elif request.form.get("start_winding"):
			print('start_winding')
			M1_state = WINDING
			M2_state = WINDING
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
			M1_state = SHUTDOWN
			M2_state = SHUTDOWN
			#reset all counters here
			M1_rotations = 0
			M2_rotations = 0
	elif request.method == "GET":
			# do something
			print('request.method')
	return render_template('index.html')


#@app.route("/calibrate")
#def calibrate():
	#calibrate_position()
	#return render_template('index.html')

#def calibrate_position():
	#print("Moving M2")


def flask_thread():
	t4 = app.run(host='0.0.0.0', port=5000, debug=False)
	t4.start()


if __name__ == "__main__":
	#flask_thread()
	#print('starting lcd_thread')
	t1 = threading.Thread(target=lcd_thread)
	t1.start()
	print('starting test_thread')
	t2 = threading.Thread(target=M1_thread)
	t2.start()
	t3 = threading.Thread(target=M2_thread)
	t3.start()
	print('starting thread ',app)
	print("starting web server")
	#t4 = threading.Thread(app.run(host='0.0.0.0', port=5000, debug=False))
	#t4.start()
	#app.run(host='0.0.0.0', port=5000, debug=False , use_reloader=False)
	flask_thread()
	print('main thread')
	while(True):
		print('Main_thread')
		time.sleep(5)
