#!/usr/bin/python3

import time
import datetime
import board
import atexit
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper as stepper
import serial
import pdb
import threading
import RPi.GPIO as GPIO
from flask import Flask, render_template, request, flash
import os
#not for use if lcd display is present
#import curses

kit2 = MotorKit(address=0x61)
kit = MotorKit(i2c=board.I2C())


#global variables from web page to all other threads
STANDBY = 0
START = 1
RUN = 2
RESET = 3
SHUTDOWN = 4
SPEED = 1	#speed (time) for setting left and right margins
Notification = ""


LEFT = 11
RIGHT = 12
STOP = 10

M1_SLEEP_TIME = 0.5
M1_STEPS = 10
Full_bobbin= 100	#how many turns to fill the bobin....
M1_position = 0

#Motor_states
WINDING = 2
CALIBRATING = 1

M1_rotations = 0
M2_rotations = 0
M1_rotations_left = -1
M1_rotations_right = -1
M1_direction = STOP
M2_direction = STOP
M1_state = STANDBY
M2_state = STANDBY
M1_rotations_settings = 0

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
	#print("lcd_thread starting")
	#stdscr = curses.initscr()
	#stdscr.clear()
	say_once = 1
	while True:
		#print("lcd_thread running")
		#print('lcd_thread M1_rotations = ',M1_rotations)
		#report_M1_rotations(M1_rotations)
		if M1_state != 0:
			#stdscr.clear()
			print('M1_thread:loop M1_state = ',M1_state,'\tM2_state = ',M2_state)
			#print('\r')
			print('M1_rotations = ',M1_rotations)
			#print('\r')
			#print('\r')
			print("M1_rotations = {:.1f}".format(M1_rotations))
			#print('\r')
			print('M2_rotations = ',M2_rotations)
			#print('\r')
			print('')
			#win.refresh()
			say_once = 1
		else:
			if say_once == 1:
				print('motors not running')
				say_once = 0
		time.sleep(1)
	return

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    print('Turning off motors')
    kit.stepper2.release()
    kit2.stepper2.release()
    kit.stepper1.release()
    kit2.stepper1.release()
    #time.sleep(0.5)
    M1_state = STANDBY
    M2_state = STANDBY
    print('Resetting state to STANDBY')

def M1_thread():		#string positioner
	global M1_speed,M2_speed,M1_rotations,M2_rotations,M1_direction,M2_direction,M1_state,M2_state,SPEED,M1_rotations_right,M1_rotations_left
	print("M1_thread starting")
	while True:
		#time.sleep(1)
		if M1_state != 0:
			print('M1_thread:loop M1_state = ',M1_state)
			pass
		if M1_state == LEFT:
			print('LEFT setting....')
			for i in range(200 * SPEED):
				kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)			
			M1_state = SHUTDOWN	#shutdown motors
			M1_position = 0	#reset counter
		if M1_state == RIGHT:
			if M1_rotations_right == -1:
				M1_rotations_right = 0		#reset to zero is -1 as used in marker that it has not been touched
			print('RIGHT setting....M1_state = ',M1_state)
			for i in range(200 * SPEED):
				kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)			
			M1_state = SHUTDOWN
			M1_position = 0
			M1_rotations_right = M1_rotations_right + SPEED
		if M1_state == WINDING:
			#print('M1_state == WINDING M1_rotations = ',M1_rotations)
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
			time.sleep(0.5)
			M1_state = STANDBY
		#time.sleep(0.5)		
	return

