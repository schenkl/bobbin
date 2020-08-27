#!/usr/bin/python3

import time
import board
import atexit
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper as stepper
import serial

Port = '/dev/ttyAMA0'

#ser=serial.Serial(’/dev/ttyACM0’,9600)
#readedText = ser.readline()
#print(readedText)
#ser.close()

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


Serial_comm -1
def connect():
	try:
		Ser = serial.Serial(Port)
		Serial_comm = 1
	except:
		print("Unable to connect to port: ",Port)
		Serial_comm = -1
	return

def lcd_on():
	global Serial_comm
	if (Serial_comm == 1)
		Ser.write('\xfe\x01')

def lcd_off():
	global Serial_comm
	if (Serial_comm == 1)
		Ser.write('\xfe\x08')

def lcd_init():		#screen on, cursor at 1,1 cursor off
	global Serial_comm
	if (Serial_comm == 1)
		Ser.write('\xfe\x42')
		Ser.write('\xfe\x48')
		Ser.write('\xfe\x54')
		Ser.write('\xfe\x4b')