def M2_thread():		#bobbin spinner
	global M1_speed,M2_speed,M1_rotations,M2_rotations,M1_state,M2_state
	print("M2_thread starting")
	while True:
		#print("test_thread running")
		if M2_state == WINDING:
			M2_rotations = M2_rotations + 1
			for i in range (200):	#1 turn of the motor ?3 turns of string
				kit2.stepper1.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)			
			if M2_rotations > Full_bobbin:	#stop both motors
				time.sleep(0.5)
				M2_state = SHUTDOWN
				M1_state = SHUTDOWN
		if M2_state == SHUTDOWN:
			turnOffMotors()
			#time.sleep(0.5)
			M2_state = STANDBY
		if M2_state != 0:
			#print('M2_thread M2_rotations = ',M2_rotations)
			pass
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
	
	
@app.route("/", methods=['POST', 'GET'])	#sssss
def submit(): 
	global M1_rotations,M1_direction,M1_state,M2_state,M1_rotations,M2_rotations,M1_direction,M1_rotations_left,M1_rotations_right,Full_bobbin,M1_rotations_settings,SPEED,Notification
	errors = []
	error = 0
	#Notification = ''	#clear string
	templateData = {}	#create an empty array, fill it in if everything is OK
	if request.method == "POST":
		if request.form.get("calibrate"):
			print('calibrate')
		elif request.form.get("start_winding"):
			print('start_winding')
			print('M1_rotations_left = ',M1_rotations_left)
			print('M1_rotations_right = ',M1_rotations_right)
			if (M1_rotations_left == -1) or (M1_rotations_right == -1):
				print('Left and right limits must be set first before winding can begin.')
				#flash('You must set both left and right limits first')
				errors.append(
                			"Left and right limits must be set first before winding can begin."
            			)
				error =1
			else:
				M1_state = WINDING
				M2_state = WINDING
				now = datetime.datetime.now()
				timeString = now.strftime("%Y-%m-%d %H:%M")
				templateData = {
					'title' : 'HELLO!',
					'time': timeString
 				}
		elif request.form.get("bobbin_increase"):
			print('increasinf bobbin count')
			Full_bobbin = Full_bobbin + int(Full_bobbin / 10)
		elif request.form.get("bobbin_decrease"):
			print('decreasing bobbin count')
			Full_bobbin = Full_bobbin - int(Full_bobbin / 10)
		elif request.form.get("1X"):
			SPEED = 1
		elif request.form.get("2X"):
			SPEED = 2
		elif request.form.get("5X"):
			SPEED = 5
		elif request.form.get("10X"):
			SPEED = 10
		elif request.form.get("pause"):
			M1_state = SHUTDOWN
			M2_state = SHUTDOWN
		elif request.form.get("reboot"):
			print('request to reboot')
			os.system("sudo reboot")
		elif request.form.get("left set"):
			print('left set')
			M1_rotations = 0
			M1_rotations_left = 0
		elif request.form.get("right set"):
			print('right set')
			M1_rotations_settings = M1_rotations_settings + 1
			if M1_rotations_left == -1:
				print('Left rotation needs to be set first, please set Left side before setting right.')
				errors.append('Left rotation needs to be set first, please set Left side before setting right..')
				error = 1
			else:
				#M1_rotations_right = M1_rotations_settings
				#M1_rotations_right = M1_rotations
				Notification = 'System is ready to start winding, hit start_winding when bobbin is ready.'
		elif request.form.get("shutdown"):
			print('request to shutdown')
			os.system("sudo shutdown -h now")
		elif request.form.get("left"):
			print('request to move left')
			M1_state = LEFT
			print('setting M1_state to ',M1_state)
		elif request.form.get("right"):
			print('request to move right')
			M1_state = RIGHT
			print('setting M1_state to ',M1_state)
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
	print('Errors = ',errors)
	print('error = ',error)
	if error == 1:
		return render_template('index.html',errors=errors)
	else:
		templateData = {
			'M1_rotations_left': M1_rotations_left,
			'M1_rotations_right': M1_rotations_right,
			'M2_rotations': M2_rotations,
			'Full_bobbin' : Full_bobbin,
			'Notification' : Notification
 		}
		return render_template('index.html', **templateData)

#@app.route('/', methods=['POST'])
#def my_form_post():
    #text = request.form['text']
    #processed_text = text.upper()
    #return processed_text

#@app.route("/calibrate")
#def calibrate():
	#calibrate_position()
	#return render_template('index.html')

#def calibrate_position():
	#print("Moving M2")


def flask_thread():
	t4 = app.run(host='0.0.0.0', port=5000, debug=False)
	#t4 = app.run(host='0.0.0.0', port=80, debug=False)
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
